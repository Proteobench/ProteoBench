library(gplots)
library(ggplot2)
library(tidyr)
library(dplyr)
library(proxy)
library(hexbin)


get_intermediate_data <- function(
        data_path = "./",
        file_name = "result_performance.csv") {
    # This function is used to get the intermediate data from the analysis
    # It is not used for the data points
    # data_path: the path to the data
    # file_name: the name of the file to read
    # Go over files and read all
    hashes <- list.files(path = data_path)
    data <- list()
    full_data <- data.frame()
    for(h in hashes) {
        # Read the file
        file_path <- paste0(data_path, h, "/result_performance.csv")
        message("Reading file: ", file_path)
        if (!file.exists(file_path)) {
            print(paste0("File ", file_path, " does not exist"))
            next
        }
        data[[h]] <- read.csv(file_path)
        full_data <- rbind(full_data, cbind(hash = h, data[[h]]))
    }
    return(full_data)
    
}

select_columns <- function(data, id_col = "precursor.ion", columns, make_one_col = FALSE) {
    # This function is used to filter and select the columns of the data
    # to generate a dedicate wide table of only these column data
    all_ions <- unique(data[, id_col])
    q_names <-  grep(columns, names(data), value = T)
    numc <- length(q_names)
    hashes <- unique(data$hash)
    
    if (make_one_col & numc > 1) {
        print("make_one_col is not implemented yet")
    }
    
    # going to wide matrix
    full_matrix <- matrix(NA, nrow = length(all_ions), ncol = length(hashes)*numc, 
                          dimnames = list(all_ions, paste0(rep(hashes, 
                                                               each = numc), "_",
                                                           rep(q_names, length(hashes)))))
    for(h in hashes) {
        # Populating the matrix
        tdata <- as.matrix(full_data[full_data$hash == h, q_names])
        t_ids <- full_data[full_data$hash == h, id_col]
        
        # Summarize tdata when there are multiple identical t_ids using mean
        # TODO
        if (sum(duplicated(t_ids)) > 0) {
            message("Multiple features of the same name, summarizing features not available yet\n
                    Skippintg this hash: ", h)
            next
        }
        # if(sum(duplicated(t_ids)) > 0) {
        #     message("Summarizing features with identical IDs in ", h, " using mean")
        #     tdata <- aggregate(tdata, by = list(t_ids), FUN = mean)
        #     t_ids <- tdata[, 1]
        #     tdata <- tdata[, -1]
        # }

        full_matrix[full_data[full_data$hash == h, id_col], 
                    ((which(h == hashes)-1)*numc)+1:numc] <- 
            tdata
    }
    
    
    return(full_matrix)
}

hierclust_quant <- function(full_matrix, log=TRUE, labels = NULL, feature_name = "Precursor Ions") {
    # This function is used to cluster the data
    # full_matrix: the matrix to cluster
    # log: if TRUE, log2 transform the data
    # labels: the labels for coloring the columns
    full_matrix[full_matrix == 0] <- NA
    
    if (log) {
        full_matrix <- log2(full_matrix)
    }
    
    # Remove rows with all NA values
    full_matrix <- full_matrix[rowSums(is.na(full_matrix)) != ncol(full_matrix), ]
    
    # Comparing all datapoints
    #red_matrix <- full_matrix[!grepl("-1", rownames(full_matrix)),]
    cors <- cor(log2(full_matrix), use = "pairwise.complete.obs", method = "pearson")
    cors[is.na(cors)] <- 0
    
    RowSideColors <- rep("#000000", ncol(full_matrix))
    if (!is.null(labels)) {
        tcols <- heat.colors(length(labels))
        for (l in labels) {
            RowSideColors[grepl(l, colnames(full_matrix))] <- tcols[which(labels == l)]
        }
    }
    
    heatmap.2(cors, 
              scale = "none", 
              main = "Correlation of Quantitative Values Across Data Points",
              xlab = "Data Points", ylab = feature_name,
              trace = "none",
              RowSideColors = RowSideColors,
              margins = c(5, 5), col = colorRampPalette(c("red", "white", "blue"))(256))
    
}


hierclust_missing <- function(full_matrix, labels = NULL, feature_name = "Precursor Ions") {
    # This function is used to cluster the identifications (on/off)
    # full_matrix: the matrix to cluster
    # labels: the labels for coloring the columns
    full_matrix[full_matrix == 0] <- NA
    
    # Comparing all datapoints
    #red_matrix <- full_matrix[!grepl("-1", rownames(full_matrix)),]
    dist_jaccard <- 1-as.matrix(proxy::dist(t(!is.na(full_matrix)), method = "Jaccard"))
    
    RowSideColors <- rep("#000000", ncol(full_matrix))
    if (!is.null(labels)) {
        tcols <- heat.colors(length(labels))
        for (l in labels) {
            RowSideColors[grepl(l, colnames(full_matrix))] <- tcols[which(labels == l)]
        }
    }
    
    heatmap.2(as.matrix(dist_jaccard), 
              scale = "none", 
              main = "Jaccard distance of Quantitative Values Across Data Points",
              xlab = "Data Points", ylab = feature_name,
              trace = "none",ColSideColors = grey.colors(256)[
                  colSums(!is.na(full_matrix))/nrow(full_matrix) * 256 + 1],
              RowSideColors = RowSideColors,
              margins = c(5, 5), col = colorRampPalette(c("red", "white", "blue"))(256))
    

}

plot_sample_coverage <- function(full_matrix, 
                     feature_name = "Precursor Ions") {
    # Number of precursor ions found in at least n samples with n as x-axis
    counts <- table(rowSums(!is.na(full_matrix)))
    cumcounts <- vector("numeric", length = length(counts))
    for (i in length(counts):1) {
        cumcounts[i] <- sum(counts[i:length(counts)])
    }
    names(cumcounts) <- names(counts)
    plot(as.numeric(names(cumcounts)), cumcounts, xlab="n samples", 
         ylab = paste("Number of", feature_name), 
         main = paste("Number of", feature_name, "found in at least n samples"),
         col = "#333355", pch = 19, cex = 0.5,
         xlim = c(0, ncol(full_matrix)), ylim = c(0, max(cumcounts)))
}

plot_missing_vs_mean <- function(full_matrix, 
                   feature_name = "Precursor Ions") {
    # 2D histogram of mean abundance vs. missingness
    plot(hexbin(rowMeans(log2(full_matrix), na.rm=T), rowSums(!is.na(full_matrix))), 
         xlab = "Mean expression (log2)", ylab = "Number of values across samples",
         main = paste("Missingness vs. Mean abundance of", feature_name))
}

# Get data from files
full_data <- get_intermediate_data(data_path = "../analysis/temp_results/")

## Filter data

#### Testing for stripping to bare sequences
# # Change to stripped sequences removing everything after "|"
# full_data$precursor.ion <- gsub("\\|.*", "", full_data$precursor.ion)
# # Remove all bracketet PTMs in sequences
# full_data$precursor.ion <- gsub("\\[.*?\\]", "", full_data$precursor.ion)
# # Remove all dashes
# full_data$precursor.ion <- gsub("-", "", full_data$precursor.ion)


# Proline has multiples, so we need to remove duplicates
full_data <- full_data[!duplicated(paste(full_data$hash, full_data$precursor.ion)),]
# Remove Sage runs with charge state "-1"
full_data <- full_data[!grepl("-1", full_data$precursor.ion), ]

# Create matrix with reduced data for plotting
full_matrix <- select_columns(full_data, id_col = "precursor.ion", 
                              columns = "log2_A_vs_B")
                                       #columns = "LFQ_Orbitrap_DDA_Condition")

# Hierarchical clustering (heatmap) of the quantitative data
hierclust_quant(full_matrix, log = TRUE, labels = c("LFQ_Orbitrap_DDA_Condition_A","LFQ_Orbitrap_DDA_Condition_B"),
                 feature_name = "Precursor Ions")

# Hierarchical clustering (heatmap) of the quantitative data
hierclust_missing(full_matrix, labels = c("LFQ_Orbitrap_DDA_Condition_A","LFQ_Orbitrap_DDA_Condition_B"),
                feature_name = "Precursor Ions")

plot_sample_coverage(full_matrix)

plot_missing_vs_mean(full_matrix)


TODO: 
    a) stripped sequences
b) make full vectors for each data set
c) pick the most intense ions for redoing the heatmaps
d) UMAP on samples taking only full coverage ions
e) Use log FCs for heatmaps



############### OLD ###########################

# Map species to percursor ions
species_map <- data.frame(precursor.ion = full_data$precursor.ion, species = full_data$species)
# THERE ARE SOME DUPLICATES, EVEN FOR SAME PEPTIDE!
species_map <- species_map[!duplicated(species_map$precursor.ion),]
rownames(species_map) <- species_map$precursor.ion

# General Umap of full data set
library(umap)
red_full <- log2(full_matrix[complete.cases(full_matrix),])
umap_results <- umap(red_full, n_neighbors = 5, min_dist = 0.1, metric = "euclidean")
plot(umap_results$layout, col = rainbow(3, alpha = 0.3)[as.numeric(factor(species_map[rownames(red_full), "species"]))], 
     pch = 19, cex = 1,
     main = "Umap of all complete precursor ions")

# Better with imputing zeroes and on absolute scale?
full_imp <- full_matrix
full_imp[is.na(full_imp)] <- 0
umap_results <- umap(full_imp, n_neighbors = 5, min_dist = 0.1, metric = "euclidean")
plot(umap_results$layout, col = rainbow(3, alpha = 0.3)[as.numeric(factor(species_map[rownames(full_imp), "species"]))], 
     pch = 19, cex = 0.5,
     main = "Umap of all complete precursor ions")

# PCA of samples
pca.out <- princomp(red_full)
plot(pca.out$loadings, pch = rep(rep(c(15, 16), each = 3), length(hashes)) , col = rainbow(length(hashes))[rep(1:length(hashes), each = 6)])

# compare CVs between data sets
cv_matrix <- full_data[, c("precursor.ion", "hash", "CV_A", "CV_B")]


df_long <- cv_matrix %>%
    pivot_longer(cols = c("CV_A", "CV_B"), 
                 names_to = "condition", 
                 values_to = "CV") %>%
    mutate(col_id = paste(hash, condition, sep = "_"))

# install.packages("pheatmap") if not installed
library(pheatmap)

pheatmap(cv_mat, 
         cluster_rows = TRUE, 
         cluster_cols = FALSE, 
         main = "CV values across conditions", 
         color = colorRampPalette(c("blue", "white", "red"))(50),
         fontsize_row = 6)

df_wide <- df_long %>%
    select(precursor.ion, col_id, CV) %>%
    pivot_wider(names_from = col_id, values_from = CV)

# Convert to matrix with precursor.ion as row names
cv_mat <- as.data.frame(df_wide)
rownames(cv_mat) <- cv_mat$precursor.ion
cv_mat <- as.matrix(cv_mat[, -1])

library(pheatmap)

pheatmap(cv_mat,
         cluster_rows = TRUE,
         cluster_cols = TRUE,
         scale = "none",  # or "row" if you want Z-score per ion
         color = colorRampPalette(c("blue", "white", "red"))(50),
         fontsize_row = 6,
         main = "CV Heatmap per Ion and Hash")



