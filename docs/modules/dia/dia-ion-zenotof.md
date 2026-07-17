# LFQ, precursor ion (ZenoTOF)

{bdg-info}`beta` {bdg-primary-line}`Quantification` — DIA, ZenoTOF 8600, precursor-ion level

Compares label-free quantification (LFQ) accuracy and sensitivity for workflows run on
data-independent acquisition (DIA) data, namely Zeno SWATH DIA with 85 variable windows, on a
ZenoTOF 8600 (SCIEX).

## At a glance

| | |
|---|---|
| Acquisition | DIA, Zeno SWATH (85 variable windows) |
| Instrument | ZenoTOF 8600 |
| Level | Precursor ion (modified sequence + charge) |
| Metric | Epsilon (quantification accuracy) |

## What this module tests

This module is best suited to evaluate the impact of, among others:

- search engine identification
- peak picking
- low-level ion signal normalization

It is **not** designed to evaluate later-stage post-processing of quantitative data (e.g. missing
value replacement or manual filtering); please upload data without that kind of post-processing.

## Dataset

A not-yet-released ZenoTOF 8600 DIA dataset using the same sample composition (conditions "A" and
"B") as described in [Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6):
commercial peptide digest standards of *Escherichia coli*, yeast, and human, at logarithmic fold
changes (log2FC) of 0, −1, and 2 respectively.

Peptides were separated on an IonOpticks Aurora® XS Ultimate column (25 cm × 75 µm, 1.7 µm) at
0.250 µL/min, 40 °C, over a 15-min gradient (3% B hold, ramp to 35% over 15 min, then 65% and 80%
B, wash, re-equilibrate). An OptiFlow Pro Nano source with NanoCal probe was used. The 15-min Zeno
SWATH DIA method used 85 variable windows over TOF MS 400–900 Da and MS/MS 140–1750 Da, Zeno trap
pulsing on, 16 ms MS/MS accumulation, with an MS1 survey scan (400–1500 Da, 50 ms) before each cycle.

**Download:**
- [All raw files + FASTA (single archive)](https://proteobench.cubimed.rub.de/raws/DIA-ZenoSWATH/all_data_LFQ_Quant_DIA_ZenoSWATH.tar.gz)
  from the [ProteoBench server](https://proteobench.cubimed.rub.de/raws/DIA-ZenoSWATH/)
- Also on [ProteomeXchange PXD070049](https://www.ebi.ac.uk/pride/archive/projects/PXD070049)
- [FASTA (HYE mixed species + contaminants)](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip),
  contaminants from [Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145)

```{important}
Do not rename the downloaded raw files.
```

## How the metric is calculated

For each precursor ion, ProteoBench sums the signal per raw file, removes contaminants (flagged
`Cont_` in the FASTA) and precursors matching multiple species, log2-transforms the remaining
values, then computes the mean and coefficient of variation (CV) per condition. The difference
between the mean log2 intensity in A and B is compared against the expected log2 fold change for
that precursor's species — that difference is **epsilon**.

The main plot shows the number of unique precursor ions quantified (vertical axis) against the
mean or median absolute epsilon (horizontal axis).

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
| PEAKS | `PEAKS_lfq_features.csv` | `PEAKS_parameters.txt` |
| Spectronaut | `Spectronaut_report.tsv` | `Spectronaut_ExperimentSetupOverview.txt` |

Expand a tool below for setup details.

:::{dropdown} DIA-NN
1. Import raw files.
2. Add the FASTA, but do not select "Contaminants" (already included).
3. Turn on FASTA digest for library-free search / library generation.
4. Do not set verbosity/log level above 1, or parameter parsing will fail.
5. Upload `*_report.tsv` or `*_report.parquet` for scoring and `report.log.txt` for public
   submission.
:::

:::{dropdown} AlphaDIA
1. Select the FASTA and import `.raw` files in "Input files".
2. Define search parameters in "Method settings".
3. Turn on "Predict Library".
4. Turn on "Precursor Level LFQ".
5. Required output files depend on version: AlphaDIA v1.x needs both `precursors.tsv` and
   `precursor.matrix.tsv` (or use the
   [conversion notebook](https://github.com/Proteobench/ProteoBench/blob/main/jupyter_notebooks/submission/ProteoBench_input_conversion.ipynb));
   later versions need only `precursors.parquet`/`.tsv`.

```{note}
Version ≥1.10.4 is recommended for improved MS1-cycle checking.
```
:::

:::{dropdown} FragPipe (DIA-NN quant)
1. Load the DIA_SpecLib_Quant workflow.
2. After importing raw files, assign experiments "by File Name".
3. **Do not add contaminants when adding decoys to the database.**
4. Upload `*report.tsv` for scoring and `fragpipe.workflow` for public submission.

FragPipe reports protein identifiers across two columns ("Proteins" and "Mapped Proteins"); these
are concatenated to form the protein groups.
:::

:::{dropdown} Spectronaut
Accepted format: BGS Factory Report — `..._Report.tsv` for scoring,
`..._Report.setup.txt` for parameter parsing.

1. Import the module FASTA in "Databases" (UniProt parsing rule).
2. In "Analysis", select "Set up a DirectDIA Analysis from folder" and load the raw-file folder.
3. Select the FASTA as the database.
4. Choose search settings.
5. Assign conditions: `LFQ_ZenoTOF8600_ZenoSWATH_85VW_15min_Nano_50ng_Condition_A_REP1`–`REP3` to
   "A", the equivalent `Condition_B` files to "B".
6. Skip GO terms/library extensions.
7. Run the search, then export a BGS Factory Report as `..._Report.tsv`.
8. Upload `..._Report.tsv` privately and `..._Report.setup.txt` for public submission.
:::

:::{dropdown} MaxDIA (work in progress)
By default MaxDIA uses its own contaminants-only FASTA. This module's FASTA already includes a
curated contaminant set, so **untick "Include contaminants"** (Global parameters → Sequences), and
set FASTA parsing to `Identifier rule = >([^\t]*)`, `Description rule = >(.*)`. Use "No Fractions"
and name experiments `A_REP1`–`A_REP3`, `B_REP1`–`B_REP3`.

Upload `evidence.txt` for scoring and `mqpar.xml` for public submission.
:::

:::{dropdown} PEAKS
Rename samples (Sample 1→6) to match the `.wiff` file names exactly:
`LFQ_ZenoTOF8600_ZenoSWATH_85VW_15min_Nano_50ng_Condition_A_REP1`–`REP3`,
`..._Condition_B_REP1`–`REP3`.

Set Enzyme = trypsin, Instrument = ZenoTOF, Fragment = CID, Acquisition = DIA. In the workflow, use
the Quantification option; define search parameters in "DB search". In "Quantification" use "Label
Free" (individually or grouped by condition); in "Report" set both Precursor/Peptide FDR and
Protein Group FDR to 1%. Check "All Search Parameters" and the "Feature Vector CSV" (Export tab)
once finished.
:::

:::{dropdown} Custom format
If your tool isn't listed above, upload a tab-delimited table with:

- `Sequence` — unmodified peptide sequence
- `Proteins` — `;`-separated identifiers, including the species flag (e.g. `_YEAST`)
- `Charge` — precursor charge
- `Modified sequence` — sequence with localized modifications, ideally
  [ProForma](https://www.psidev.info/proforma)
- one quantitative column per sample:
  `LFQ_ZenoTOF8600_ZenoSWATH_85VW_15min_Nano_50ng_Condition_A_REP1` …
  `..._Condition_B_REP3`

The table must not contain non-validated ions.
:::

### How ProteoBench maps each tool's columns

Each tool's output format is described in a `.toml` file under
`proteobench/io/parsing/io_parse_settings/`, defining `[mapper]` (column-name mapping),
`[condition_mapper]`/`[run_mapper]` (raw file to condition/sample), `[species_mapper]` (protein-ID
suffix to species), `[general]` (contaminant flag `Cont_` and decoy flag), and
`[modifications_parser]` where needed.

## Result columns

After upload, the results table includes: the precursor ion (modified sequence + charge); mean and
standard deviation of log2-transformed and of raw intensity per condition; CV per condition; the
difference of mean log2 values between conditions; per-raw-file intensity; the number of raw files
with a non-missing value; species and whether the sequence is species-specific; the expected ratio
for that species; and epsilon.

Use the slider to set the minimum number of raw files a precursor must be quantified in to be
included in the plot.

## Parameters tracked for public submission

Upload your parameter file under "Download calculated ratios"; see
[Tool-specific setup](#tool-specific-setup) above for which file that is per tool. ProteoBench
tracks:

- software tool name and version; search engine name and version, if different
- FDR threshold (PSM, precursor, peptide, protein level)
- match-between-runs (on/off)
- precursor and fragment m/z range and mass tolerance
- enzyme (Trypsin, for this dataset) and maximum missed cleavages
- minimum/maximum peptide length
- fixed and variable modifications, and the maximum number of modifications
- minimum/maximum precursor charge

If any of these are missing from your parameter file, add them in the `Comments for submission`
field.

```{admonition} Check your parameter file for personal information
:class: warning
Parameter files can embed local file paths (FASTA location, `.wiff`/`.wiff.scan` data location, tool
installation paths) that may reveal personal or institutional information. Review and sanitize
before submission.
```

Once submitted you'll get a pull-request link; save it to track your submission (see
[what happens next](../../your-first-submission/index.md#6-submit-for-public-review)).
[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues/new) with any problems.
