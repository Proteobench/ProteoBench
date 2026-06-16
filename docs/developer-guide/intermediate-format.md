# Intermediate format specification

This document specifies the internal tabular formats that ProteoBench produces
while processing a benchmark submission. These formats are for the internal use of:
scoring, plotting, datapoint generation, the submission-validation layer, and the
`intermediate_hash` that identifies a dataset all depend on the column names,
types, and semantics defined here. It is important to note that the intermediate format
is specific for a module. Even though models can share intermediate formats where
applicable. If there is any explanation on this page that is module specific, this
is purely for illustrative purposes.

```{note}
Status: descriptive specification of the current behaviour (format version 1,
implicit). It documents what the code produces today. Proposed changes (an
explicit version field, a canonical serialisation for hashing) are described in
the "Reproducibility and the intermediate hash" and "Versioning" sections below.
```

## Scope

There are two distinct tables:

| Artifact | Produced by | Persisted | Consumed by |
|----------|-------------|-----------|-------------|
| **Standard format** (pre-scoring) | `ParseSettingsQuant.convert_to_standard_format()` | No (in-memory) | Scoring; the submission-validation layer |
| **Intermediate format** (post-scoring) | `QuantScoresHYE.generate_intermediate()` | Yes, as `result_performance.csv` in the dataset archive; also hashed into `intermediate_hash` | Plotting, datapoint metrics, the "View Single Result" table |

The intermediate format is the primary subject of this specification. The
standard format is documented as the declared input format that any module or
tool parser must produce.

## Standard format

Produced by `convert_to_standard_format()` in
`proteobench/io/parsing/parse_settings.py`. It is a long table with one row per
(e.g., precursor, run for the precursor quantification module): a precursor 
that was quantified in six runs yields six rows. The table is not projected to a fixed column set, so unmapped input columns may
also be present; only the columns below are relied upon downstream (this is quite specific
for quantification modules; may differ for other modules!).

| Column | Type | Required | Meaning |
|--------|------|----------|---------|
| `Proteins` | str | yes | Protein or protein-group identifier(s). Multiple proteins may be joined by `;` or `,`; UniProt-style identifiers are split on the pipe character into database, accession, and entry name. |
| `Sequence` | str | yes | Plain (unmodified) peptide sequence. |
| `Charge` | int | yes | Precursor charge. |
| `proforma` | str | conditional | [ProForma](https://github.com/HUPO-PSI/ProForma)-encoded modified sequence. Present only when the tool TOML defines a `[modifications_parser]`. |
| `precursor ion` | str | conditional | `proforma + "/" + Charge`. Present when `level = "ion"`. |
| `peptidoform` | str | conditional | Equal to `proforma`. Present when `level = "peptidoform"`. |
| `Raw file` | str | yes | Cleaned run name (extensions and known suffixes stripped by `_clean_run_name()`). |
| `Intensity` | float | yes | Quantitative intensity for the (precursor, run). Rows with `Intensity <= 0` are removed. |
| `replicate` | str | yes | Condition label, `"A"` or `"B"`, mapped from `Raw file` via the tool's `condition_mapper`. |
| `contaminant` | bool | yes | Result of matching `Proteins` against the contaminant flag. Contaminant rows are removed, so survivors are all `False`. |
| species flags | bool | yes | One boolean column per species in the module `species_mapper` (for HYE: `HUMAN`, `YEAST`, `ECOLI`), set by substring match on `Proteins`. |
| `MULTI_SPEC` | bool | yes | `True` when the precursor matches more than `min_count_multispec` species. Multi-species rows are removed. |
| run dummy columns | bool | yes | One boolean column per distinct `Raw file` (from `pd.get_dummies`). |

## Intermediate format

The intermediate format is the table defined for calculating all metrics in a given module. It should contain
every value needed for metric calculation in a standardized fashion. It is not limited to 
these columns, it can contain more columns, even ones that are tool specific. However, it at
least needs defined (i.e., description of columns) and "normalized" (i.e., values should be comparable between submissions) columns for metric calculation.

An example for quantificaiton modules; produced by `QuantScoresHYE.generate_intermediate()` in
`proteobench/score/quantscoresHYE.py`. One row per precursor (or peptidoform).
Only **single-species** precursors are retained: `compute_epsilon()` keeps rows
where exactly one species flag is set (`unique == 1`), so multi-species
precursors do not appear.

### Column catalog

| Column | Type | Meaning |
|--------|------|---------|
| `precursor ion` or `peptidoform` | str | Precursor key. Name depends on the module `level`. For ion modules this is `proforma + "/" + charge`. |
| `Intensity_mean_A`, `Intensity_mean_B` | float | Mean linear intensity across the runs of condition A / B. |
| `Intensity_std_A`, `Intensity_std_B` | float | Standard deviation of linear intensity per condition. |
| `log_Intensity_mean_A`, `log_Intensity_mean_B` | float | Mean of the log2 intensities per condition. |
| `log_Intensity_std_A`, `log_Intensity_std_B` | float | Standard deviation of log2 intensities per condition. |
| `CV_A`, `CV_B` | float | Coefficient of variation per condition, `Intensity_std / Intensity_mean`. |
| `log2_A_vs_B` | float | `log_Intensity_mean_A - log_Intensity_mean_B`. The observed log2 fold change. |
| per-run intensity columns | float | One column per distinct run name (cleaned `Raw file`), holding that run's intensity for the quantified feature. The set of columns therefore depends on the experimental design. |
| `nr_observed` | int | Number of runs in which the feature (i.e. precursor, peptidoform) was quantified. |
| species flags | bool | One boolean per species (HYE: `YEAST`, `ECOLI`, `HUMAN`). For a retained row exactly one is `True`. |
| `unique` | int | Sum of the species flags. Always `1` in the persisted table. |
| `species` | str | The single species name for the precursor. |
| `log2_expectedRatio` | float | `log2` of the module's expected A-vs-B ratio for `species`. |
| `epsilon` | float | Accuracy: `log2_A_vs_B - log2_expectedRatio`. Deviation from the known ratio. |
| `log2_empirical_median`, `log2_empirical_mean` | float | Per-species empirical centre of `log2_A_vs_B` (median / mean over the species). |
| `epsilon_precision_median`, `epsilon_precision_mean` | float | Precision: `log2_A_vs_B - log2_empirical_{median,mean}`. Deviation from the empirical centre. |

### Notes on semantics

- All logarithms are base 2.
- `epsilon` requires ground truth (the expected ratio) and measures accuracy;
  `epsilon_precision_*` requires no ground truth and measures reproducibility.
- The per-run intensity columns are not a fixed part of the schema: their names
  and number follow the run names of the submitted experiment.

## Reproducibility and the intermediate hash

The dataset identity is `intermediate_hash`, computed in
`proteobench/datapoint/quant_datapoint.py` as the SHA1 of the intermediate
DataFrame rendered with `pandas.DataFrame.to_string()`.

Because the hash is taken over the rendered text, it depends on:

- the set of columns and their **order**;
- the **row order**;
- the floating-point formatting used by `to_string()`;
- the run-specific intensity column names.

Any change to the scoring code, the column order, or the pandas rendering can
change the hash for identical inputs. Implementers must therefore treat the
column order and row order as part of the format.

## Module variants

- **HYE (Human-Yeast-Ecoli)**: the format described above. Species set
  `HUMAN`, `YEAST`, `ECOLI`.
- **PYE (Plasma, `quant_lfq_DIA_ion_plasma`)**: `QuantScoresPYE.generate_intermediate()`
  is currently a pass-through over the HYE implementation, so the intermediate
  columns are the same. The plasma-specific quantities (spike-in fold-change
  error, dynamic range, human-plasma epsilon) are computed later, in
  `QuantDatapointPYE`, not in the intermediate table. The plasma datapoint also
  uses `max_nr_observed = 12` instead of 6.
- **De novo (`denovo_DDA_HCD`)**: a different schema entirely, produced by
  columns above. This modules is still in development, the full documentation of its intermediate format will be provided soon.
  and carries match-type and amino-acid-level columns (for example `match_type`,
  `aa_matches_dn`/`aa_matches_gt`, `pep_match`) rather than the quantitative
  columns above. A detailed catalogue for the de novo intermediate is out of
  scope for this revision and should be added alongside the de novo module's
  maturation.

## Persistence and external resources

The intermediate format table is written to `result_performance.csv` inside the dataset
archive on the public datasets server
(`https://proteobench.cubimed.rub.de/datasets/`), keyed by `intermediate_hash`.
It is reloaded for the "View Single Result" tab and for regenerating plots.

## Reference example

`test/data/intermediate_files/result_performance_MaxQuant_20241216_120952.csv`
is a committed sample of the (version-1, pre-precision) intermediate for a
MaxQuant DDA submission.

## Non-goals

- This specification does not define the per-tool native output formats; those
  are handled by the format-specific loaders in `io/parsing/parse_ion.py`.
- It does not define the datapoint JSON stored in the results repositories; that
  is a separate structure built by the `QuantDatapoint*` classes.