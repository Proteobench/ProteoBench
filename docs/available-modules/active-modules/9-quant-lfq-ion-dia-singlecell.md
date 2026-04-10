# DIA quantification - precursor ion level - Single Cell

This module compares the sensitivity and quantification accuracy of workflows for data acquired with data-independent acquisition (DIA) on an Astral with low sample input.
Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

For bulk sample analyses, see [the DIA Astral module](#8-quant-lfq-ion-dia-Astral_2Th).

**This module is not designed to compare later-stages post-processing of quantitative data such as missing value replacement, and we advise users to publically upload data without replacement of missing values and without manual filtering.**  

## Data set
A subset of the Astral (Thermo Fisher) data independent acquisition (DIA) data described by [Bubis et al., 2024](https://www.biorxiv.org/content/10.1101/2024.02.01.578358v2.abstract) was used as a benchmark dataset. Here, only the series containing 240:10 (condition 'A') and 200:50 (condition 'B') ratios were used, encompassing three replicates each.
The samples are a mixture of commercial peptide digest standards of the following species: HeLa (H) (Thermo Scientific, Pierce™ HeLa Protein Digest Standard, 88328) and yeast (Y) (Promega, MS Compatible Yeast Protein Extract, Digest, Saccharomyces cerevisiae, 100ug, V7461), combined in 0.1% TFA.
Please refer to the original publication for the full description of sample preparation and data acquisition parameters ([Bubis et al., 2024](https://www.biorxiv.org/content/10.1101/2024.02.01.578358v2.abstract)). 

The files can be downloaded from the proteomeXchange repository [PXD049412](https://www.ebi.ac.uk/pride/archive/projects/PXD049412), make sure that you download the following raw files:

- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r2.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r2.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r3.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r3.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r1.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r1.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r2.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r2.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r3.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r3.raw)

Alternatively, you can download them from the ProteoBench server [here](https://proteobench.cubimed.rub.de/raws/DIA-SingleCell/).


**It is imperative not to rename the files once downloaded!**

Download the zipped FASTA file here: [ProteoBenchFASTA_MixedSpecies_HY.zip](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HY.zip).
The fasta file provided for this module contains the two species
present in the samples **and contaminant proteins**
([Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145)).

## Metric calculation

The metric calculation follows the same approach as the [DIA Astral bulk module](7-quant-lfq-ion-dia-Astral_2Th.md):

For each precursor ion (modified sequence + charge), we calculate the sum of signal per raw file. Contaminant sequences flagged with the prefix "Cont_" in the fasta file are removed, as well as the peptide ions that match proteins from several species and the peptide ions that are not quantified in any raw file. When applicable, "0" are replaced by NAs and missing values are ignored.
Then we log2-transform the values, and calculate the mean signal per condition, with the standard deviation and coefficient of variation (CV). For each precursor ion, we calculate the difference between the mean(log2) in A and B, and compare it to its expected value. The difference between measured and expected mean(log2) is called "epsilon".
The total number of unique precursor ions is reported on the vertical axis, and the mean or median absolute epsilon is reported on the horizontal axis.

## How to use

### Input data for private visualization of your benchmark run(s)

The module is flexible in terms of what workflow the participants can run. However, to ensure a fair comparison of the different processing tools, we suggest using the parameters listed below.

| Parameter                                | Value                                  |
| ---------------------------------------- | -------------------------------------- |
| Maximum number of missed cleavages       | 1                                      |
| PSM/Precursor FDR                        | 0.01                                   |
| Spectral Library                         | Predicted spectral library from FASTA  |
| Endopeptidase                            | Trypsin/P                              |
| Fixed modifications                      | Carbamidomethylation (C)               |
| Variable modifications                   | Oxidation (M), Acetyl (Protein N-term) |
| Minimum peptide length                   | 6 residues                             |

### Submit your run for public usage

When you have successfully uploaded and visualized a benchmark run, we strongly encourage you to add the result to the online repository. This way, your run will be available to the entire community and can be compared to all other uploaded benchmark runs.

To submit your run for public usage, you need to upload the parameter file associated to your run in the field `Meta data for searches`. Please fill the `Comments for submission` if needed, and confirm that the metadata is correct before checking the button `I confirm that the metadata is correct`. Then the button `I really want to upload it` will appear to trigger the submission.

### Important tool-specific settings

For detailed tool-specific instructions (DIA-NN, AlphaDIA, FragPipe, Spectronaut, PEAKS), see [the DIA Astral bulk module](7-quant-lfq-ion-dia-Astral_2Th.md). The same tools and input file formats apply to this module; only the raw files and FASTA differ.

**Table: Overview of input files required for metric calculation and public submission**

| Tool | Input file | Parameter File |
|---|---|---|
| AlphaDIA | `precursors.tsv` | `log.txt` |
| DIA-NN | `*_report.tsv` or `*_report.parquet` | `*_report.log.txt` |
| FragPipe | `*_report.tsv` | `fragpipe.workflow` |
| Spectronaut | `*_Report.tsv` | `*_ExperimentSetupOverview*.txt` |
| PEAKS | PEAKS output `.txt` | Settings `.txt` |
| Custom | Tab-delimited table | Not required |

### Custom format

If you do not use a tool that is compatible with ProteoBench, you can upload a tab-delimited table format containing the following columns:

- Sequence: peptide sequence without the modification(s)
- Proteins: column containing the protein identifiers. These should be separated by ";", and contain the species flag (for example "_YEAST").
- Charge: Charge state of measured peptide ions
- Modified sequence: column containing the sequences and the localised modifications in the [ProForma standard](https://www.psidev.info/proforma) format. 
20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1: Quantitative column sample 1
20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r2: Quantitative column sample 2
20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r3: Quantitative column sample 3
20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r1: Quantitative column sample 4
20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r2: Quantitative column sample 5 
20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r3: Quantitative column sample 6

The table must not contain non-validated ions. If you have any issue, contact us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).

---

> **DOCUMENTATION GAPS** (compared to other DIA modules like Module 5, Module 7, Module 10)
>
> - **Table of supported tools**: No overview table of input files and parameter files per tool.
> - **TOML file description**: Not present; other modules include this section.
> - **Result description**: Not present; other modules describe result DataFrame columns.
> - **Public submission instructions**: Missing dedicated section on how to submit for public usage.
