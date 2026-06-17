# DIA Ion Entrapment - Astral

This module uses entrapment peptides to assess whether the false discovery rate (FDR) reported by a DIA search engine is reliable. It is based on the entrapment approach described in [Wen et al., 2025](https://www.nature.com/articles/s41592-025-02719-x).

> **This module is in alpha stage. Results and interfaces may change.**

## Purpose

FDR control is a central assumption in proteomics data analysis. When a search engine reports 1% FDR, the actual proportion of false discoveries should not exceed 1%. This module tests that assumption empirically by spiking a known set of "entrapment" peptides into the search space. These peptides cannot be present in the sample (they are derived from a shuffled or decoupled database), so any identification of an entrapment peptide represents a false discovery.

It is important to note that different search engines calculate the FDR on different levels - within a run, globally, on the precursor level, peptidoform level, protein group level, ... .
This module tests the **global precursor ion level FDR**. Search engines that do not calculate the FDR on this level can not be benchmarked with this module.

Three metrics are computed:

- **Lower bound FDP**: minimum estimate of the false discovery proportion, based on the raw count of entrapment identifications.
- **Combined FDP** (upper bound): corrected upper bound accounting for the 1:1 target-to-entrapment ratio in the search database.
- **Paired FDP** (upper bound): refined upper bound using a paired peptide mapping, which accounts for entrapment peptides that are harder to identify than their target counterparts.

Each workflow submission is classified as:

- **Valid**: the upper bound FDP is lower than the reported FDR threshold.
- **Inconclusive**: the lower bound is lower than the declared FDR but the upper bound is higher. This means that the actual FDP could be lower or higher than the reported FDR, therefore we can not say if the FDR is valid or not.
- **Invalid**: even the lower bound is higher than the declared FDR threshold.

## Critical requirements before running

> **Do not rename the raw files after download.** File names are used for run mapping and must match exactly.

> **Use the pre-digested entrapment FASTA — do not enable in-silico digestion.** The entrapment FASTA already contains peptide sequences (not full proteins). Enabling digestion in your search engine will lead to identified peptides without matched entrapments, which makes FDP calculation less accurate.

> **Do not add any variable modifications.**

## Data set

The benchmark dataset consists of three technical replicates of a human plasma digest acquired on an Orbitrap Astral (Thermo Fisher Scientific) in DIA mode with a 15-minute gradient.

Download the raw files from the ProteoBench server:

- `LFQ_Astral_DIA_15min_50ng_Human_01`
- `LFQ_Astral_DIA_15min_50ng_Human_02`
- `LFQ_Astral_DIA_15min_50ng_Human_03`

**It is imperative not to rename the files once downloaded.**

The entrapment FASTA (`ProteoBenchFASTA_Entrapment_Human_with_contaminants_entrapment_pep.txt`) is available from the ProteoBench server. It contains human peptide sequences alongside a matched set of entrapment peptide sequences (suffixed `_p_target` to allow classification). **This file is pre-digested: do not apply enzymatic digestion in your search engine settings.**

## Metric calculation

ProteoBench reads the search engine output, maps runs to samples, and classifies each precursor identification as either a **target** or an **entrapment** hit based on the tag in the fasta.

The three FDP estimates are computed from the resulting set and compared to the reported FDR threshold (inferred from the output file).

## How to use

### Input data for private visualisation

The module currently accepts DIA-NN output (`report.tsv` or `report.parquet`). Use the suggested parameters in Table 1 for a fair comparison between tools.

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

## Tool-specific settings

### [DIA-NN](https://github.com/vdemichev/DiaNN)

1. Import the raw `.raw` files.
2. Add the entrapment FASTA. Do not enable "Contaminants" — contaminants are already included in the FASTA.
3. **Disable in-silico digestion.** The FASTA is pre-digested; use '--cut ' in the additional parameter fields to disable enzymatic cleavage.
4. Enable library-free search / FASTA-based library generation (activates deep-learning prediction of spectra, RTs, and IMs).
5. Do not set verbosity / log level higher than 1, otherwise parameter parsing will fail.
6. Upload `report.tsv` or `report.parquet` for metric calculation, and `report.log.txt` for public submission.

## Result description

After uploading, you will see the FDP bounds plotted against the FDR estimates by the search engine. A valid (conservative) FDR calculation shows as both the upper and lower bound being higher than the FDR estimation.

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
