It contains the following columns:

- precursor ion = concatenation of the modified sequence and charge
- mean log2-transformed intensities for condition A and B
- standard deviations calculated for the log2-transformed values in condition A and B
- mean intensity for condition A and B
- standard deviations calculated for the intensity values in condition A and B
- coefficient of variation (CV) for condition A and B
- differences of the mean log2-transformed values between condition A and B
- MS signal from the input table ("abundance_DDA_Condition_A_Sample_Alpha_01" to "abundance_DDA_Condition_B_Sample_Alpha_03")
- Count = number of runs with non-missing values
- species the sequence matches to
- unique = TRUE if the sequence is species-specific
- species
- expected ratio for the given species
- epsilon = difference of the observed and expected log2-transformed fold change
