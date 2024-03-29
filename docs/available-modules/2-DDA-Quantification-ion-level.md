# DDA quantification - precursor ions

This module compares the sensitivity and quantification accuracy for data acquired with data-dependent acquisition (DDA) on a Q Exactive HF-X Orbitrap (Thermo Fisher).
Users can load their data and inspect the results privately. They can also make their outputs public by providing the sassociated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

**This module is not designed to compare later-stages post-processing of quantitative data such as missing value replacement, and we advise users to publically upload data without replacement of missing values and without manual filtering.**  

We think that this module is more suited to evaluate the impact of (non exhaustive list):
- search engine identification
- peak picking
- match between run
- low-level ion signal normalisation

Other modules will be more suited to explore further post-pocessing steps. 

## Data set

A subset of the Q Exactive HF-X Orbitrap (Thermo Fisher) data dependent acquisition (DDA) data described by [Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6) was used as a benchmark dataset. Here, only the first biological replicate series (named “alpha”) was used, encompassing three technical replicates of two different conditions (referred to as “A” and “B”). The samples are a mixture of commercial peptide digest standards of the following species: Escherichia coli (P/N:186003196, Waters Corporation), Yeast (P/N: V7461, Promega) and Human (P/N: V6951, Promega), with logarithmic fold changes (log2FCs) of 0, −1 and 2 for respectively Human, Yeast and E.coli. 
Please refer to the original publication for the full description of sample preparation and data acquisition parameters ([Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6)). 

## Metric calculation

For each precursor ion (modified sequence + charge), we calculate the sum of signal per raw file and condition. Then, we calculate the average signal per condition ("0" are replaced by NAs and missing values are ignored). The total number of unique precursor ions is reported on the *y*-axis, and the weighted sum of the mean absolute error from the expected ratio is reported on the *x*-axis. Precursors matched to contaminant sequences and/or to multiple species are excluded for error calculation.

## How to use

### Input data for private visualisation of your benchmark run(s)

The module is flexible in terms of what workflow the participants can run. However, to ensure a fair comparison of the different processing tools, we suggest using the parameters listed in Table 1.

|Parameter|Value|
|---------|-----|
|Maximum number of missed cleavages|2|
|PSM FDR|0.01|
|Endopeptidase|Trypsin/P|
|Fixed modifications|Carbamidomethylation (C)|
|Variable modifications|Oxidation (M), Acetyl (Protein N-term)|
|Precursor mass tolerance|10 ppm|
|Fragment mass tolerance|0.02 Da|
|Minimum peptide length|7 residues|

### Submit your run for public usage

When you have successfully uploaded and visualized a benchmark run, we strongly encourage you to add the result to the online repository. This way, your run will be available to the entire community and can be compared to all other uploaded benchmark runs. By doing so, your workflow outputs, parameters and calculated metrics will be stored and publicly available. 

To submit your run for public usage, you need to upload the parameter file associated to your run in the field `Meta data for searches`. Currently, we accept outputs from MaxQuant, FragPipe and Proline (see bellow for more tool-specific details). Please fill the `Comments for submission` if needed, and confirm that the metadata is correct (correspond to the benchmark run) before pressing the button `I really want to upload it`. 

After upload, you will get a link to the pull request associated with your data. Please copy it and save it. With this link, you can get the unique identifier of your run (for example "Proline__20240106_141919"), and follow the advancement of your submission and add comments to communicate with the ProteoBench maintainers. If everything looks good, your submission will be reviewed and accepted (it will take a few working days). Then, your benchmark run will be added to the public runs of this module and plotted alongside all other benchmark runs in the figure. 

## Important Tool-specific settings

### AlphaPept
1. Load folder that contains the data files.
2. Define parameters 
-> For Match Between runs, please select “Match”
3. The input files for ProteoBench are "result_peptides.tsv" (peptide identification) and "results.yaml" (parameter files)

### FragPipe
1. Select the LFQ-MBR workflow (using only 1 enzyme).
2. Following import of raw files, assign experiments "by File Name" right above the list of raw files.
3. **Make sure contaminants are not added when you add decoys to the database**. 
4. Upload "combined_ion/modified_peptides.tsv" in order for Proteobench to calculate the ion ratios. Parameter files are not yet implemented in ProteoBench, but we are working on it.
For public submission, please provide the ".params" and the ".worflow" files that correspond to your search. 

### i2MassChroQ
-- available soon --

### MaxQuant
By default, MaxQuant uses a contaminants-only fasta file that is located in the software folder (“contaminant.txt”). However, the fasta file provided for this module already contains a set of curated contaminant sequences. Therefore, in the MaxQuant settings (Global parameters > Sequences), **UNTICK the “Include contaminants” box**
For this module, use the "evidence.txt" output in the "txt" folder of MaxQuant search outputs. For public submission, please upload the "mqpar.xml" file associated with your search.
#### Troubleshooting: Fasta header parsing
The field "Proteins" in **the "evidence.txt" table should report proteins in the format "sp|O75822|EIF3J_HUMAN" (and separated with ";" in the case of protein groups)**. 
In the recent versions of MaxQuant, the default settings work perfectly (`Identifier rule = >([^\s]*)`; `Description rule = >(.*)`).
Some older versions of MaxQuant do not provide the option to change fasta header parsing. These are not compatible with ProteoBench.

### Proline
Use the raw file names as sample names. In the output, it will automatically remove "LFQ_Orbitrap_".
For this module, use the excel exports. Make sure that the “Quantified peptide ions” tab contains the columns "samesets_accessions" and "subsets_accessions". The accessions in these two field are combined to determine what species a peptide sequence matches to.
The "Quantified peptide ions" tab reports validated PSMs, so precursor ion quantities (retrieved from XICs) are duplicated. This redundancy is removed before metric calculation.
For public submission, you can upload the same excel export, just make sure to have the tabs "Search settings and infos", "Import and filters", "Quant config".

### Sage

1. Convert .raw files into .mzML using MSConvert or ThermoRawFileParser **(do not change the file names)**
2. Run sage using a .json file
3. Upload "lfq.tsv" in order for Proteobench to calculate the ion ratios, combined with the search parameter file "results.json".

### Custom format

If you do not use a tool that is compatible with ProteoBench, you can upload a tab-delimited table format containing the following columns:

- Sequence: peptide sequence without the modification(s)
- Proteins: column containing the protein identifiers. These should be separated by ";", and contain the species flag (for example "_YEAST").
- Charge: Charge state of measured peptide ions
- Modified sequence: column containing the sequences and the localised modifications in the [ProForma standard](https://www.psidev.info/proforma) format. 
- LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01: Quantitative column sample 1
- LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02: Quantitative column sample 2
- LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03: Quantitative column sample 3
- LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01: Quantitative column sample 4
- LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02: Quantitative column sample 5
- LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03: Quantitative column sample 6

the table must not contain non-validated ions. If you have any issue, contact us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).

## toml file description

Each software tool produces specific output files formats. We made ``.toml`` files that describe where to find the information needed in each type of input. These can be found in `proteobench/modules/dda_quant/io_parse_settings`:

- **[mapper]**
mapping between the headers in the input file (left-hand side) and the header of the intermediate file generated by ProteoBench. If more parsing is required before metrics calculation, this part can contain mapping between intermediatec column names and the name in the intermediate file. This is the case for Proline where protein accessions are reported in two independent columns that need to be combined. This should be commented in the toml.

  - "Raw file" = field that contains the raw file identifiers. **If the field "Raw file" is present, the table is parsed is a long format, otherwise it is parsed as wide format.**
 
  - "Reverse" = field that indicates if the precursor is identified as decoy/reverse. **If the field "Reverse" is present, we will filter out the values of this column equal to the decoy flag (see [general]).**

  - "Sequence" = peptide sequence without modification(s)
 
  - "Modified sequence" = peptide sequence with localised modifications, ideally in the ProForma format.
 
  - "Charge" = precursor charge.
 
  - "Proteins" = field containing the protein identifiers. These should be separated by ";", and contain the species flag (for example "_YEAST").
 
  - "Intensity" = field containing the intensities utilised to calculate the module metrics. Used for long-format input.

- **[condition_mapper]**
mapping between the headers of the quantification values in the input file (left-hand side) and the condition (Condition A and Condition B). 

- **[run_mapper]**
mapping between the headers of the quantification values in the input file (left-hand side) and the samples (condition + replicate) in the intermediate file.

- **[species_mapper]**
suffix corresponding to the species in the input table (left-hand side), and corresponding species (right-hand side) for ratio calculation. 

- **[general]**
contaminant and decoy flags used for filtering out precursor ions matched to decoy or contaminant sequences. The contaminant flag in this module should be "Cont_" to correspond to the contaminants as labelled in the provided fasta file. The decoy flag is only used to filter out rows that do not pass the validation step but are reported in the table.

- **[modifications_parser]**
information necessary for parsing the modification and their localisation when the input table contains a columns with modified sequences. When the input contains a column with stripped sequences and a column with the localised modification, this part is not needed. 

  - "parse_column" = "Modified Sequence" / Indicates the name of the column that should be parsed (i.e. that contains the sequence and localised modifications).

  - "before_aa" = false / Indicates if the modification flag is before or after the modification. For example, this has to be set to false when the cysteine is carbamidomethylated on the third position here: NEC[+57.0214]VVVIR. However, when the modification tag is before the amino acid it needs to be set to true, for example for the same peptidoforms: NE[+57.0214]CVVVIR.

  - "isalpha" = true / In the code the sequence is stripped to insert modifications later. This flag indicates that the modification can be separated by taking only characters that are alpha. For example, “NE[+57.0214]CVVVIR”, "[+57.0214]" is removed.

  - "isupper" = true / In the code the sequence is stripped to insert modifications later. This flag indicates that the modification can be separated by taking only characters that are capitalized. For example, “NEYpCVVVIR”, "p" is removed.

  - "pattern" = "\\[([^]]+)\\]" \ This regex pattern indicates the values to be matched for modifications. Make sure to include the full tag (only the peptide sequence should remain): "NEC[+57.0214]VVM[+15.9949]VIR". You can test your python regexes here: https://regex101.com/

  - "modification_dict" = {"+57.0215" = "Carbamidomethyl", "+15.9949" = "Oxidation", "-17.026548" = "Gln->pyro-Glu", "-18.010565" = "Glu->pyro-Glu", "+42" = "Acetyl"} / Pattern that is matched to be translated into the [ProForma standard](https://www.psidev.info/proforma): HUPO-PSI/ProForma: HUPO-PSI Standardized peptidoform notation (link to [github](https://github.com/HUPO-PSI/ProForma)). Make sure there are no additional parentheses, only the modification name should be translated to.


