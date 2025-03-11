It contains the following columns:

- **precursor ion**: concatenation of the modified sequence and charge
- **log_Intensity_mean_{condition}**: mean log2-transformed intensities for condition A and B
- **log_Intensity_std_{condition}**: standard deviations calculated for the log2-transformed values in condition A and B
- **Intensity_mean_{condition}**: mean intensity for condition A and B
- **Intensity_std_{condition}**: standard deviations calculated for the intensity values in condition A and B
- **CV_{condition}**: coefficient of variation (CV) for condition A and B
- **log2_A_vs_B**: differences of the mean log2-transformed values between condition A and B
- **LFQ_Orbitrap_AIF_Condition_{}\_Sample\_Alpha\_{}**: MS signal from the input table
- **nr_observed**: number of runs with non-missing values
- **YEAST/ECOLI/HUMAN**: species the sequence matches to
- **unique**: TRUE if the sequence is species-specific
- **species**: species the sequence matches to
- **log2_expectedRatio**: expected ratio for the given species
- **epsilon**: difference of the observed and expected log2-transformed fold change
