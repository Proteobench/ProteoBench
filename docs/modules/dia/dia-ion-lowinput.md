# LFQ, low input

{bdg-success}`alpha` {bdg-primary-line}`Quantification` — DIA, Orbitrap Astral, low sample input

Compares the sensitivity and quantification accuracy of workflows for data acquired with
data-independent acquisition (DIA) on an Astral at low sample input (single-cell-scale amounts).

For bulk sample analyses on the same instrument type, see [LFQ, precursor ion (Astral)](dia-ion-astral.md).

## At a glance

| | |
|---|---|
| Acquisition | DIA |
| Instrument | Orbitrap Astral, low input |
| Level | Precursor ion |
| Metric | Epsilon (quantification accuracy) |

## What this module tests

Search-specific instructions, metric definitions, and result-column descriptions are shared with
the bulk [DIA Astral module](dia-ion-astral.md); see that page for the full detail. This module is
**not** designed to evaluate later-stage post-processing (e.g. missing value replacement or manual
filtering).

## Dataset

A subset of the Astral DIA data described in
[Bubis et al., 2024](https://www.biorxiv.org/content/10.1101/2024.02.01.578358v2.abstract), using
only the series with 240:10 (condition "A") and 200:50 (condition "B") ratios, three replicates
each. Samples are a mixture of HeLa (Thermo Scientific, Pierce™ HeLa Protein Digest Standard,
88328) and yeast (Promega, MS Compatible Yeast Protein Extract Digest, *S. cerevisiae*, V7461),
combined in 0.1% TFA.

**Download:**
- [All raw files + FASTA (single archive)](https://proteobench.cubimed.rub.de/raws/DIA-SingleCell/all_data_LFQ_Quant_DIA_SC.tar.gz)
- Or from [ProteomeXchange PXD049412](https://www.ebi.ac.uk/pride/archive/projects/PXD049412):
  `20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1`–`r3` (condition A) and
  `..._200pg_50pg_H_Y_r1`–`r3` (condition B)
- [FASTA (HY mixed species + contaminants)](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HY.zip),
  contaminants from [Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145)

```{important}
Do not rename the downloaded raw files.
```

## Run your workflow

Run your analysis on the downloaded files, then follow
[Your First Submission](../../your-first-submission/index.md) to upload, inspect, and (if you'd
like) submit your results publicly.

## Tool-specific setup

**Table: input files required for metric calculation and public submission**

| Tool | Input file | Parameter file |
|---|---|---|
| AlphaDIA | `precursors.parquet`/`.tsv` (v2+) or `precursor.matrix.tsv` + `precursors.tsv` (v1) | `log_alphadia.txt` |
| Custom | `custom_input.tsv` | — |
| DIA-NN | `report.tsv` or `report.parquet` | `report.log.txt` |
| FragPipe | `combined_ion.tsv` | `fragpipe.workflow` |
| FragPipe (DIA-NN quant) | `report.tsv` or `report.parquet` | `fragpipe.workflow` |
| MSAID | `MSAID_output.tsv` | `MSAID_params.csv` |
| MaxQuant | `evidence.txt` | `mqpar.xml` |
| PEAKS | `lfq.features.csv` | `*.txt` |
| Spectronaut | `*.tsv` | `ExperimentSetupOverview.txt` |

For per-tool setup steps, see the [DIA Astral bulk module's tool-specific setup](dia-ion-astral.md#tool-specific-setup) — the same tools and general workflow apply here.

:::{dropdown} Custom format
If your tool isn't listed above, upload a tab-delimited table with:

- `Sequence` — unmodified peptide sequence
- `Proteins` — `;`-separated identifiers, including the species flag (e.g. `_YEAST`)
- `Charge` — precursor charge
- `Modified sequence` — sequence with localized modifications, ideally
  [ProForma](https://www.psidev.info/proforma)
- one quantitative column per sample:
  `20231123_DIA_240k_20Th_40ms_FAIMSCV-48_gas3p8_240pg_10pg_H_Y_r1`–`r3` (condition A),
  `..._200pg_50pg_H_Y_r1`–`r3` (condition B)

The table must not contain non-validated ions.
:::

## Parameters tracked for public submission

Parameters tracked, result columns, and how the metric is calculated are the same as the
[DIA Astral bulk module](dia-ion-astral.md); see that page for the full list.

[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues/new) with any problems.
