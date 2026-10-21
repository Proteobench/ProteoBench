# LFQ, human plasma

{bdg-success}`beta` {bdg-primary-line}`Quantification` — DIA, timsTOF, human plasma background (PYE)

```{admonition} This module is in beta stage
:class: note
This module has been validated and is suitable for submissions. However, metrics or thresholds may
be refined as we gather more community results and feedback.
```

Compares the sensitivity and quantification accuracy of workflows for data-independent acquisition
(DIA) data on human plasma samples spiked with yeast and *E. coli* (the PYE dataset:
Plasma/Yeast/*E. coli*).

```{button-link} https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_Plasma
:color: primary
:class: sd-px-4

Open in web app
```

## At a glance

| | |
|---|---|
| Acquisition | DIA |
| Instrument | timsTOF, nano-LC |
| Level | Precursor ion |
| Metric | Spike-in log2FC error, dynamic range, plasma accuracy |

## What this module tests

This module is best suited to evaluate the impact of, among others:

- search engine identification
- peak picking
- low-level ion signal normalization
- performance on complex biological matrices (plasma background)

It is **not** designed to evaluate later-stage post-processing of quantitative data (e.g. missing
value replacement or manual filtering); please upload data without that kind of post-processing.

## Dataset

Based on the benchmark study by
[Distler et al., Nat. Comms.](https://www.nature.com/articles/s41467-025-64501-z), the PYE dataset
uses a three-component mixture:

- **HUMAN** (plasma background) — the complex endogenous proteome, expected ratio A/B = 1.0 (log2FC = 0)
- **YEAST** (spike-in) — expected ratio A/B = 1/3 (log2FC ≈ −1.585)
- **ECOLI** (spike-in) — expected ratio A/B = 2.0 (log2FC = 1)

Samples are commercial peptide digest standards (*E. coli*: Waters Corporation; *S. cerevisiae*:
Promega; human plasma as the complex background), mixed to the ratios above, with six technical
replicates per condition (12 raw files total). Acquisition used a timsTOF with nano-LC DIA. Raw
files follow the naming `A9_G_DIA_nLC_tTOF_R1`–`R6` (condition A) and `B9_G_DIA_nLC_tTOF_R1`–`R6`
(condition B).

**Download:**
- [All raw files + FASTA (single archive)](https://proteobench.cubimed.rub.de/raws/DIA-plasma/all_data_LFQ_Quant_DIA_Plasma.tar.gz)
- Or from [ProteomeXchange JPST003358](https://repository.jpostdb.org/entry/JPST003358):
  `A9_G_DIA_nLC_tTOF_R1`–`R6.d`, `B9_G_DIA_nLC_tTOF_R1`–`R6.d`
- [FASTA (HYE mixed species + contaminants)](https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip),
  contaminants from [Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145)

```{important}
Do not rename the downloaded raw files.
```

## How the metric is calculated

Contaminant sequences (flagged `Cont_` in the FASTA) and precursor ions matching multiple species,
or not quantified in any raw file, are removed. Quantities are log2-transformed, and the mean per
condition is computed with standard deviation and CV. For each precursor ion, the difference
between mean log2 in condition A and B is compared to its expected value (epsilon).

**Main plot dimensions:**

- **X-axis**: absolute log2 fold-change error for spike-ins (YEAST + ECOLI), as Median or Mean
- **Y-axis**: number of quantified spike-in precursor ions
- **Dot size**: dynamic range of HUMAN plasma precursors (mean condition-wise log10 90th–10th
  percentile spread)
- **Dot opacity**: HUMAN plasma quantification accuracy (absolute epsilon; darker = more accurate)

**Calculation modes** (available in Mean and Median variants):

- **Global**: error calculated across all spike-in precursors together
- **Species-weighted**: per-species error (YEAST, ECOLI), averaged equally

A cutoff slider filters precursors by the minimum number of runs in which they're observed.

### Dynamic range calculation

The dynamic range summarises over how many orders of magnitude a workflow quantifies the human plasma background. It is calculated on the HUMAN precursor ions only, and for each condition separately:

1. Take the mean intensity of each HUMAN precursor ion in that condition (`Intensity_mean_A` or `Intensity_mean_B` in the intermediate table).
2. Log10-transform these mean intensities.
3. Subtract the 10th percentile from the 90th percentile of the resulting distribution.

The values of condition A and condition B are then averaged:

```
dynamic_range = mean( P90(log10 I_A) - P10(log10 I_A),
                      P90(log10 I_B) - P10(log10 I_B) )
```

Because the values are log10-transformed, the dynamic range is expressed in orders of magnitude. A dynamic range of 3.0 means that the central 80% of the quantified plasma precursor ions span three orders of magnitude in intensity. A larger value indicates that the workflow quantifies both high-abundant and low-abundant plasma precursor ions, whereas a smaller value indicates that quantification is restricted to a narrower abundance window.

The 10th and 90th percentiles are used instead of the minimum and maximum so that the metric is not determined by single extreme precursor ions. The dynamic range is recomputed for every value of the cutoff slider, and the condition-wise values (`dynamic_range_human_plasma_A` and `dynamic_range_human_plasma_B`) are stored next to the averaged value in the submitted datapoint. The same explanation is available as a tooltip in the web interface: hover over the caption below the overview plot, or open the "How are the metrics calculated?" panel at the top of the page.

### Identification counts

The number of quantified precursor ions is reported both for the spike-ins combined and for each species separately:

| Metric | Description |
|---|---|
| `nr_quantified_spike_ins` | YEAST plus ECOLI precursor ions (the y-axis of the overview plot) |
| `nr_quantified_HUMAN` | HUMAN plasma background precursor ions |
| `nr_quantified_YEAST` | YEAST spike-in precursor ions |
| `nr_quantified_ECOLI` | ECOLI spike-in precursor ions |

The per-species counts are stored for every cutoff level and are shown in the hover text of the overview plot as well as in the benchmark results table. They allow the identification depth in the complex plasma background to be assessed separately from the depth reached for the spike-in species, which is relevant because the two behave differently in a high dynamic range matrix.

## In-depth plots

For a single benchmark run the following plots are available in the "View Single Result" tab:

- **Abundance range plot**: the normalised precursor intensity against the intensity rank, with the rolling median of the absolute epsilon on the secondary y-axis. A species is selected with the dropdown menu; the rank is assigned within the selected species, so the count axis runs from 1 to the number of precursor ions quantified for that species. The intensities remain normalised against the highest intensity over all species, so that the species can be compared on a common intensity scale.
- **Missing values plot**: distribution of the percentage of missing values of the quantified HUMAN precursor ions against their intensity rank.
- **Log2 fold change distributions**: density of the measured log2 fold changes per species, with the expected ratios indicated.
- **Coefficient of variation**: CV distribution in condition A and B.
- **Signed epsilon plot**: distribution of the signed epsilon (measured minus expected log2 fold change) per species, shown as a violin plot with an embedded box plot and a reference line at zero. Values below zero indicate that the log2 fold change is underestimated, values above zero that it is overestimated. The median signed epsilon and the percentage of precursor ions on either side of zero are annotated per species. A distribution centred on zero indicates an unbiased workflow. Note that ratio compression shifts the two spike-in species in opposite directions, because YEAST is expected below zero (log2FC = -1.585) and ECOLI above zero (log2FC = 1).
- **MA plot**: measured log2 fold change against the mean abundance, coloured by species.

## Run your workflow

Run your analysis on the downloaded files with the tool of your choice; the module supports
multiple input formats to maximize flexibility. Then follow
[Your First Submission](../../your-first-submission/index.md) to upload, inspect, and (if you'd
like) submit your results publicly. The
[web app](https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_Plasma) is where you upload results
and submit them for public review.

## Tool-specific setup

**Table: input files required for metric calculation and public submission**

| Tool | Input file | Parameter file |
|---|---|---|
| AlphaDIA | `precursors.parquet/.tsv (v2+) or precursor.matrix.tsv + precursors.tsv (v1)` | `log_alphadia.txt` |
| Custom | `custom_input.tsv` | — |
| DIA-NN | `report.tsv or report.parquet` | `report.log.txt` |
| FragPipe (DIA-NN quant) | `report.tsv or report.parquet` | `fragpipe.workflow` |
| PEAKS | `lfq.features.csv` | `*.txt` |
| Spectronaut | `*.tsv` | `ExperimentSetupOverview.txt` |

Expand a tool below for setup details.

:::{dropdown} DIA-NN
1. Generate a spectral library from the provided FASTA using DIA-NN's library-generation mode.
2. Process raw files with the standard DIA-NN DIA workflow.
3. Export results as `*_report.tsv` or `*_report.parquet`.
4. Collect `*_report.log.txt` for public submission.
:::

:::{dropdown} AlphaDIA
1. Process DIA raw files with AlphaDIA's standard workflow.
2. Both `precursors.tsv` (long-format precursor-level data) and `precursor.matrix.tsv`
   (quantification matrix) are required and must both be uploaded.
3. If your AlphaDIA version outputs a different format, preprocess with the
   [conversion notebook](https://github.com/Proteobench/ProteoBench/blob/main/jupyter_notebooks/ProteoBench_input_conversion.ipynb).
4. Upload `log.txt` for public submission.
:::

:::{dropdown} Spectronaut
1. Generate a spectral library from the provided FASTA.
2. Process raw files with DirectDIA or the standard Spectronaut DIA workflow.
3. Export a BGS Factory Report as `*_Report.tsv`.
4. Use `*_Report.setup.txt` for public submission.
5. Ensure your export includes precursor-level data with modified peptide sequence, charge, protein
   IDs, and intensity columns.
:::

:::{dropdown} FragPipe (DIA-NN quant)
1. Load the DIA_SpecLib_Quant workflow.
2. Import DIA raw files and assign experimental group information.
3. Generate or use a spectral library from the provided FASTA.
4. **Do not add contaminants when adding decoys to the database.**
5. Run the analysis and export the DIA-NN-style `*_report.tsv` (precursor-level quantification).
6. Upload `fragpipe.workflow` for public submission.

FragPipe reports protein identifiers across two columns ("Proteins" and "Mapped Proteins"); these
are concatenated to form the protein groups.
:::

:::{dropdown} PEAKS
1. Import DIA raw files into a new PEAKS project.
2. Configure sample grouping to match Condition A vs. Condition B.
3. Set up DIA quantification with appropriate parameters.
4. Use label-free quantification (LFQ) with Identification Directed Quantification (IDQ).
5. Export a text report (`.txt`) with precursor-level quantification.
6. Upload the settings `.txt` file for public submission.
:::

:::{dropdown} Custom format
If your tool isn't listed above, upload a tab-delimited table with:

| Column | Description |
|---|---|
| `Sequence` | Unmodified peptide sequence |
| `Modified sequence` | Sequence with localized modifications, [ProForma](https://www.psidev.info/proforma) format |
| `Proteins` | `;`-separated identifiers, must contain species flags (`_HUMAN`, `_YEAST`, `_ECOLI`) |
| `Charge` | Precursor charge state |
| `LFQ_Plasma_Condition_A_Sample_Alpha_01`…`06` | Intensity values, condition A replicates |
| `LFQ_Plasma_Condition_B_Sample_Alpha_01`…`06` | Intensity values, condition B replicates |

The table should contain only validated ions, with no contaminant sequences or non-specific
peptides.
:::

## Parameters tracked for public submission

To submit publicly: upload your quantification output, the matching parameter/log file(s), fill in
optional comments, confirm the metadata, and submit. A GitHub pull request is generated
automatically for tracking and community review.

Contaminants are expected flagged `Cont_`; species annotation in protein identifiers must support
`_HUMAN`, `_YEAST`, and `_ECOLI` mapping.

Once submitted you'll get a pull-request link; save it to track your submission (see
[what happens next](../../your-first-submission/index.md#6-submit-for-public-review)).
[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues/new) with any problems.
