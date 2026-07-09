# DIA quantification - precursor ion level - Low input

> **Using ProteoBench for the first time?** Check out our [Quick Start guide](../../general-information/1-quickstart.md) to help you get started!

This module compares the sensitivity and quantification accuracy of workflows for data acquired with data-independent acquisition (DIA) on an Astral with low sample input.
Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

For bulk sample analyses, see [the DIA Astral module](#8-quant-lfq-ion-dia-Astral_2Th).

**This module is not designed to compare later-stages post-processing of quantitative data such as missing value replacement, and we advise users to publically upload data without replacement of missing values and without manual filtering.**  

## Data set
A subset of the Astral (Thermo Fisher) data independent acquisition (DIA) data described by [Bubis et al., 2024](https://www.biorxiv.org/content/10.1101/2024.02.01.578358v2.abstract) was used as a benchmark dataset. Here, only the series containing 240:10 (condition 'A') and 200:50 (condition 'B') ratios were used, encompassing three replicates each.
The samples are a mixture of commercial peptide digest standards of the following species: HeLa (H) (Thermo Scientific, Pierce™ HeLa Protein Digest Standard, 88328) and yeast (Y) (Promega, MS Compatible Yeast Protein Extract, Digest, Saccharomyces cerevisiae, 100ug, V7461), combined in 0.1% TFA.
Please refer to the original publication for the full description of sample preparation and data acquisition parameters ([Bubis et al., 2024](https://www.biorxiv.org/content/10.1101/2024.02.01.578358v2.abstract)). 

The files can be downloaded from the [ProteoBench server](https://proteobench.cubimed.rub.de/raws/DIA-SingleCell/):

- Single archive with FASTA: [all_data_LFQ_Quant_DIA_SC.tar.gz](https://proteobench.cubimed.rub.de/raws/DIA-SingleCell/all_data_LFQ_Quant_DIA_SC.tar.gz).

Alternatively, you can download them from the proteomeXchange repository [PXD049412](https://www.ebi.ac.uk/pride/archive/projects/PXD049412):

- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r2.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r2.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r3.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r3.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r1.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r1.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r2.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r2.raw)
- [	20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r3.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2025/01/PXD049412/20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_200pg_50pg_H_Y_r3.raw)

**It is imperative not to rename the files once downloaded!**

Download the zipped FASTA file here: [ProteoBenchFASTA_MixedSpecies_HY.zip](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HY.zip).
The fasta file provided for this module contains the two species
present in the samples **and contaminant proteins**
([Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145)).

For search specific instructions, metric definitions, troubleshooting, and result descriptions, see [the DIA Astral bulk module](#8-quant-lfq-ion-dia-Astral_2Th).

## Important Tool-specific settings

Table 2 provides an overview of the required input files for public submission. More detailed instructions are provided for each individual tool in the following section.

**Table 2. Overview of input files required for metric calculation and public submission**
| Tool | Input file | Parameter File |
|---|---|---|
| AlphaDIA | precursors.parquet/.tsv (v2+) or precursor.matrix.tsv + precursors.tsv (v1) | log_alphadia.txt |
| Custom | custom_input.tsv |  |
| DIA-NN | report.tsv or report.parquet | report.log.txt |
| FragPipe | combined_ion.tsv | fragpipe.workflow |
| FragPipe (DIA-NN quant) | report.tsv or report.parquet | fragpipe.workflow |
| MSAID | MSAID_output.tsv | MSAID_params.csv |
| MaxQuant | evidence.txt | mqpar.xml |
| PEAKS | lfq.features.csv | *.txt |
| Spectronaut | *.tsv | ExperimentSetupOverview.txt |

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
