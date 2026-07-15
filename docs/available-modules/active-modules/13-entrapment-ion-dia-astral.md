# DIA Ion Entrapment - Astral

This module uses entrapment peptides to assess whether the false discovery rate (FDR) reported by a DIA search engine is reliable. It is based on the entrapment approach described in [Wen et al., 2025](https://www.nature.com/articles/s41592-025-02719-x).

> **This module is in alpha stage. Results and interfaces may change.**

## Purpose

FDR control is a central assumption in proteomics data analysis. When a search engine reports 1% FDR, the actual proportion of false discoveries should not exceed 1%. This module tests that assumption empirically by spiking a known set of "entrapment" peptides into the search space. These peptides cannot be present in the sample (they are derived from a shuffled or decoupled database), so any identification of an entrapment peptide represents a false discovery.

It is important to note that different search engines calculate the FDR on different levels - within a run, globally, on the precursor level, peptidoform level, protein group level, ... .
This module tests the **global precursor ion level FDR**. Search engines that do not calculate the FDR on this level can not be benchmarked with this module.

Two metrics are computed:

- **Lower bound FDP**: minimum estimate of the false discovery proportion, based on the raw count of entrapment identifications.

- **Paired FDP** (upper bound): refined upper bound using a paired peptide mapping, which accounts for entrapment peptides that are harder to identify than their target counterparts.

The combined method from Wen et al. is also implemented, which represents a less tight upper bound. This bound is available for local use in the intermediate file format, and not shown in the plots.

- **Combined FDP** (upper bound): corrected upper bound accounting for the 1:1 target-to-entrapment ratio in the search database.

Each workflow submission is classified as:

- **Valid**: the upper bound FDP is lower than the reported FDR threshold.
- **Inconclusive**: the lower bound is lower than the declared FDR but the upper bound is higher. This means that the actual FDP could be lower or higher than the reported FDR, therefore we can not say if the FDR is valid or not.
- **Invalid**: even the lower bound is higher than the declared FDR threshold.

## Critical requirements before running

> **Do not rename the raw files after download.** File names are used for run mapping and must match exactly.

> **Use the pre-digested entrapment FASTA — do not enable in-silico digestion.** The entrapment FASTA already contains peptide sequences (not full proteins). Enabling digestion in your search engine will lead to identified peptides without matched entrapments, which makes FDP calculation less accurate.

> **Do not add any variable modifications.**

## Data set

The benchmark dataset consists of three technical replicates of a human plasma digest acquired on an Orbitrap Astral (Thermo Fisher Scientific) in DIA mode with a 15-minute gradient The mass spectrometer was operated in positive ionization mode with data-independent acquisition, with a full MS scans over a mass range of m/z 380-980 with detection in the Orbitrap at a resolution of 240,000. In each cycle of data-independent acquisition, 300 windows of 2 Th were used to isolate and fragment all precursor ions from 380 to 980 m/z. A normalized collision energy of 25% was used for HCD fragmentation. MS2 scan range was set from 150 to 2000 m/z with detection in the Astral with a maximum injection time of 3 ms. Full details on the dataset can be found in [this preprint](https://www.biorxiv.org/content/10.64898/2026.01.29.702266v2)

The files can be downloaded from the [ProteoBench server](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/):

- Single archive with FASTA: [all_data_Entrapment_DIA_Astral.tar.gz](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/all_data_Entrapment_DIA_Astral.tar.gz).

- [LFQ_Astral_DIA_15min_50ng_Human_01.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/LFQ_Astral_DIA_15min_50ng_Human_01.raw)
- [LFQ_Astral_DIA_15min_50ng_Human_02.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/LFQ_Astral_DIA_15min_50ng_Human_02.raw)
- [LFQ_Astral_DIA_15min_50ng_Human_03.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/LFQ_Astral_DIA_15min_50ng_Human_03.raw)

**It is imperative not to rename the files once downloaded.**

The entrapment FASTA (`ProteoBenchFASTA_Entrapment_Human_with_contaminants_entrapment_pep.txt`) is available from the ProteoBench server. It contains human peptide sequences alongside a matched set of entrapment peptide sequences (suffixed `_p_target` to allow classification). **This file is pre-digested: do not apply enzymatic digestion in your search engine settings.**

## Metric calculation

ProteoBench reads the search engine output, maps runs to samples, and classifies each precursor identification as either a **target** or an **entrapment** hit based on the tag in the fasta.

The three FDP estimates are computed from the resulting set and compared to the reported FDR threshold (inferred from the output file). Let $N_T$ and $N_E$ be the number of identified target and entrapment precursors, respectively, at a given score (Q-value) threshold.

**Lower bound FDP**: the raw proportion of entrapment identifications.

```{math}
FDP_{lower} = \frac{N_E}{N_T + N_E}
```

**Combined FDP** (upper bound, Wen et al. 2025, eq. 1): corrects the raw entrapment proportion for the 1:1 ratio of target to entrapment sequences in the search database ($r = 1$).

```{math}
FDP_{combined} = \frac{N_E \left(1 + \dfrac{1}{r}\right)}{N_T + N_E}
```

**Paired FDP** (upper bound, Wen et al. 2025, eq. 2): refines the estimate using the target/entrapment peptide pairing. For each identified entrapment peptide, its paired target counterpart is looked up:

- $N_{E \sim T}$: identified entrapments whose paired target was **not** identified (unambiguous false positive).
- $N_{E \succ T}$: identified pairs where the entrapment scored **better** than its paired target (counted twice, reflecting the pair's symmetric contribution to the inflation).

```{math}
FDP_{paired} = \frac{N_E + N_{E \sim T} + 2\, N_{E \succ T}}{N_T + N_E}
```

The identifications are filtered at self-reported FDR of [0.001, 0.01, 0.1, maximum reported]. At each FDR, the lower and upper bounds are computed, and compared against the reported FDR threshold to classify a submission as **valid**, **inconclusive**, or **invalid** (see above).
Important: This means that the FDR calculation of a workflow can be e.g. valid at FDR = 0.01, and invalid at FDR=0.001.

## How to use

### Suggested parameters

The module currently accepts DIA-NN, FragPipe, FragPipe with DIA-NN quantification, and AlphaDIA output. Use the suggested parameters in Table 1 for a fair comparison between tools.

**Table 1. Suggested parameters**

| Parameter | Value |
|---|---|
| PSM / precursor FDR | 0.01 |
| Spectral library | Predicted from entrapment FASTA |
| Digestion | **None** (FASTA is pre-digested) |
| Fixed modifications | Carbamidomethylation (C) |
| Variable modifications | **None** |
| Precursor charge range | 1–5 |
| Precursor m/z range | 400–1000 |
| Fragment m/z range | 100–1800 |

### Submit your run for public usage

After uploading and privately inspecting your results, you can submit the run for public display. Upload the parameter file associated with your search (see tool-specific sections below), fill in the `Comments for submission` field if needed, confirm the metadata is correct, and press `I really want to upload it`.

You will receive a link to a GitHub pull request. Save it — it contains your run's unique identifier and allows you to communicate with the ProteoBench maintainers. Accepted submissions become publicly visible within a few working days.

**Table 2. Input files required for metric calculation and public submission**

| Tool | Input file | Parsed FDR Column | Parameter file |
|---|---|---|---|
| DIA-NN | `report.tsv` or `report.parquet` | Lib.Q.Value | `report.log.txt` |
| FragPipe (DIA-NN quant) | `report.tsv` or `report.parquet` | Q.Value | FragPipe `.workflow` |
| AlphaDIA | `precursors.parquet` | qval | AlphaDIA `log.txt` |

## Tool-specific settings

### [DIA-NN](https://github.com/vdemichev/DiaNN)

1. Import the raw `.raw` files.
2. Add the entrapment FASTA. Do not enable "Contaminants" — contaminants are already included in the FASTA.
3. **Disable in-silico digestion.** The FASTA is pre-digested; use '--cut ' in the additional parameter fields to disable enzymatic cleavage.
4. Enable library-free search / FASTA-based library generation (activates deep-learning prediction of spectra, RTs, and IMs).
5. Do not set verbosity / log level higher than 1, otherwise parameter parsing will fail.
6. Upload `report.tsv` or `report.parquet` for metric calculation, and `report.log.txt` for public submission.

### FragPipe with DIA-NN quantification

FragPipe workflows that produce a DIA-NN-style report are submitted as **FragPipe (DIA-NN quant)**. ProteoBench parses the precursor identifications from the DIA-NN report and extracts workflow metadata from the FragPipe `.workflow` file.

1. Use the ProteoBench entrapment FASTA as the sequence database. Do not add a second contaminant database.
2. Configure the search without enzymatic digestion. The FASTA contains pre-digested peptide entries, so in-silico digestion must remain disabled throughout the FragPipe/DIA-NN workflow. MSFragger Protein Digestion settings:

```
Load Rules:    nocleavage
Cuts 1:        @
No cuts 1:     @
```

To set these via the GUI: MSFragger tab -> Protein Digestion -> Load Rules = "nocleavage"; Cuts 1 = "@"; No cuts 1 = "@".
3. Keep variable modifications disabled. Carbamidomethylation (C) may be used as the fixed modification.
4. Use the DIA-NN report generated by FragPipe (`report.tsv` or `report.parquet`) for metric calculation.
5. Upload the FragPipe `.workflow` file for public submission. Do not upload the DIA-NN log as the parameter file for this workflow type.

### [AlphaDIA](https://github.com/MannLabs/alphadia)

AlphaDIA submissions are parsed from precursor-level output. The entrapment module currently expects AlphaDIA 2.x-style precursor output.

1. Use the ProteoBench entrapment FASTA and disable additional contaminants.
2. Configure AlphaDIA for a no-enzyme / pre-digested FASTA search: set "no-cleave" as the enzyme parameter.
3. Keep variable modifications disabled. Use Carbamidomethylation (C) as the fixed modification if alkylation was applied.
4. Upload `precursors.parquet` for metric calculation.
5. Upload the AlphaDIA `log.txt` file for public submission.

## Result description

After uploading, you will see the FDP bounds plotted against the FDR estimate reported by the search engine. A valid (conservative) FDR calculation has the empirical upper bound below the declared FDR threshold.

You can also compare the results with other submissions in the 'View Public + New Results' Tab. The following plots are shown:

- **Forest plot**: one horizontal interval per workflow, showing the lower bound FDP to the paired FDP upper bound. The declared FDR threshold is marked with a diamond.
- **FDP / FDR ratio vs # IDs**: scatter plot of paired FDP divided by the declared FDR (x-axis) against the number of identifications at 1% FDR (y-axis). Points to the left of x = 1 have an empirical FDP below the declared threshold.

## Define parameters

For public submission, the following parameters are extracted from the parameter file. If a parameter is not in the file, add it in `Comments for submission`.

- Software tool name and version
- FDR threshold for PSM / precursor, peptide, and protein level
- Precursor and fragment m/z range
- Precursor mass tolerance
- Fragment mass tolerance
- Fixed and variable modifications
- Minimum and maximum precursor charge
- Enzyme (should be "None" for this module)

**DISCLAIMER**: Parameter files may contain file paths that reveal personal usernames, system architecture, or directory structures (FASTA location, raw data location, tool installation paths). Review and sanitize file paths before submission to avoid disclosing institutional or personal identifiers.

Once submitted, a pull request link is shown. Save it to track your submission. Contact us via a [GitHub issue](https://github.com/Proteobench/ProteoBench/issues/new) or [email](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) if you encounter any problems.
