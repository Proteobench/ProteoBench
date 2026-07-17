# DIA ion entrapment (Astral)

{bdg-success}`alpha` {bdg-primary-line}`FDR validation` — DIA, Orbitrap Astral, global precursor-ion FDR

Uses entrapment peptides to assess whether the false discovery rate (FDR) reported by a DIA search
engine is reliable. Based on the entrapment approach in
[Wen et al., 2025](https://www.nature.com/articles/s41592-025-02719-x).

```{admonition} Alpha stage
:class: warning
Results and interfaces may change.
```

## At a glance

| | |
|---|---|
| Acquisition | DIA |
| Instrument | Orbitrap Astral |
| Level | Global precursor-ion FDR |
| Metric | Lower bound / combined / paired FDP |

## What this module tests

FDR control is a central assumption in proteomics data analysis: if a search engine reports 1%
FDR, the actual proportion of false discoveries should not exceed 1%. This module tests that
assumption empirically by spiking a known set of "entrapment" peptides into the search space. These
peptides cannot be present in the sample (they're derived from a shuffled/decoupled database), so
any identification of one is a genuine false discovery.

Search engines calculate FDR at different levels (within-run vs. global, precursor vs. peptidoform
vs. protein-group). **This module tests the global precursor-ion-level FDR** specifically — search
engines that don't calculate FDR at this level can't be benchmarked here.

Three metrics are computed:

- **Lower bound FDP**: minimum estimate of the false discovery proportion, from the raw count of
  entrapment identifications.
- **Combined FDP** (upper bound): corrected upper bound accounting for the 1:1 target-to-entrapment
  ratio in the search database.
- **Paired FDP** (upper bound): refined upper bound using a paired peptide mapping, accounting for
  entrapment peptides that are harder to identify than their target counterparts.

Each submission is classified as:

- **Valid**: the upper bound FDP is lower than the reported FDR threshold.
- **Inconclusive**: the lower bound is below the declared FDR but the upper bound is above it — the
  actual FDP could be either side of the reported value.
- **Invalid**: even the lower bound is above the declared FDR threshold.

## Critical requirements before running

```{important}
- **Do not rename the raw files after download.** File names are used for run mapping.
- **Use the pre-digested entrapment FASTA; do not enable in-silico digestion.** The FASTA already
  contains peptide sequences, not full proteins. Enabling digestion leads to identified peptides
  without matched entrapments, which makes FDP calculation less accurate.
- **Do not add any variable modifications.**
```

## Dataset

Three technical replicates of a human plasma digest acquired on an Orbitrap Astral in DIA mode with
a 15-minute gradient. Full MS scans over m/z 380–980 at 240,000 resolution (Orbitrap); 300 windows
of 2 Th isolating and fragmenting precursors from 380–980 m/z; 25% normalized collision energy
(HCD); MS2 over m/z 150–2000 (Astral), 3 ms maximum injection time. Full dataset details are in
[this preprint](https://www.biorxiv.org/content/10.64898/2026.01.29.702266v2).

**Download:**
- [All raw files + FASTA (single archive)](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/all_data_Entrapment_DIA_Astral.tar.gz)
- Individual raw files (`Human_01`–`03`) from the
  [ProteoBench server](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/)

```{important}
Do not rename the downloaded raw files.
```

The entrapment FASTA (`ProteoBenchFASTA_Entrapment_Human_with_contaminants_entrapment_pep.txt`) is
available from the ProteoBench server. It contains human peptide sequences alongside a matched set
of entrapment peptides (suffixed `_p_target` for classification). **This file is pre-digested — do
not apply enzymatic digestion in your search engine settings.**

## How the metric is calculated

ProteoBench reads the search engine output, maps runs to samples, and classifies each precursor
identification as a **target** or an **entrapment** hit based on the FASTA tag. The three FDP
estimates are computed from the resulting set and compared to the reported FDR threshold (inferred
from the output file).

## Run your workflow

The module currently accepts DIA-NN, FragPipe, FragPipe with DIA-NN quantification, and AlphaDIA
output. Use the suggested parameters below for a fair comparison between tools, then follow
[Your First Submission](../../your-first-submission/index.md) to upload, inspect, and (if you'd
like) submit your results publicly.

**Table: suggested parameters**

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

## Tool-specific setup

**Table: input files required for metric calculation and public submission**

| Tool | Input file | Parsed FDR column | Parameter file |
|---|---|---|---|
| DIA-NN | `report.tsv` or `report.parquet` | Lib.Q.Value | `report.log.txt` |
| FragPipe (DIA-NN quant) | `report.tsv` or `report.parquet` | Q.Value | FragPipe `.workflow` |
| AlphaDIA | `precursors.parquet` | qval | AlphaDIA `log.txt` |

:::{dropdown} DIA-NN
1. Import the raw `.raw` files.
2. Add the entrapment FASTA. Do not enable "Contaminants" (already included).
3. **Disable in-silico digestion** — use `--cut ` in additional parameters, since the FASTA is
   pre-digested.
4. Enable library-free search / FASTA-based library generation.
5. Do not set verbosity/log level above 1, or parameter parsing will fail.
6. Upload `report.tsv` or `report.parquet` for scoring and `report.log.txt` for public submission.
:::

:::{dropdown} FragPipe with DIA-NN quantification
Submitted as **FragPipe (DIA-NN quant)**. ProteoBench parses precursor identifications from the
DIA-NN-style report and workflow metadata from the FragPipe `.workflow` file.

1. Use the entrapment FASTA as the sequence database; do not add a second contaminant database.
2. Configure the search without enzymatic digestion throughout the FragPipe/DIA-NN workflow.
   MSFragger Protein Digestion settings:

   ```
   Load Rules:    nocleavage
   Cuts 1:        @
   No cuts 1:     @
   ```

   Via the GUI: MSFragger tab → Protein Digestion → Load Rules = "nocleavage"; Cuts 1 = "@"; No
   cuts 1 = "@".
3. Keep variable modifications disabled; carbamidomethylation (C) may be used as the fixed
   modification.
4. Use the DIA-NN report generated by FragPipe (`report.tsv` or `report.parquet`) for scoring.
5. Upload the FragPipe `.workflow` file for public submission (not the DIA-NN log).
:::

:::{dropdown} AlphaDIA
Parsed from precursor-level output; the entrapment module currently expects AlphaDIA 2.x-style
precursor output.

1. Use the entrapment FASTA and disable additional contaminants.
2. Configure a no-enzyme / pre-digested-FASTA search: set "no-cleave" as the enzyme parameter.
3. Keep variable modifications disabled; use carbamidomethylation (C) as the fixed modification if
   alkylation was applied.
4. Upload `precursors.parquet` for scoring and the AlphaDIA `log.txt` for public submission.
:::

## Result columns

After uploading, you'll see the FDP bounds plotted against the FDR estimate reported by the search
engine. A valid (conservative) FDR calculation has the empirical upper bound below the declared FDR
threshold.

The "View Public + New Results" tab shows:

- **Forest plot**: one horizontal interval per workflow, from the lower bound FDP to the paired FDP
  upper bound, with the declared FDR threshold marked as a diamond.
- **FDP / FDR ratio vs. # IDs**: paired FDP divided by the declared FDR (x-axis) against the number
  of identifications at 1% FDR (y-axis). Points left of x = 1 have an empirical FDP below the
  declared threshold.

## Parameters tracked for public submission

ProteoBench extracts:

- software tool name and version
- FDR threshold (PSM/precursor, peptide, protein level)
- precursor and fragment m/z range
- precursor and fragment mass tolerance
- fixed and variable modifications
- minimum/maximum precursor charge
- enzyme (should be "None" for this module)

If a parameter isn't in your file, add it in `Comments for submission`.

```{admonition} Check your parameter file for personal information
:class: warning
Parameter files can embed local file paths (FASTA location, raw data location, tool installation
paths) that may reveal personal or institutional information. Review and sanitize before
submission.
```

Once submitted you'll get a pull-request link; save it to track your submission (see
[what happens next](../../your-first-submission/index.md#6-submit-for-public-review)).
[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues/new) with any problems.
