# DIA quantification - precursor ion level (PYE: Plasma/Yeast/E. coli)

This module compares the sensitivity and quantification accuracy for data-independent acquisition (DIA) data on plasma samples spiked with yeast and E. coli (PYE dataset).
Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

**This module is not designed to compare later-stages post-processing of quantitative data such as missing value replacement, and we advise users to publicly upload data without replacement of missing values and without manual filtering.**

We think that this module is more suited to evaluate the impact of (non exhaustive list):
- search engine identification
- peak picking
- low-level ion signal normalisation
- performance on complex biological matrices (plasma background)

Other modules will be more suited to explore further post-processing steps.

**Release stage: BETA.**

## Data set

The PYE (Plasma/Yeast/E. coli) dataset is based on a comprehensive benchmark study ([Distler et al., Nat. Comms.](https://www.nature.com/articles/s41467-025-64501-z)) evaluating DIA quantification strategies. The dataset uses a three-component mixture to simulate complex biological quantification scenarios:

- **HUMAN** (plasma background) - represents the complex endogenous proteome
- **YEAST** (spike-in) - log2FC ≈ -1.585 (1:3 ratio A/B)
- **ECOLI** (spike-in) - log2FC = 1 (2:1 ratio A/B)

### Expected condition ratios (A/B):
- HUMAN: 1.0 (log2FC = 0)
- YEAST: 1/3 (log2FC ≈ -1.585)
- ECOLI: 2.0 (log2FC = 1)

### Sample composition and preparation

The samples consist of commercial peptide digest standards from three species:
- Escherichia coli (Waters Corporation)
- Saccharomyces cerevisiae (Promega)
- Human plasma (as the complex biological background)

The samples are mixed to achieve the specified fold-change ratios, with condition A containing the base ratio and condition B containing the modified ratios. Each condition is measured in six technical replicates, resulting in a total of 12 raw files (6 replicates × 2 conditions).

### Data acquisition

The dataset was acquired on a timsTOF instrument using data-independent acquisition (DIA) with nano-LC separation. The raw files follow the naming convention:
- Condition A: `A9_G_DIA_nLC_tTOF_R1` ... `A9_G_DIA_nLC_tTOF_R6`
- Condition B: `B9_G_DIA_nLC_tTOF_R1` ... `B9_G_DIA_nLC_tTOF_R6`

Full acquisition details and analytical procedures are available in the [original publication](https://www.nature.com/articles/s41467-025-64501-z).

### Downloading the data

The files can be downloaded from the proteomeXchange repository [JPST003358](https://repository.jpostdb.org/entry/JPST003358):

- [A9_G_DIA_nLC_tTOF_R1.d](https://storage.jpostdb.org/JPST003358/A9_G_DIA_nLC_tTOF_R1.d.zip)
- [A9_G_DIA_nLC_tTOF_R2.d](https://storage.jpostdb.org/JPST003358/A9_G_DIA_nLC_tTOF_R2.d.zip)
- [A9_G_DIA_nLC_tTOF_R3.d](https://storage.jpostdb.org/JPST003358/A9_G_DIA_nLC_tTOF_R3.d.zip)
- [A9_G_DIA_nLC_tTOF_R4.d](https://storage.jpostdb.org/JPST003358/A9_G_DIA_nLC_tTOF_R4.d.zip)
- [A9_G_DIA_nLC_tTOF_R5.d](https://storage.jpostdb.org/JPST003358/A9_G_DIA_nLC_tTOF_R5.d.zip)
- [A9_G_DIA_nLC_tTOF_R6.d](https://storage.jpostdb.org/JPST003358/A9_G_DIA_nLC_tTOF_R6.d.zip)
- [B9_G_DIA_nLC_tTOF_R1.d](https://storage.jpostdb.org/JPST003358/B9_G_DIA_nLC_tTOF_R1.d.zip)
- [B9_G_DIA_nLC_tTOF_R2.d](https://storage.jpostdb.org/JPST003358/B9_G_DIA_nLC_tTOF_R2.d.zip)
- [B9_G_DIA_nLC_tTOF_R3.d](https://storage.jpostdb.org/JPST003358/B9_G_DIA_nLC_tTOF_R3.d.zip)
- [B9_G_DIA_nLC_tTOF_R4.d](https://storage.jpostdb.org/JPST003358/B9_G_DIA_nLC_tTOF_R4.d.zip)
- [B9_G_DIA_nLC_tTOF_R5.d](https://storage.jpostdb.org/JPST003358/B9_G_DIA_nLC_tTOF_R5.d.zip)
- [B9_G_DIA_nLC_tTOF_R6.d](https://storage.jpostdb.org/JPST003358/B9_G_DIA_nLC_tTOF_R6.d.zip)

Alternatively, you can download them from the ProteoBench server here: [proteobench.cubimed.rub.de/raws/DIA-plasma/](https://proteobench.cubimed.rub.de/raws/DIA-plasma/)

**It is imperative not to rename the files once downloaded!**

### FASTA database

Download the zipped FASTA file here: [ProteoBenchFASTA_Distler_PYE.zip](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_Distler_PYE.zip).

The FASTA file provided for this module contains the three species present in the samples (HUMAN, YEAST, ECOLI) **and contaminant proteins**. It is the same FASTA that was used in the original article describing the dataset ([Distler et al., Nat. Comms.](https://www.nature.com/articles/s41467-025-64501-z)).

## Metric calculation

Contaminant sequences flagged with the prefix "Cont_" in the FASTA file are removed, as well as precursor ions that match proteins from multiple species and ions that are not quantified in any raw file. Missing values are handled appropriately per tool specification.

Quantification values are log2-transformed, and the mean signal per condition is calculated with standard deviation and coefficient of variation (CV). For each precursor ion, the difference between the mean(log2) in condition A and condition B is compared to its expected value (epsilon).

### Main plot dimensions:

- **X-axis**: absolute log2 fold-change error for spike-ins (YEAST + ECOLI), displayed as Median or Mean
- **Y-axis**: number of quantified spike-in precursor ions
- **Dot size**: dynamic range of HUMAN plasma precursors (mean of condition-wise log10 90th-10th percentile spread)
- **Dot opacity**: HUMAN plasma quantification accuracy (absolute epsilon; darker coloring = better accuracy)

### Calculation modes:

Two error calculation modes are available:
- **Global**: globally calculated error across all spike-in precursors
- **Species-weighted**: per-species error (YEAST, ECOLI) averaged equally

Both modes are available in **Mean** and **Median** variants.

A cutoff slider allows filtering of precursors by the minimum number of runs in which the precursor is observed.

## How to use

Click [here](https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_Plasma) if you want to submit your results or when you want to explore the plasma quantification module.

### Input data for private visualization

The module supports multiple data formats to maximize flexibility. Users can process the data with their preferred DIA analysis tool, as long as one of the supported formats is generated.

**Currently supported input formats in this module:**
- DIA-NN
- AlphaDIA
- Spectronaut
- PEAKS
- FragPipe (DIA-NN Quant)
- Custom (tab-delimited format)

### Suggested parameters

To ensure fair comparison between different processing workflows, we suggest using the parameters listed below:

| Parameter | Value |
|-----------|-------|
| Maximum number of missed cleavages | 1 |
| PSM/Precursor FDR | 0.01 |
| Spectral Library | Predicted spectral library from FASTA |
| Precursor charge state | 1-5 |
| Fixed modifications | Carbamidomethylation (C) |
| Variable modifications | Oxidation (M), Acetyl (Protein N-term) |
| Minimum peptide length | 6-7 residues |

These parameters represent a standardized configuration to evaluate the intrinsic performance of different analysis tools without the confounding effects of non-standard parameter choices.

### Important Tool-specific settings

Detailed instructions and optimal settings for each supported tool are provided below.

#### [DIA-NN](https://github.com/vdemichev/DiaNN)

1. Use the provided FASTA file to generate a spectral library using DIA-NN's library generation mode
2. Process the raw files using the standard DIA-NN workflow with the recommended DIA settings
3. Export the results as either `*_report.tsv` or `*_report.parquet` format
4. The parameter log file `*_report.log.txt` should be collected for public submissions

#### [AlphaDIA](https://github.com/MannLabs/alphadia)

1. Process your DIA raw files with AlphaDIA following the standard workflow
2. AlphaDIA generates two important output files that must both be uploaded:
   - `precursors.tsv` - contains precursor-level quantification data in long format
   - `precursor.matrix.tsv` - contains the quantification matrix
3. Both files are required for proper parsing
4. If your AlphaDIA version outputs a different format, you may need to preprocess the files using the [ProteoBench_input_conversion.ipynb](https://github.com/Proteobench/ProteoBench/blob/main/jupyter_notebooks/ProteoBench_input_conversion.ipynb) Jupyter Notebook
5. Upload the `log.txt` file for public submissions

#### [Spectronaut](https://biognosys.com/software/spectronaut)

1. Create a spectral library from the provided FASTA using Spectronaut's library generation tools
2. Process your DIA raw files using DirectDIA or standard Spectronaut DIA analysis workflow
3. Export results in the BGS Factory Report format: `*_Report.tsv`
4. Use the Spectronaut setup file `*_Report.setup.txt` for public submission, which contains all analysis parameters
5. Ensure that your export includes precursor-level quantification data with columns for: modified peptide sequence, charge state, protein IDs, and intensity values

#### [FragPipe (DIA-NN Quant)](https://fragpipe.nesvilab.org/)

1. Load the DIA_SpecLib_Quant workflow
2. Import your DIA raw files into FragPipe
3. Assign experimental group information to raw files
4. Generate or use a spectral library from the provided FASTA
5. **Important:** Make sure contaminants are not added when you add decoys to the database
6. Run the analysis and export DIA-NN output `*_report.tsv` file containing precursor-level quantification
7. For public submissions, provide the `fragpipe.workflow` parameter file that corresponds to your search

**Note:** FragPipe output files concatenate protein identifiers from "Proteins" and "Mapped Proteins" columns to create protein groups.

#### [PEAKS](https://www.bioinfor.com/)

1. Create a new PEAKS project and import your DIA raw files
2. Configure sample grouping to match your experimental design (Condition A vs. Condition B)
3. Set up the DIA quantification method with appropriate parameters
4. Use label-free quantification (LFQ) with Identification Directed Quantification (IDQ) mode
5. Export results as a text report (`.txt` format) containing precursor-level quantification data
6. For public submission, upload the settings text file (`.txt`) containing all analysis parameters

#### Custom format

If you do not use a tool that is compatible with ProteoBench, you can upload a tab-delimited table format containing the following columns:

| Column | Description |
|--------|-------------|
| Sequence | Peptide sequence without modifications |
| Modified sequence | Sequence with localised modifications in [ProForma standard](https://www.psidev.info/proforma) format |
| Proteins | Protein identifiers separated by ";"; must contain species flags (e.g., "_HUMAN", "_YEAST", "_ECOLI") |
| Charge | Charge state of the precursor ion |
| A9_G_DIA_nLC_tTOF_R1 ... R6 | Quantitative intensity values for condition A replicates |
| B9_G_DIA_nLC_tTOF_R1 ... R6 | Quantitative intensity values for condition B replicates |

The table should contain only validated ions and must not include contaminant sequences or non-specific peptides.

### Submit your run for public usage

When you have successfully uploaded and visualized a benchmark run, we strongly encourage you to add the result to the online repository. This way, your run will be available to the entire community and can be compared to all other uploaded benchmark runs.

To submit your benchmark run publicly:

1. Upload your quantification output file (in one of the supported formats)
2. Provide the matching parameter/log file(s) from your analysis tool
3. Fill in optional comments describing your workflow, any filtering steps, or notable observations
4. Confirm the metadata information (software name, version, parameters)
5. Submit your benchmark run

Once submitted, a GitHub pull request will be automatically generated for tracking and community review. Your workflow output, parameters, and calculated metrics will be stored and made publicly available.

## Tool-specific input files

| Tool | Quantification input | Metadata / parameter file |
|---|---|---|
| DIA-NN | `*_report.tsv` or `*_report.parquet` | `*_report.log.txt` |
| AlphaDIA | `precursors.tsv` + `precursor.matrix.tsv` (both required; see Jupyter Notebook for preprocessing) | `log.txt` |
| Spectronaut | `*_Report.tsv` (BGS factory report format) | `*_Report.setup.txt` |
| FragPipe (DIA-NN Quant) | `*_report.tsv` | `fragpipe.workflow` |
| PEAKS | PEAKS DIA output file (`.txt` format - export as text report) | Settings text file (`.txt`) |
| Custom | Tab-separated values (`.tsv` or `.csv`) following standard format | Not required |

## Notes

- Contaminants are expected to be flagged with `Cont_`.
- Species annotation in protein identifiers must support `_HUMAN`, `_YEAST`, and `_ECOLI` mapping.
- For this module page, only currently implemented formats and behavior are documented.
