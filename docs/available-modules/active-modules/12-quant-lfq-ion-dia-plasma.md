# DIA quantification - precursor ion level (PYE: Plasma/Yeast/E. coli)

This module benchmarks DIA precursor-level quantification on plasma samples spiked with yeast and E. coli.
Runs can be inspected privately, and submitted publicly with metadata for community comparison.

**Release stage: BETA.**

## Data set

The PYE setup uses three species:
- HUMAN (plasma background)
- YEAST (spike-in)
- ECOLI (spike-in)

Expected condition ratios (A/B):
- HUMAN: 1.0 (log2FC = 0)
- YEAST: 1/3 (log2FC ≈ -1.585)
- ECOLI: 2.0 (log2FC = 1)

Current parser settings expect 12 runs with these raw names:
- A9_G_DIA_nLC_tTOF_R1 ... A9_G_DIA_nLC_tTOF_R6
- B9_G_DIA_nLC_tTOF_R1 ... B9_G_DIA_nLC_tTOF_R6

**Do not rename raw files.**

## Metric calculation

Per precursor (modified sequence + charge), ProteoBench computes condition-level summaries and epsilon (difference between observed and expected log2 fold-change), then derives PYE-specific benchmarking metrics.

Main plot dimensions:
- **X-axis**: absolute log2 fold-change error for spike-ins (YEAST + ECOLI), as Median or Mean
- **Y-axis**: number of quantified spike-in precursors
- **Dot size**: dynamic range of HUMAN plasma precursors (mean of condition-wise log10 90th-10th percentile spread)
- **Dot opacity**: HUMAN plasma quantification accuracy (absolute epsilon; darker = better)

Two error calculation modes are available:
- **Global**: globally calculated error
- **Species-weighted**: per-species error averaged equally
In both mean and median.

A cutoff slider filters precursors by minimum number of runs in which the precursor is observed.

## How to use

### Input data for private visualization

Currently supported input formats in this module:
- DIA-NN
- AlphaDIA
- Spectronaut
- PEAKS
- FragPipe (DIA-NN Quant)
- Custom

### Submit your run for public usage

For public submission, upload:
1. The quantification output file
2. The matching parameter/log file(s)
3. Optional comments

Then confirm metadata and submit. A GitHub pull request link is generated for tracking and review.

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
