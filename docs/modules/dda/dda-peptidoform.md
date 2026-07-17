# LFQ, peptidoform (QExactive)

{bdg-info}`beta` {bdg-primary-line}`Quantification` — DDA, Q Exactive HF-X Orbitrap, peptidoform level

Compares label-free quantification (LFQ) accuracy and sensitivity for workflows run on the same
data-dependent acquisition (DDA) dataset as [LFQ, precursor ion (QExactive)](dda-ion-qexactive.md),
but scored at the **peptidoform level** (summarized from precursor-ion quantities) rather than the
precursor-ion level.

## At a glance

| | |
|---|---|
| Acquisition | DDA |
| Instrument | Q Exactive HF-X Orbitrap |
| Level | Peptidoform |
| Metric | Epsilon (quantification accuracy) |

## What this module tests

The dataset and metric definitions are identical to the
[precursor-ion-level module](dda-ion-qexactive.md); the only difference is that quantities are
summarized to the peptidoform level before scoring. See that page for the full description of the
dataset, sample composition, and how epsilon is calculated.

## Run your workflow

Run your analysis on the [same dataset](dda-ion-qexactive.md#dataset), then follow
[Your First Submission](../../your-first-submission/index.md) to upload, inspect, and submit
your results. The [web app](https://proteobench.cubimed.rub.de/Quant_LFQ_DDA_peptidoform) is where
you upload results and submit them for public review.

## Tool-specific setup

**Table: input files required for metric calculation and public submission**

| Tool | Input file | Parameter file |
|---|---|---|
| Custom | `custom_input.tsv` | — |
| PEAKS | `lfq.features.csv` | `*.txt` |
| WOMBAT | `*.csv` | `config.yaml` |

```{note}
Tool-specific setup instructions for this module are still being written. In the meantime, the
[precursor-ion-level module's tool-specific setup](dda-ion-qexactive.md#tool-specific-setup) covers
the same tools and input conventions for the QExactive DDA dataset.
```

## Parameters tracked for public submission

Upload your parameter file alongside your results. See
[Your First Submission](../../your-first-submission/index.md#5-fill-in-the-metadata) for the
general submission and metadata process, and the
[precursor-ion-level module](dda-ion-qexactive.md#parameters-tracked-for-public-submission) for the
full list of parameters ProteoBench tracks for this dataset.

[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues/new) with any problems.
