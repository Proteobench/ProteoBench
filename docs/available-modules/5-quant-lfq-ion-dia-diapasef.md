# DIA quantification - precursor ion level - diaPASEF (**We are working on the documentation: come back soon.**)


This module compares the sensitivity and quantification accuracy for data acquired with data-independent acquisition (DIA) on a timsTOF (Bruker).
It is similar to the DIA quantification module "precursor ion-level" described [here](#7-quant-lfq-precursor-dia-Astral_2Th).

This module compares the sensitivity and quantification accuracy for data-independent acquisition (DIA) data, namely dia-PASEF, on a timsTOF SCP (Bruker Corporation).
Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

**This module is not designed to compare later-stages post-processing of quantitative data such as missing value replacement, and we advise users to publically upload data without replacement of missing values and without manual filtering.**  

We think that this module is more suited to evaluate the impact of (non exhaustive list):
- search engine identification
- peak picking
- low-level ion signal normalisation

Other modules will be more suited to explore further post-pocessing steps. 

## Data set

A dia-PASEF dataset using the same sample composition (for "A" and "B") as described by [Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6)] was used as a benchmark dataset. The samples are a mixture of commercial peptide digest standards of the following species: Escherichia coli (P/N:186003196, Waters Corporation), Yeast (P/N: V7461, Promega) and Human (P/N: V6951, Promega), with logarithmic fold changes (log2FCs) of 0, −1 and 2 for respectively Human, Yeast and E.coli. 
Please refer to the original publication for the full description of sample preparation ([Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6)). 

Data acquisition parameters were as following: 
The resulting peptides were analysed in triplicate (25ng) by nanoLC-MS/MS using an UltiMate 3000 RS nanoLC system (Thermo Fisher Scientific) coupled to a timsTOF SCP mass spectrometer (Bruker). Peptides were separated on a C18 Aurora column (25cm x 75µm ID, IonOpticks) using a gradient ramping from 2% to 20% of B in 30 min, then to 37% of B in 3min and to 85% of B in 2min (solvent A: 0.1% formic acid in H2O; solvent B: 0.1% FA in acetonitrile), with a flow rate of 150nL/min. MS acquisition was performed in diaPASEF mode on the precursor mass range [400-1000] m/z and ion mobility 1/K0 [0.64-1.37]. The acquisition scheme was composed of 8 consecutive TIMS ramps using an accumulation time of 100ms, with 3 MS/MS acquisition windows of 25 Th for each of them. The resulting cycle time was 0.96 seconds. The collision energy was ramped linearly as a function of the ion mobility from 59 eV at 1/K0=1.6Vs cm−2 to 20 eV at 1/K0=0.6Vs cm−2.

These files are available alongside all the associated metadata27 on the ProteomeXchange28 repository PRIDE29 with the following identifier: PXD062685.



The files are currently not yet uploaded to the ProteomeXchange repository, but we are working on this to make them accessible in the near future.

For now, you can download the raw files via:

- [ttSCP_diaPASEF_Condition_A_Sample_Alpha_01_11494.d](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/ttSCP_diaPASEF_Condition_A_Sample_Alpha_01_11494.d.zip)
- [ttSCP_diaPASEF_Condition_A_Sample_Alpha_02_11500.d](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/ttSCP_diaPASEF_Condition_A_Sample_Alpha_02_11500.d.zip)
- [ttSCP_diaPASEF_Condition_A_Sample_Alpha_03_11506.d](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/ttSCP_diaPASEF_Condition_A_Sample_Alpha_03_11506.d.zip)
- [ttSCP_diaPASEF_Condition_B_Sample_Alpha_01_11496.d](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/ttSCP_diaPASEF_Condition_B_Sample_Alpha_01_11496.d.zip)
- [ttSCP_diaPASEF_Condition_B_Sample_Alpha_02_11502.d](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/ttSCP_diaPASEF_Condition_B_Sample_Alpha_02_11502.d.zip)
- [ttSCP_diaPASEF_Condition_B_Sample_Alpha_03_11508.d](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/ttSCP_diaPASEF_Condition_B_Sample_Alpha_03_11508.d.zip)

Alternatively, you can download them from a private server here: [https://proteobench.cubimed.rub.de/datasets/raw_files/DIA/](https://proteobench.cubimed.rub.de/datasets/raw_files/diaPASEF/))

**It is imperative not to rename the files once downloaded!**

Download the zipped FASTA file here: <a href="https://proteobench.cubimed.rub.de/datasets/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip" download>ProteoBenchFASTA_MixedSpecies_HYE.zip</a>.
The fasta file provided for this module contains the three species
present in the samples **and contaminant proteins**.
([Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145))

## Metric calculation

For each precursor ion (modified sequence + charge), we calculate the sum of signal per raw file. Contaminant sequences flagged with the prefix "Cont_" in the fasta file are removed, as well as the peptide ions that match proteins from several species and the peptide ions that are not quantified in any raw file. When applicable, "0" are replaced by NAs and missing values are ignored.
Then we log2-transform the values, and calculate the mean signal per condition, with the standard deviation and coefficient of variation (CV). For each precursor ion, we calculate the difference between the mean(log2) in A and B, and compare it to its expected value. The difference between measured and expected mean(log2) is called "epsilon".
The total number of unique precursor ions is reported on the vertical axis, and the mean or median absolute epsilon is reported on the horizontal axis. More detailed description of how the data are handled before metrics calculation may be found in the tool-specific paragraphs below. 

## How to use

### Input data for private visualisation of your benchmark run(s)

The module is flexible in terms of what workflow the participants can run. However, to ensure a fair comparison of the different processing tools, we suggest using the parameters listed in Table 1. 

|Parameter|Value|
|---------|-----|
|Maximum number of missed cleavages|1|
|PSM FDR|0.01|
|Spectral Library|Predicted spectral library from FASTA|
|Precursor charge state|1-5|
|Precursor m/z range|400-1000|
|Fragment ion m/z range|100-1700|
|Endopeptidase|Trypsin/P|
|Fixed modifications|Carbamidomethylation (C)|
|Variable modifications|Oxidation (M), Acetyl (Protein N-term)|
|Maximum number of variable modifications|1|
|Minimum peptide length|6 residues|


### Submit your run for public usage

When you have successfully uploaded and visualized a benchmark run, we strongly encourage you to add the result to the online repository. This way, your run will be available to the entire community and can be compared to all other uploaded benchmark runs. By doing so, your workflow outputs, parameters and calculated metrics will be stored and publicly available. 

To submit your run for public usage, you need to upload the parameter file associated to your run in the field `Meta data for searches`. Currently, we accept outputs from DIA-NN, AlphaDIA, FragPipe, MaxDIA and Spectronaut (see bellow for more tool-specific details). Please fill the `Comments for submission` if needed, and confirm that the metadata is correct (corresponds to the benchmark run) before checking the button `I confirm that the metadata is correct`. Then the button 
`I really want to upload it` will appear to trigger the submission.

Table 2 provides an overview of the required input files for public submission. More detailed instructions are provided for each individual tool in the following section.

**Table 2. Overview of input files required for metric caluclation and public submission**
|Tool|Input file|Parameter File|
|---------|-----|-|
|AlphaDIA|precursors.tsv|log.txt|
|DIA-NN|*_report.tsv or *_report.parquet|*report.log.txt|
|FragPipe|*_report.tsv|fragpipe.workflow|
|MaxDIA|evidence.txt|mqpar.xml|
|Spectronaut|*.tsv|*.txt|
|PEAKS|lfq.dia.features.csv|parameters.txt|


After upload, you will get a link to a Github pull request associated with your data. Please copy it and save it. With this link, you can get the unique identifier of your run (for example `Proline__20240106_141919`), and follow the advancement of your submission and add comments to communicate with the ProteoBench maintainers. If everything looks good, your submission will be reviewed and accepted (it will take a few working days). Then, your benchmark run will be added to the public runs of this module and plotted alongside all other benchmark runs in the figure. 

## Important Tool-specific settings

### [DIA-NN](https://github.com/vdemichev/DiaNN)
1. Import .d files
2. Add FASTA but do not select "Contaminants" since these are already included in the FASTA file
3. Turn on FASTA digest for library-free search / library generation (automatically activates deep-learning based spectra, RTs, and IMs prediction).
4. Do not set verbosity/Log Level higher than 1, otherwise parameter parsing will not work correctly.
5. The input files for Proteobench are "*_report.tsv*" or "*_report.parquet*" (main report for the precursor quantities) and "*report.log.txt*" (parameter files).

### [AlphaDIA](https://github.com/MannLabs/alphadia)
1. Select FASTA and import .raw files in "Input files"
2. In "Method settings" you need to define your search parameters 
3. Turn on "Predict Library" 
4. Turn on "Precursor Level LFQ"
4. Because ProteoBench requires information from both "precursors.tsv" and "precursor.matrix.tsv", it needs to be preprocessed. For this, please refer to the Jupyter Notebook "ProteoBench_input_conversion.ipynb" [HERE](https://github.com/Proteobench/ProteoBench/blob/main/jupyter_notebooks/ProteoBench_input_conversion.ipynb). Using this notebook will provide you with the correct input file that can be used in ProteoBench. The parameter file is "log.txt".

### [FragPipe - DIA-NN](https://github.com/Nesvilab/FragPipe)
1. Load the DIA_SpecLib_Quant workflow
2. Following import of .d files, assign experiments "by File Name" right above the list of raw files.
3. **Make sure contaminants are not added when you add decoys to the database**. 
4. Upload “*report.tsv” in order for Proteobench to calculate the ion ratios. For public submission, please provide the parameter file “fragpipe.workflow”  that correspond to your search.

In FragPipe output files, the protein identifiers matching a given ion are in two separate columns: "Proteins" and "Mapped Proteins". So we concatenate these two fields to have the protein groups.

### [Spectronaut](https://biognosys.com/software/spectronaut/?gad_source=1&gclid=CjwKCAjwreW2BhBhEiwAavLwfBvsoFvzw54UAATBCaHN6kn8T0vmcdo1ZLhPUH0t90yM-XGo9_fNOhoCsuUQAvD_BwE)
We accept Spectronaut BGS Factory Reports (normal format): the ".._Report.tsv" file is used for calculating the metrics, and the "..._Report.setup.txt" file for parameter parsing when doing public upload.

In the windowsGUI:

1. Configure the proteobench fasta by importing the fasta provided in this module in the "Databases" tab using uniprot parsing rule
2. In the "Analysis" tab, select "Set up a DirectDIA Analysis from file"
3. Select the folder containting the raw files in order to load them
4. Once loaded, you optionally can change the name of the project ("Condition" by default)
5. In the next tab, click on "Import..." to import the proteobench fasta. Next, check the box corresponding to the proteobench fasta on the left panel, and click on "Next".
6. Choose your settings in the next tab
7. In the next tab, fill "A" and "B" in the "Condition" column:
   "A" for "ttSCP_diaPASEF_Condition_A_Sample_Alpha_01_11494","ttSCP_diaPASEF_Condition_A_Sample_Alpha_02_11500", "ttSCP_diaPASEF_Condition_A_Sample_Alpha_03_11506";
   "B" for "ttSCP_diaPASEF_Condition_B_Sample_Alpha_01_11496","ttSCP_diaPASEF_Condition_B_Sample_Alpha_02_11502","ttSCP_diaPASEF_Condition_B_Sample_Alpha_03_11508" 
9. Do not tick any GO terms or Library exensions in the next tabs
10. Finish the settings on the next tab in order to start the search
11. After the search is finished go to the "Report" tab, select "BGS factory Report" and go for "export Report", name the file"..._Report" and select .tsv format
12. Upload the "..._Report.tsv" for private submission and "...Report.setup.txt" (which is in the same folder as the report.tsv file) for public submission to Proteobench

### [MaxDIA](https://www.maxquant.org/) (work in progress)
By default, MaxDIA uses a contaminants-only fasta file that is located in the software folder (“contaminant.txt”). However, the fasta file provided for this module already contains a set of curated contaminant sequences. Therefore, in the MaxQuant settings (Global parameters > Sequences), **UNTICK the “Include contaminants” box**. Furthermore, please make sure the FASTA parsing is set as `Identifier rule = >([^\t]*)`; `Description rule = >(.*)`). When uploading the raw files, press the "No Fractions" button to set up the experiment names as follows: "A_Sample_Alpha_01", "A_Sample_Alpha_02", "A_Sample_Alpha_03", "B_Sample_Alpha_01", "B_Sample_Alpha_02", "B_Sample_Alpha_03". 

For this module, use the "evidence.txt" output in the "txt" folder of MaxQuant search outputs. For public submission, please upload the "mqpar.xml" file associated with your search.

### [PEAKS](https://www.bioinfor.com//)
When starting a new project and selecting the .d files for analysis, you will need to modify the sample names given by PEAKS. More specifically, 

LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_01, 
LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_02,
LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_03,
LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_01,
LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_02,
LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_03

Make sure to set Enzyme as trypsin, Instrument as timsTOF, Fragment as CID and Acquisition as DIA.
In workflow section use the Quantification option. While we do not propose to use a custom spectral library, one could define one in the "Spectral library" tab. Define the different search parameters in the tab "DB search". 
In the tab "Quantification" use the "Label Free" option, followed by either adding all samples individually or grouping samples according to their respective condition. In the "Report" tab, make sure both Precursor and Peptide FDR are set to 1%. 
Once the workflow has run succesfully, make sure to check the "All Search Parameters" and the "Feature Vector CSV" from the Label Free Quantification Exports in the "Export" tab. 

### Custom format

If you do not use a tool that is compatible with ProteoBench, you can upload a tab-delimited table format containing the following columns:

- Sequence: peptide sequence without the modification(s)
- Proteins: column containing the protein identifiers. These should be separated by ";", and contain the species flag (for example "_YEAST").
- Charge: Charge state of measured peptide ions
- Modified sequence: column containing the sequences and the localised modifications in the [ProForma standard](https://www.psidev.info/proforma) format. 
- ttSCP_diaPASEF_Condition_A_Sample_Alpha_01_11494: Quantitative column sample 1
- ttSCP_diaPASEF_Condition_A_Sample_Alpha_02_11500: Quantitative column sample 2
- ttSCP_diaPASEF_Condition_A_Sample_Alpha_03_11506: Quantitative column sample 3
- ttSCP_diaPASEF_Condition_B_Sample_Alpha_01_11496: Quantitative column sample 4
- ttSCP_diaPASEF_Condition_B_Sample_Alpha_02_11502: Quantitative column sample 5
- ttSCP_diaPASEF_Condition_B_Sample_Alpha_03_11508: Quantitative column sample 6

the table must not contain non-validated ions. If you have any issue, contact us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).

## toml file description (work in progress)

Each software tool produces specific output files formats. We made ``.toml`` files that describe where to find the information needed in each type of input. These can be found in `proteobench/modules/dia_quant/io_parse_settings`:

- **[mapper]**
mapping between the headers in the input file (left-hand side) and the header of the intermediate file generated by ProteoBench. If more parsing is required before metrics calculation, this part can contain mapping between intermediatec column names and the name in the intermediate file. This is the case for Proline where protein accessions are reported in two independent columns that need to be combined. This should be commented in the toml.

  - "Raw file" = field that contains the raw file identifiers. **If the field "Raw file" is present, the table is parsed is a long format, otherwise it is parsed as wide format.**
 
  - "Reverse" = field that indicates if the precursor is identified as decoy/reverse. **If the field "Reverse" is present, we will filter out the values of this column equal to the decoy flag (see [general]).**

  - "Sequence" = peptide sequence without modification(s)
 
  - "Modified sequence" = peptide sequence with localised modifications, ideally in the ProForma format.
 
  - "Charge" = precursor charge.
 
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

- **[modifications_parser]**
information necessary for parsing the modification and their localisation when the input table contains a columns with modified sequences. When the input contains a column with stripped sequences and a column with the localised modification, this part is not needed. 

  - "parse_column" = "Modified Sequence" / Indicates the name of the column that should be parsed (i.e. that contains the sequence and localised modifications).

  - "before_aa" = false / Indicates if the modification flag is before or after the modification. For example, this has to be set to false when the cysteine is carbamidomethylated on the third position here: NEC[+57.0214]VVVIR. However, when the modification tag is before the amino acid it needs to be set to true, for example for the same peptidoforms: NE[+57.0214]CVVVIR.

  - "isalpha" = true / In the code the sequence is stripped to insert modifications later. This flag indicates that the modification can be separated by taking only characters that are alpha. For example, “NE[+57.0214]CVVVIR”, "[+57.0214]" is removed.

  - "isupper" = true / In the code the sequence is stripped to insert modifications later. This flag indicates that the modification can be separated by taking only characters that are capitalized. For example, “NEYpCVVVIR”, "p" is removed.

  - "pattern" = "\\[([^]]+)\\]" \ This regex pattern indicates the values to be matched for modifications. Make sure to include the full tag (only the peptide sequence should remain): "NEC[+57.0214]VVM[+15.9949]VIR". You can test your python regexes here: https://regex101.com/

  - "modification_dict" = {"+57.0215" = "Carbamidomethyl", "+15.9949" = "Oxidation", "-17.026548" = "Gln->pyro-Glu", "-18.010565" = "Glu->pyro-Glu", "+42" = "Acetyl"} / Pattern that is matched to be translated into the [ProForma standard](https://www.psidev.info/proforma): HUPO-PSI/ProForma: HUPO-PSI Standardized peptidoform notation (link to [github](https://github.com/HUPO-PSI/ProForma)). Make sure there are no additional parentheses, only the modification name should be translated to.

## Result Description

After uploading an output file, a table is generated that contains the following columns:

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
  - FDR threshold for PSM, peptide and protein level
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
