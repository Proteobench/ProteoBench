# De novo sequencing (DDA-HCD)

{bdg-success}`alpha` {bdg-primary-line}`Identification` — DDA, HCD fragmentation, peptide/amino-acid level

Compares the peptide-sequencing accuracy of *de novo* sequencing models and algorithms on
data-dependent acquisition (DDA) data acquired with HCD fragmentation on Orbitrap instruments.

```{admonition} Training data can bias results
:class: warning
Deep-learning models can be trained (and thus overfit) on the benchmark data used here, which
biases the comparison. If you retrained any compatible model, describe the training data and
procedure in the `Comments for submission` field before uploading.
```

## At a glance

| | |
|---|---|
| Acquisition | DDA, HCD |
| Instrument | Orbitrap (various; nine-species dataset) |
| Level | Peptide and amino acid |
| Metric | Precision / recall (peptide and amino-acid level) |

## What this module tests

This module can be used to evaluate the impact of:

- post-translational modifications (PTMs)
- missing fragments
- peptide length
- noise relative to precursor-ion signal
- species-specific sequence biases

It also shows which tools outperform others in specific scenarios, and lets the effect of
post-processing *de novo* results be investigated side by side with the original results (if
uploaded separately, with the post-processing method described in the submission metadata).

## Dataset

The widely used "balanced" nine-species dataset from
[Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2) (first used in
[Li et al., 2017](https://pubmed.ncbi.nlm.nih.gov/28720701/)): nine species searched with
Tide-Percolator, PSMs filtered at 1% PSM-level FDR, peptides shared between species removed, and
downsampled to 779,879 PSMs total.

**Table: benchmark dataset statistics**

| PRIDE | Species | Instrument | Spectra | PSMs |
|---|---|---|---|---|
| [PXD005025](https://www.ebi.ac.uk/pride/archive/projects/PXD005025) | *Vigna Mungo* | QExactive | 932,848 | 102,255 |
| [PXD004948](https://www.ebi.ac.uk/pride/archive/projects/PXD004948) | *Mus musculus* | LTQ-Orbitrap Velos | 306,786 | 25,522 |
| [PXD004325](https://www.ebi.ac.uk/pride/archive/projects/PXD004325) | *Methanosarcina mazei* | QExative Plus | 3,728,183 | 100,485 |
| [PXD004565](https://www.ebi.ac.uk/pride/archive/projects/PXD004565) | *Bacillus subtilis* | QExactive | 4,336,428 | 113,234 |
| [PXD004536](https://www.ebi.ac.uk/pride/archive/projects/PXD004536) | *Candidatus endoloripes* | Q Exactive Plus Hybrid | 2,272,023 | 82,514 |
| [PXD004947](https://www.ebi.ac.uk/pride/archive/projects/PXD004947) | *Solanum lycopersicum* | QExactive | 603,506 | 100,056 |
| [PXD003868](https://www.ebi.ac.uk/pride/archive/projects/PXD003868) | *Saccharomyces cervisiae* | Q-Exactive Plus | 1,477,397 | 108,973 |
| [PXD004467](https://www.ebi.ac.uk/pride/archive/projects/PXD004467) | *Apis mellifera* | QExactive | 823,169 | 102,285 |
| [PXD004424](https://www.ebi.ac.uk/pride/archive/projects/PXD004424) | *Homo sapiens* | QExactive | 684,821 | 44,555 |
| **Total** | | | **15,165,161** | **779,879** |

The benchmark was built from `nine-species-balanced.zip` on
[Zenodo](https://zenodo.org/records/13685813) (one MGF per species, combined here with reannotated
spectrum identifiers to prevent duplicates).

**Download:** the parsed and combined dataset from the
[ProteoBench server](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/).

## How the metric is calculated

Performance is evaluated at both the amino-acid and peptide level. As introduced by
[DeepNovo](https://www.pnas.org/doi/10.1073/pnas.1705691114), a correct amino acid is one whose mass
differs by less than 0.1 Da from the ground-truth amino acid, and whose predicted prefix or suffix
differs by no more than 0.5 Da in mass from the ground-truth peptide. A peptide is correct only if
every amino-acid prediction meets these criteria. This mode is called **mass-based**. A stricter
**exact** mode instead requires the two sequences to be identical (deamidated Q/E count as
incorrect; only Ile/Leu substitutions are allowed).

### Main benchmarking plot

Each point is one *de novo* tool, plotting a **peptide-level metric** (x-axis: precision or recall,
depending on the selected setting) against the corresponding **amino-acid-level metric** (y-axis).

- **Precision** = correct predictions ÷ predictions above threshold — emphasizes reliability of
  reported identifications.
- **Recall** = correct predictions ÷ total spectra — emphasizes dataset coverage.

The **evaluation mode** (exact vs. mass-based) determines how "correct" is defined, as above.
Mass-based matching finds the longest mass-matching prefix/suffix between predicted and reference
sequences, using a cumulative mass threshold (50 ppm) and an individual amino-acid mass threshold
(20 ppm).

### In-depth plots

**PTMs.** Precision for each supported PTM (Table below), both as an overview across all
modifications and per-modification plots contrasting precision computed over ground-truth-containing
peptides vs. over predicted-containing peptides (to catch over-prediction bias).

**Table: PTMs in the ground-truth dataset**

| PTM | Occurrences | Fixed |
|---|---|---|
| Carbamidomethylation (C) | 118,133 | True |
| Methionine Oxidation | 62,815 | False |
| N-terminal Acetylation | 11,373 | False |
| N-terminal Carbamylation | 19,993 | False |
| N-terminal ammonia-loss | 18,352 | False |
| Asparagine deamidation | 59,437 | False |
| Glutamine deamidation | 25,212 | False |

**Spectrum characteristics.** Peptide-level precision subset by: missing fragmentation sites
(number of missing complementary b/y ion pairs), peptide length, and % explained intensity
(annotated-peak intensity ÷ TIC, an inverse noise proxy).

**Species.** Precision computed per species separately, to explore species-specific sequence
biases (particularly relevant for deep-learning models). This was originally a train/test split
design (train on eight species, evaluate on the held-out one); ProteoBench does not train models,
so if you want to use this feature as intended, generate predictions accordingly and concatenate
them into one ProteoBench-compatible result file.

## Run your workflow

The module is flexible about which workflow you run, but supporting the PTMs in the table above
gives the fairest comparison. Then follow
[Your First Submission](../../your-first-submission/index.md) to upload, inspect, and submit
your results.

## Tool-specific setup

**Table: input files required for metric calculation and public submission**

| Tool | Input file | Parameter file |
|---|---|---|
| AdaNovo | `*.mzTab` | `*.yaml` |
| Casanovo | `*.mztab` | `*.yaml` |
| ContraNovo | `*.mztab` | `*.yaml` |
| DeepNovo | `*.tab` | — |
| InstaNovo | `*.csv` | `*.yaml` |
| NovoB | `*.csv` | — |
| PepNet | `*.tsv` | — |
| Pi-HelixNovo | `*.tsv` | `*.yaml` |
| Pi-PrimeNovo | `*.tsv` | `*.yaml` |
| PointNovo | `*.csv` | — |
| SMSNet | results + results_prob (2 files) | — |

PepNet, DeepNovo, PointNovo, NovoB, and SMSNet don't have an easily parsable configuration file, so
no parameter file is required for them; fill in the `Comments for submission` field as completely
as possible instead.

Expand a tool below for setup details. All tools use the same
[ground-truth MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/) — do not rename the
file or the spectrum identifiers.

:::{dropdown} AdaNovo
Set up [AdaNovo](https://github.com/Westlake-OmicsAI/adanovo_v1) and run it on the ground-truth
MGF. Upload `results.mztab` for scoring and `config.yaml` for public submission.

From `results.mztab`, ProteoBench reads `spectra_ref` (spectrum ID, from `index=<number>`),
`sequence` (prediction), `search_engine_score[1]` (peptide score), and
`opt_ms_run[1]_aa_scores` (amino-acid scores).
:::

:::{dropdown} Casanovo
Set up [Casanovo](https://casanovo.readthedocs.io/en/latest/) and run it on the ground-truth MGF.
Upload `results.mztab` for scoring and `config.yaml` for public submission.

From `results.mztab`, ProteoBench reads `spectra_ref` (spectrum ID, from `index=<number>`),
`sequence`, `search_engine_score[1]`, and `opt_ms_run[1]_aa_scores`.
:::

:::{dropdown} ContraNovo
Set up [ContraNovo](https://github.com/BEAM-Labs/ContraNovo) and run it on the ground-truth MGF.
Upload `results.mztab` for scoring and `config.yaml` for public submission.

From `results.mztab`, ProteoBench reads `spectra_ref` (spectrum ID, from `scan=<number>`),
`sequence`, `search_engine_score[1]`, and `opt_ms_run[1]_aa_scores`.
:::

:::{dropdown} DeepNovo
Best run through [this pipeline](https://github.com/denisbeslic/denovopipeline) on the ground-truth
MGF. Upload the output `.tab` file; no parameter file is required.

From the `.tab` file, ProteoBench reads `scan` (spectrum ID), `output_seq` (prediction),
`output_score`, and `aa_score` (precision-recall curve support for the latter two is not yet
implemented). DeepNovo's special tokens for modified residues (`Cmod`, `Mmod`, `Nmod`, `Qmod`) are
converted to ProForma automatically.
:::

:::{dropdown} InstaNovo
Set up [InstaNovo](https://instanovo.ai/) and run it on the ground-truth MGF. Upload `results.csv`
for scoring and `config.yaml` for public submission.

From `results.csv`, ProteoBench reads `spectrum_id` (trailing number after the last colon, e.g.
`filename:1234` → `1234`), `predictions`, `log_probs`, and `token_log_probs` (precision-recall curve
support not yet implemented).
:::

:::{dropdown} NovoB
Set up [NovoB](https://github.com/ProteomeTeam/NovoB) and run it on the ground-truth MGF. Upload the
output CSV; no parameter file is required.

ProteoBench reads `spectrum_id` (first integer in the identifier string), `sequence`, and `score`.
NovoB treats all cysteines as carbamidomethylated and uses lowercase letters for variable
modifications (`m`, `n`, `q`, `s`, `t`, `y`), converted to ProForma automatically. NovoB does not
provide amino-acid-level scores.
:::

:::{dropdown} PepNet
Set up [PepNet](https://github.com/lkytal/PepNet) and run it on the ground-truth MGF, or use the
[web interface](https://denovo.predfull.com/) directly. Upload `results.tsv`; no parameter file is
required.

ProteoBench reads `TITLE` (spectrum ID, from `scan=<number>`), `DENOVO` (prediction), `Score`, and
`Positional Score` (precision-recall curve support not yet implemented).
:::

:::{dropdown} π-HelixNovo
Set up [π-HelixNovo](https://github.com/PHOENIXcenter/pi-HelixNovo/tree/pi-HelixNovo) and run it on
the ground-truth MGF. Upload `results.tsv` for scoring and `config.yaml` for public submission.

Columns `0` (spectrum ID, from `scan=<number>`), `1` (prediction), and `2` (score) are read;
positional scores are set equal to the amino-acid scores.
:::

:::{dropdown} π-PrimeNovo
Set up [π-PrimeNovo](https://github.com/PHOENIXcenter/pi-PrimeNovo) and run it on the ground-truth
MGF. Upload `results.tsv` for scoring and `config.yaml` for public submission.

ProteoBench reads `label` (spectrum ID, from `scan=<number>`), `prediction`, and `score`; positional
scores are set equal to the amino-acid scores.
:::

:::{dropdown} PointNovo
Best run through [this pipeline](https://github.com/denisbeslic/denovopipeline) on the ground-truth
MGF. Upload the output file (typically named with a `.pointnovo_output`-style extension); no
parameter file is required.

ProteoBench reads `feature_id` (spectrum ID), `predicted_sequence`, `predicted_score`, and
`predicted_position_score` (precision-recall curve support not yet implemented). PointNovo's
spelled-out modification names (e.g. `C(Carbamidomethylation)`) are converted to ProForma
automatically.
:::

:::{dropdown} SMSNet
Best run through [this pipeline](https://github.com/denisbeslic/denovopipeline) on the ground-truth
MGF. Upload **two** output files (`results` and `results_prob`); no parameter file is required.

ProteoBench reads `index` (spectrum ID), `sequence`, `peptide_score`, and `aa_scores`
(precision-recall curve support not yet implemented). SMSNet uses the same lowercase-modification
convention as NovoB, converted to ProForma automatically.
:::

:::{dropdown} Custom format
If your tool isn't listed above, submit a plain CSV/TSV with:

| Column | Required | Description |
|---|---|---|
| `spectrum_id` | Yes | Must contain `scan=<number>` or be a plain integer scan number |
| `sequence` | Yes | Predicted sequence; ProForma or mass-offset brackets (e.g. `C[+57.021]`) |
| `score` | Yes | Per-prediction confidence score |
| `aa_scores` | No | Per-amino-acid scores; defaults to the peptide score per position if omitted |

Spectrum identifiers must match the scan numbers in the ProteoBench ground-truth dataset. No
parameter file is supported; describe your tool and settings in `Comments for submission`.
:::

### How to run these models more easily

**Table: public model execution pipelines**

| Pipeline | Workflow manager | Supported tools |
|---|---|---|
| [denisbeslic/denovopipeline](https://github.com/denisbeslic/denovopipeline) | Python | DeepNovo, PointNovo, SMSNet, Casanovo (newer models may be incompatible) |
| [SamvPy/DeNovo_Benchmark](https://github.com/SamvPy/DeNovo_Benchmark) | Nextflow + Python | AdaNovo, Casanovo, ContraNovo, InstaNovo, NovoB, PepNet, π-HelixNovo, π-PrimeNovo, InstaNovo+, Spectralis |
| [bittremieuxlab/denovo_benchmarks](https://github.com/bittremieuxlab/denovo_benchmarks) | Apptainer | AdaNovo, Casanovo, ContraNovo, DePS, PEAKS, biatNovo-DDA, DeepNovo, GCNovo, InstaNovo, Novor, PepNet, π-HelixNovo, π-PrimeNovo, SMSNet, Spectralis |

Output from some of these pipelines may need reformatting; see the "Custom format" dropdown above
if you run into trouble.

### How ProteoBench maps each tool's columns

Each tool's output format is described in a `.toml` file under
`proteobench/io/parsing/io_parse_settings/`, with sections `[mapper]` (`spectrum_id`, `sequence`,
`score`, optional `aa_scores`), `[spectrum_id_mapper]` (regex to extract the spectrum ID),
`[sequence_mapper.replacement_dict]` (modification renaming for uniform parsing), and
`[modifications_parser]` (`parse_column`, `before_aa`, `isalpha`, `isupper`, `pattern`,
`modification_dict`), analogous to the quant modules' modification parsing.

## Result columns

The results table is built by left-joining predictions onto the ground truth: every ground-truth
spectrum is retained, with `NaN` prediction columns where the tool made no call.

**Identification**: `spectrum_id`, `proforma` (prediction), `peptidoform_ground_truth`, `score`,
`aa_scores`, `title`, `precursor_mz`, `retention_time`, `collection` (species/dataset).

**Match evaluation**: `match_type` (`exact` / `mass` / `mismatch`), `pep_match`, `aa_matches_gt`,
`aa_matches_dn`, `aa_exact_gt`, `aa_exact_dn` (booleans indexed to ground-truth or predicted sequence
length).

**Spectrum characteristics** (precomputed): `peptide_length`, `missing_frag_sites`,
`missing_frag_pct`, `explained_y_pct`, `explained_b_pct`, `explained_by_pct`, `explained_all_pct`,
`cos`, `cos_ionb`, `cos_iony`, `spec_pearson`, `dotprod`.

**PTM flags** (ground truth and, suffixed ` (denovo)`, prediction): Methionine oxidation, Glutamine
deamidation, Asparagine deamidation, N-terminal acetylation, N-terminal carbamylation, N-terminal
ammonia-loss.

## Parameters tracked for public submission

Upload your parameter file under "Download calculated metrics"; see
[Tool-specific setup](#tool-specific-setup) above for which file that is per tool.

| Parameter | Description |
|---|---|
| Software name / version | *De novo* tool and version |
| Model checkpoint identifier | Filename, tag, or URL of the model weights used |
| Number of beams | Beam-search width |
| Peaks considered per spectrum | Maximum retained before prediction |
| Precursor mass tolerance | Including unit (e.g. `10 ppm` or `0.02 Da`) |
| Min/max peptide length | |
| Min/max fragment m/z | |
| Min/max intensity threshold | |
| Tokens | Vocabulary of amino acids and modifications the model can predict |
| Min/max precursor charge | |
| Remove precursor peaks | Whether precursor peaks are stripped before prediction |
| Isotope error range | Allowed range during precursor matching |
| Decoding strategy | e.g. beam search, greedy |

If a parameter isn't in your file, add it in `Comments for submission`.

Once submitted you'll get a pull-request link; save it to track your submission (see
[what happens next](../../your-first-submission/index.md#6-submit-for-public-review)).
[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues/new) with any problems.
