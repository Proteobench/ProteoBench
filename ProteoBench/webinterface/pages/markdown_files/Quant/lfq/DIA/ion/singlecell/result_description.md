It contains the following columns:

- **precursor ion**: concatenation of the modified sequence and charge
- **log_Intensity_mean_{condition}**: mean log2-transformed intensities for condition A and B
- **log_Intensity_std_{condition}**: standard deviations calculated for the log2-transformed values in condition A and B
- **Intensity_mean_{condition}**: mean intensity for condition A and B
- **Intensity_std_{condition}**: standard deviations calculated for the intensity values in condition A and B
- **CV_{condition}**: coefficient of variation (CV) for condition A and B
- **log2_A_vs_B**: differences of the mean log2-transformed values between condition A and B
- **20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_{}pg\_{}pg\_H_Y_r{}**: MS signal from the input table
- **nr_observed**: number of runs with non-missing values
- **YEAST/HUMAN**: species the sequence matches to
- **unique**: TRUE if the sequence is species-specific
- **species**: species the sequence matches to
- **log2_expectedRatio**: expected ratio for the given species
- **epsilon**: difference of the observed and expected log2-transformed fold change
