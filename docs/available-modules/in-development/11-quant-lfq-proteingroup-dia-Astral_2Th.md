# DIA quantification - protein-group level - Astral 2Th

This module compares the sensitivity and quantification accuracy for data-independent acquisition (DIA) data, namely Narrow-window 2 Th, on an Orbitrap Astral (Thermo Fisher Scientific).
Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

**This module is not designed to compare later-stages post-processing of quantitative data such as missing value replacement, and we advise users to publically upload data without replacement of missing values and without manual filtering.**  

We think that this module is more suited to evaluate the impact of (non exhaustive list):
- search engine identification
- peak picking
- low-level ion signal normalisation
- protein inference
- protein summarization

Other modules will be more suited to explore further post-pocessing steps. 

## Data set

A not yet released Astral (Thermo Fisher) data independent acquisition (DIA) dataset using the same sample composition (for "A" and "B") as described by [Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6) was used as a benchmark dataset. The samples are a mixture of commercial peptide digest standards of the following species: Escherichia coli (P/N:186003196, Waters Corporation), Yeast (P/N: V7461, Promega) and Human (P/N: V6951, Promega), with logarithmic fold changes (log2FCs) of 0, −1 and 2 for respectively Human, Yeast and E.coli.
Please refer to the original publication for the full description of sample preparation ([Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6)). 

Data acquisition parameters were as following: 
Peptides were loaded directly onto the analytical column and were separated by reversed-phase chromatography using a 50 cm μPAC™ column (Thermo Scientific, cat # COL-NANO050NEOB), featuring a structured pillar array bed with a 180 µm bed width. The chromatographic gradient was initiated with 96% buffer A and 4% buffer B at a flow rate of 750 nL/min durig 1 minute. The flow rate was then reduced to 250 nL/min, and the percentage of buffer B was further increased to 40% over 15 minutes. Buffer A: 0.1% formic acid in water. Buffer B: 0.1% formic acid in 80% acetonitrile.

The mass spectrometer was operated in positive ionization mode with data-independent acquisition, with a full MS scans over a mass range of m/z 380-980 with detection in the Orbitrap at a resolution of 240,000. In each cycle of data-independent acquisition, 300 windows of 2 Th were used to isolate and fragment all precursor ions from 380 to 980 m/z. A normalized collision energy of 25% was used for higher-energy collisional dissociation
(HCD) fragmentation. MS2 scan range was set from 150 to 2000 m/z with detection in the Astral with a maximum injection time of 3 ms.

The files are currently not yet uploaded to the ProteomeXchange repository, but we are working on this to make them accessible in the near future.

For now, you can download the raw files from the ProteoBench server here:

- [LFQ_Astral_DIA_15min_50ng_Condition_A_REP1.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral/LFQ_Astral_DIA_15min_50ng_Condition_A_REP1.raw)
- [LFQ_Astral_DIA_15min_50ng_Condition_A_REP2.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral/LFQ_Astral_DIA_15min_50ng_Condition_A_REP2.raw)
- [LFQ_Astral_DIA_15min_50ng_Condition_A_REP3.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral/LFQ_Astral_DIA_15min_50ng_Condition_A_REP3.raw)
- [LFQ_Astral_DIA_15min_50ng_Condition_B_REP1.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral/LFQ_Astral_DIA_15min_50ng_Condition_B_REP1.raw)
- [LFQ_Astral_DIA_15min_50ng_Condition_B_REP2.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral/LFQ_Astral_DIA_15min_50ng_Condition_B_REP2.raw)
- [LFQ_Astral_DIA_15min_50ng_Condition_B_REP3.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral/LFQ_Astral_DIA_15min_50ng_Condition_B_REP3.raw)

All files can be found here [proteobench.cubimed.rub.de/raws/DIA-astral/](https://proteobench.cubimed.rub.de/raws/DIA-astral/)

**It is imperative not to rename the files once downloaded!**

Download the zipped FASTA file here: [ProteoBenchFASTA_MixedSpecies_HYE.zip](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip).
The fasta file provided for this module contains the three species
present in the samples **and contaminant proteins**.
([Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145))

## Metric calculation

For each protein group, as reported by the software tool (we consider one protein group = one row of the table), we calculate the sum of signal per raw file. Contaminant sequences flagged with the prefix "Cont_" in the fasta file are removed, as well as the protein groups with accessions from several species and the protein groups that are not quantified in any raw file. When applicable, "0" are replaced by NAs and missing values are ignored.
Then we log2-transform the values, and calculate the mean signal per condition, with the standard deviation and coefficient of variation (CV). For each protein group, we calculate the difference between the mean(log2) in A and B, and compare it to its expected value. The difference between measured and expected mean(log2) is called "epsilon".
The total number of protein groups is reported on the vertical axis, and the mean or median absolute epsilon is reported on the horizontal axis. More detailed description of how the data are handled before metrics calculation may be found in the tool-specific paragraphs below. 

## How to use

### Input data for private visualisation of your benchmark run(s)

The module is flexible in terms of what workflow the participants can run. However, to ensure a fair comparison of the different processing tools, we suggest using the parameters listed in Table 1. 

| Parameter                                | Value                                  |
| ---------------------------------------- | -------------------------------------- |
| Maximum number of missed cleavages       | 1                                      |
| PSM/Precursor FDR                        | 0.01                                   |
| Spectral Library                         | Predicted spectral library from FASTA  |
| Precursor charge state                   | 1-5                                    |
| Precursor m/z range                      | 380-980                                |
| Fragment ion m/z range                   | 150-2000                               |
| Endopeptidase                            | Trypsin/P                              |
| Fixed modifications                      | Carbamidomethylation (C)               |
| Variable modifications                   | Oxidation (M), Acetyl (Protein N-term) |
| Maximum number of variable modifications | 1                                      |
| Minimum peptide length                   | 6 residues                             |


### Submit your run for public usage

When you have successfully uploaded and visualized a benchmark run, we strongly encourage you to add the result to the online repository. This way, your run will be available to the entire community and can be compared to all other uploaded benchmark runs. By doing so, your workflow outputs, parameters and calculated metrics will be stored and publicly available. 

To submit your run for public usage, you need to upload the parameter file associated to your run in the field `Meta data for searches`. Currently, we accept outputs from AlphaDIA, DIA-NN and Spectronaut (see bellow for more tool-specific details). Please fill the `Comments for submission` if needed, and confirm that the metadata is correct (corresponds to the benchmark run) before checking the button `I confirm that the metadata is correct`. Then the button 
`I really want to upload it` will appear to trigger the submission.

Table 2 provides an overview of the required input files for public submission. More detailed instructions are provided for each individual tool in the following section.

**Table 2. Overview of input files required for metric caluclation and public submission**
| Tool        | Input file                                                                  | Parameter File    |
| ----------- | --------------------------------------------------------------------------- | ----------------- |
| AlphaDIA    | *_pg.matrix.tsv | log.txt           |
| DIA-NN      | *.pg_matrix.tsv                                            | *report.log.txt   |
| Spectronaut | *.tsv                                                                       | *.txt             |


After upload, you will get a link to a Github pull request associated with your data. Please copy it and save it. With this link, you can get the unique identifier of your run (for example `DIANN_20250505_083341`), and follow the advancement of your submission and add comments to communicate with the ProteoBench maintainers. If everything looks good, your submission will be reviewed and accepted (it will take a few working days). Then, your benchmark run will be added to the public runs of this module and plotted alongside all other benchmark runs in the figure. 

## Important Tool-specific settings

### [DIA-NN](https://github.com/vdemichev/DiaNN)
1. Import Raw files
2. Add FASTA but do not select "Contaminants" since these are already included in the FASTA file
3. Turn on FASTA digest for library-free search / library generation (automatically activates deep-learning based spectra, RTs, and IMs prediction).
4. Do not set verbosity/Log Level higher than 1, otherwise parameter parsing will not work correctly.
5. The input files for Proteobench are "*_report.tsv*" or "*_report.parquet*" (main report for the precursor quantities) and "*report.log.txt*" (parameter files).

### [AlphaDIA](https://github.com/MannLabs/alphadia)
1. Select FASTA and import .raw files in "Input files"
2. In "Method settings" you need to define your search parameters 
3. Turn on "Predict Library" 
4. Turn on "Precursor Level LFQ"
5. The "pg.matrix.tsv" table is used as input to ProteoBench. Make sure that the path to the raw files is not present in the table header. Insted, the columns containing the protein group signal should be in the format "LFQ_Astral_DIA_15min_50ng_Condition_A_REP1", "LFQ_Astral_DIA_15min_50ng_Condition_A_REP2", etc...

Note: >=V1.10.4 is required to obtain the most desired performance (improved check for MS1 cycle)

### [Spectronaut](https://biognosys.com/software/spectronaut/?gad_source=1&gclid=CjwKCAjwreW2BhBhEiwAavLwfBvsoFvzw54UAATBCaHN6kn8T0vmcdo1ZLhPUH0t90yM-XGo9_fNOhoCsuUQAvD_BwE)
1. Configure the proteobench fasta by importing the fasta provided in this module in the "Databases" tab using uniprot parsing rule
2. In the "Analysis" tab, select "Set up a DirectDIA Analysis from folder"
3. Select the folder containting the raw files in order to load the raw files
4. Once loaded, you optionally can change the name of the project
5. In the next tab select the proteobench fasta as the database
6. Choose your settings in the next tab
7. In the next tab fill in the conditions: "LFQ_Astral_DIA_15min_50ng_Condition_A_REP1","LFQ_Astral_DIA_15min_50ng_Condition_A_REP2", "LFQ_Astral_DIA_15min_50ng_Condition_A_REP3","LFQ_Astral_DIA_15min_50ng_Condition_B_REP1","LFQ_Astral_DIA_15min_50ng_Condition_B_REP2","LFQ_Astral_DIA_15min_50ng_Condition_B_REP3"
8. Do not tick any GO terms or Library exensions in the next tabs
9. Finish the settings on the next tab in order to start the search
10. After the search is finished go to the "Report" tab, select "BGS factory Report" and go for "export Report", name the file"..._Report" and select .tsv format
11. Upload the "..._Report.tsv" for private submission and "...Report.setup.txt" (which is in the same folder as the report.tsv file) for public submission to Proteobench

We accept Spectronaut BGS Factory Reports (normal format): the ".._Report.tsv" file is used for calculating the metrics, and the "..._Report.setup.txt" file for parameter parsing when doing public upload.

### Custom format

If you do not use a tool that is compatible with ProteoBench, you can upload a tab-delimited table format containing the following columns:

- Proteins: column containing the protein group identifiers. These should be separated by ";", and contain the species flag (for example "_YEAST").
- LFQ_Astral_DIA_15min_50ng_Condition_A_REP1: Quantitative column sample 1
- LFQ_Astral_DIA_15min_50ng_Condition_A_REP2: Quantitative column sample 2
- LFQ_Astral_DIA_15min_50ng_Condition_A_REP3: Quantitative column sample 3
- LFQ_Astral_DIA_15min_50ng_Condition_B_REP1: Quantitative column sample 4
- LFQ_Astral_DIA_15min_50ng_Condition_B_REP2: Quantitative column sample 5
- LFQ_Astral_DIA_15min_50ng_Condition_B_REP3: Quantitative column sample 6

If you have any issue, contact us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).

## toml file description (work in progress)

Each software tool produces specific output files formats. We made ``.toml`` files that describe where to find the information needed in each type of input. These can be found in `proteobench/modules/dia_quant/io_parse_settings`:

- **[mapper]**
mapping between the headers in the input file (left-hand side) and the header of the intermediate file generated by ProteoBench. If more parsing is required before metrics calculation, this part can contain mapping between intermediatec column names and the name in the intermediate file. This is the case for Proline where protein accessions are reported in two independent columns that need to be combined. This should be commented in the toml.

  - "Raw file" = field that contains the raw file identifiers. **If the field "Raw file" is present, the table is parsed is a long format, otherwise it is parsed as wide format.**
 
  - "Proteins" = field containing the protein identifiers. These should be separated by ";", and contain the species flag (for example "_YEAST"). *Curently, there is an exception for FragPipe's .toml where we combine two columns, and protein IDs are seperated by "," (see the FragPipe section).*
 
  - "Intensity" = field containing the intensities utilised to calculate the module metrics. Used for long-format input.

- **[condition_mapper]**
mapping between the headers of the quantification values in the input file (left-hand side) and the condition (Condition A and Condition B). 

- **[run_mapper]**
mapping between the headers of the quantification values in the input file (left-hand side) and the samples (condition + replicate) in the intermediate file.

- **[species_mapper]**
suffix corresponding to the species in the input table (left-hand side), and corresponding species (right-hand side) for ratio calculation. 

- **[general]**
contaminant and decoy flags used for filtering out precursor ions matched to decoy or contaminant sequences. The contaminant flag in this module should be "Cont_" to correspond to the contaminants as labelled in the provided fasta file. The decoy flag is only used to filter out rows that do not pass the validation step but are reported in the table.

## Result Description

After uploading an output file, a table is generated that contains the following columns:

- Proteins = protein groups as reported in the original data
- mean log2-transformed intensities for condition A and B
- standard deviations calculated for the log2-transformed values in condition A and B
- mean intensity for condition A and B
- standard deviations calculated for the intensity values in condition A and B
- coefficient of variation (CV) for condition A and B
- differences of the mean log2-transformed values between condition A and B
- MS signal from the input table ("abundance_LFQ_Astral_DIA_15min_50ng_Condition_A_REP1" to "abundance_LFQ_Astral_DIA_15min_50ng_Condition_B_REP3")
- Count = number of runs with non-missing values
- species the sequence matches to
- unique = TRUE if the sequence is species-specific
- species
- expected ratio for the given species
- epsilon = difference of the observed and expected log2-transformed fold change

Choose with the slider below the minimum number of quantification value per raw file.
Example: when 3 is selected, only the precursor ions quantified in 3 or more raw files will be considered for the plot.
 
## Define Parameters

To make the results available to the entire community, you need to provide the parameter file that corresponds to 
your analysis. You can upload it in the drag and drop area in the "Add results to online repository" section (under Download calculated ratio's). 
See [here](#important-tool-specific-settings)
for all compatible parameter files.
In this module, we keep track of the following parameters, if you feel 
that some important information is missing, please add it in the 
`Comments for submission` field. 
  - software tool name and version
  - search engine name and version (if different from software tool)
  - FDR threshold for PSM, precursor, peptide and protein level
  - match between run (or not)
  - Precursor and fragment m/z range
  - precursor and fragment mass tolerance
  - enzyme (although for these data it should be Trypsin)
  - maximum number of missed-cleavages
  - minimum and maximum peptide length
  - fixed and variable modifications
  - maximum number of modifications
  - minimum and maximum precursor charge

Once you confirm that the metadata is correct (and corresponds to the 
table you uploaded before generating the plot), a button will appear.
Press it to submit. 

**DISCLAIMER**: When submitting parameter files, please be aware that your dataset may contain identifiable information through embedded file paths. These paths can reveal personal usernames, system architecture, project names, and directory structures associated with e.g.
- The FASTA database location
- The RAW data location
- Installation paths for the tools being used

Such metadata can inadvertently disclose sensitive or institution-specific information.
We recommend reviewing and sanitizing any file paths prior to submission to ensure compliance with your organization's data privacy policies and to protect personal or institutional identifiers.

**If some parameters are not in your parameter file, it is important that 
you provide them in the "comments" section.**

Once submitted, you will see a weblink that will prompt you to a 
pull request on the github repository of the module. Please write down
its number to keep track of your submission. If it looks good, one of 
the reviewers will accept it and make your data public. 

Please contact us if you have any issue. To do so, you can create an 
[issue](https://github.com/Proteobench/ProteoBench/issues/new) on our 
github, or [send us an email](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).
