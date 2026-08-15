# De novo sequencing (DDA-HCD)

{bdg-success}`alpha` {bdg-primary-line}`Identification` — DDA, HCD fragmentation, peptide/amino-acid level

```{admonition} This module is in alpha stage
:class: warning
This module is still in active development. Its scope, metrics, or dataset may change as we refine
it based on community feedback. Submissions are welcome, but please be aware that comparisons may
shift in future versions.
```

Compares the peptide-sequencing accuracy of *de novo* sequencing models and algorithms on
data-dependent acquisition (DDA) data acquired with HCD fragmentation on Orbitrap instruments.

```{admonition} Training data can bias results
:class: warning
Deep-learning models can be trained (and thus overfit) on the benchmark data used here, which
biases the comparison. If you retrained any compatible model, describe the training data and
procedure in the `Comments for submission` field before uploading.
```

```{button-link} https://proteobench.cubimed.rub.de/denovo_DDA_HCD
:color: primary
:class: sd-px-4

Open in web app
```

## At a glance

| | |
|---|---|
| Acquisition | DDA, HCD |
| Instrument | Orbitrap (various; nine-species dataset) |
| Level | Peptide and amino acid |
| Metric | Precision / coverage (peptide and amino-acid level) |

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

The performance is evaluated at both the amino acid and peptide level. As introduced by [DeepNovo](https://www.pnas.org/doi/10.1073/pnas.1705691114), a correct amino acid whose mass differs by less than 0.1 Da from the corresponding ground truth amino acid. Additionally, this predicted amino acid must have either a prefix or suffix that differs by no more than 0.5 Da in mass from the corresponding amino acid sequence in the ground truth peptide. Correct peptides are defined as sequences where all amino acid predictions meet these criteria, ensuring that only fully accurate predictions are considered correct at the peptide level. In the module, this mode of evaluation is called '**mass-based**', where the tolerances for the particular token and prefix/suffix are set at 20 and 50 ppm respectively. However, a more strict evaluation mode can be selected and is termed '**exact mode**'. In this mode, the two sequences should be exactly the same. However, you can specify to allow mistakes made between isoleucine-leucine and deamidated-DE - NQ.

### Main benchmarking plot

The main accuracy plot provides a **global overview of de novo sequencing performance** across the evaluated tools. It visualizes the relationship between **peptide-level identification performance** and **amino-acid level sequence accuracy**. Each point in the plot corresponds to a de novo sequencing tool and shows the amino acid and peptide level accuracy. The plot combines two levels of evaluation:

**X-axis – Peptide-level metric**
The x-axis displays either peptide-level **precision** or **AUC**, depending on the selected setting.

**Y-axis – Amino-acid level metric**
The y-axis always shows the corresponding **amino-acid level metric**, measuring how accurately the individual residues in the predicted sequences match the ground truth.

This design allows the plot to simultaneously capture both **identification reliability** and **sequence-level correctness**.

The **Precision vs AUC** setting determines which peptide-level metric is shown on the x-axis.
Precision measures how many reported peptide predictions are correct:

    Precision = correct predictions ÷ predictions above threshold

This view emphasizes the **reliability of reported identifications**. Tools that achieve high precision produce predictions that are more likely to be correct.

AUC is the **area under the precision-coverage curve**. This curve is constructed by ranking a tool's predictions by their reported confidence score and, at each score threshold, computing:

    Coverage = (correct + incorrect) ÷ total spectra
    Precision = correct ÷ (correct + incorrect)

As the threshold is relaxed from the highest-confidence prediction to the lowest, coverage increases monotonically from 0 to 1, while precision typically decreases as lower-confidence predictions are included. AUC condenses this trade-off into a single value between 0 and 1: a tool that keeps precision high even as coverage approaches 1 will have an AUC close to 1, while a tool whose precision drops sharply as more predictions are included will have a lower AUC.

This view emphasizes **overall sequencing performance across the full range of a tool's confidence in its predictions**, rather than reliability at a single, fixed threshold.

The **evaluation mode** determines how predictions are classified as correct.

In **exact** evaluation mode, a prediction is considered correct only if the predicted peptide sequence **exactly matches the ground-truth sequence**, including both amino acids and modifications. This represents the **strictest accuracy definition**. This exact matching can be relaxed by allowing 2 specific ambiguities: Isoleucine-leucine ambiguity and deamidated-DE - NQ ambiguity. In **mass-based** evaluation mode, predictions are considered correct when they match the ground-truth sequence based on **cumulative fragment masses**, even if the exact amino-acid sequence differs.
The algorithm identifies the longest **mass-matching prefix and suffix** between the predicted and reference peptide sequences. Two mass tolerances are used during this process:

- **Cumulative mass threshold** – maximum allowed difference between cumulative fragment masses (50 ppm)
- **Individual mass threshold** – maximum allowed difference between individual amino-acid masses (20 ppm)

This evaluation accounts for typical ambiguities in mass spectrometry data. Match-based evaluation therefore counts both **exact matches and mass-equivalent matches**, while exact evaluation only counts **perfect sequence matches** (while optionally allowing two specific commonly occuring ambiguities).


#### Precision-coverage curves

The main benchmarking view described above plots a single, threshold-independent summary per tool: precision (at every reported prediction) or AUC (integrated across every possible threshold). A second view, selectable via a **Scatter / Precision-Coverage Curves** tab switcher above the plot, shows the full curve that the AUC value is derived from, so you can inspect *how* a tool's precision degrades as more of its lower-confidence predictions are included, rather than only its integrated summary.

This view shows two side-by-side plots — peptide-level and amino-acid level — with one line per tool. Each curve is built by ranking a tool's predictions by their reported confidence score (from highest to lowest) and, after including each successive prediction, recomputing:

    Coverage = number of predictions included ÷ total number of spectra
    Precision = correct predictions included ÷ total predictions included

Predictions that tie on score cannot be meaningfully split by any threshold — either all of a tied group clears it or none does — so the curve has one point per *distinct* score value rather than one point per prediction. AUC (average precision) is always computed by integrating this full-resolution curve, before any further reduction described below, so the reported AUC value is unaffected by how the curve is displayed.

Since the ground-truth dataset contains hundreds of thousands of spectra, storing every curve point for every tool would not scale as more tools are compared side by side. The stored/plotted curve is therefore capped at 500 points, sampled at evenly-spaced values along the coverage axis (not evenly-spaced by row index, since tied-score groups can otherwise leave the curve very unevenly spaced) — this only affects the resolution of the displayed line, never the AUC metric itself.

Both this view and the main scatter plot respond to the same **evaluation mode** (exact/mass-based) and ambiguity toggle selections. As with the main plot, datapoints submitted before this curve was stored are silently hidden from this view.

### In-depth plots

The in-depth section provides a more detailed picture of the (relative) performance of the *de novo* tools.


#### PTMs

Firstly, the ability of the tool to accurately predict several **PTM's** can be evaluated. Since the ground-truth dataset was generated by searching against specific modifications, only these are supported. In Table 2, an overview of supported PTMs and their statistics are stated. Two types of plots are created for this: (i) an overview plot and (ii) PTM-specific plots. In the overview plot, the precision across all modifications are plotted together where precision is defined as the proportion of correctly predicted modifications over all peptides containing this modification in the ground-truth. A correct prediction does not require a fully correctly predicted peptide, only the specific amino acid with its PTM at the correct position. In the PTM-specific plots, this precision is plotted against the precision calculated as the proportion over all peptides containing this modification in the predicted peptide list. By doing so, biased precision estimates are handled in cases when the *de novo* tool would predict PTMs abundantly yet erroneously.

**Table 2. PTMs in the ground-truth dataset**

| PTM                      | Occurrences | Fixed |
| ------------------------ | ----------- | ----- |
| Carbamidomethylation (C) | 118,133     | True  |
| Methionine Oxidation     | 62,815      | False |
| N-terminal Acetylation   | 11,373      | False |
| N-terminal Carbamylation | 19,993      | False |
| N-terminal ammonia-loss  | 18,352      | False |
| Asparagine deamidation   | 59,437      | False |
| Glutamine deamidation    | 25,212      | False |


#### Spectrum characteristics

Secondly, the ability of the tool to correctly predict spectra with specific characteristics can be evaluated. As shown in previous benchmark publications ([Denis et al](https://doi.org/10.1093/bib/bbac542), [Muth et al](https://doi.org/10.1093/bib/bbx033), [McDonnel et al](https://doi.org/10.1016/j.csbj.2022.03.008), [van Puyenbroeck et al](https://www.biorxiv.org/content/10.1101/2025.08.19.671052v1)), the accuracy of any *de novo* tool is dependent on several spectrum properties. To show this effect, we calculate precision on a selection of PSMs subsetted by each of the following characteristics:

- Missing fragmentation sites: The number of missing complementary (b and y) ions
- Peptide length: Not specifically a spectrum characteristic, but reported to impact the performance of *de novo* tools
- Percentage Explained intensity: Serves as an inverse of the noise. Defined as the proportion of the intensity of annotated peaks over all peaks (TIC)

The precision is calculated on the peptide level as the proportion of correct peptides among the predictions made by the *de novo* tool

#### Species

Protein sequences can differ considerably between species. Therefore, particularly for deep learning methods, models trained on data from one species might not be directly applicable to predict peptide sequences from other species. To roughly explore these differences, precision is calculated as above for each species separately.

Beware, this set up was meant to work as training-test split procedure, where the data of eight species was used to train a model and evaluated on the unseen spectra from the excluded species. Here, we do not use it as intented since training the models is not directly supported in ProteoBench. If the user wants to use this feature as intented, the predictions should be generated accordingly as described. The results should be concatenated into a single result file in the format compatible with ProteoBench (see below).

#### In-FASTA evaluation

A wrong prediction is not necessarily a meaningless one: the predicted sequence might still be a real peptide, just the wrong one for that particular spectrum. To capture this, every prediction is placed into one of three categories:

- **Correct** – the prediction matches the ground-truth peptide exactly (allowing isoleucine/leucine ambiguity, since the two cannot be distinguished by mass).
- **In FASTA** – the prediction does not match the ground truth, but the predicted sequence is nonetheless found elsewhere in the reference proteome of the species the spectrum originates from.
- **Not in FASTA** – the prediction matches neither the ground-truth peptide nor any other protein in that species' proteome. Spectra for which the tool made no prediction at all also fall into this category.

Only predictions of at least 8 amino acids are checked against the proteome; below this length, a match can easily occur by chance and would not be a meaningful signal. Note that this categorization always uses the I/L-ambiguity exact match to determine "correct", independently of the **evaluation mode** and ambiguity toggles selected for the main benchmarking plot.

For each tool, the proportion of predictions in each category is shown as a stacked bar. A large **In FASTA** share indicates that, even where a tool's prediction is wrong, it is often still calling a genuinely existing peptide from the correct organism — suggestive of a real but different peptide (e.g. from a co-eluting or chimeric spectrum) rather than a sequencing error. A large **Not in FASTA** share instead points to predictions that are not just wrong, but not proteome-supported either.

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
| SMSNet | `results + results_prob (2 files)` | — |

PepNet, DeepNovo, PointNovo, NovoB, and SMSNet don't have an easily parsable configuration file, so
no parameter file is required for them; fill in the `Comments for submission` field as completely
as possible instead.

Expand a tool below for setup details. All tools use the same
[ground-truth MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/) — do not rename the
file or the spectrum identifiers.

:::{dropdown} AdaNovo
Set up [AdaNovo](https://github.com/Westlake-OmicsAI/adanovo_v1) and run it on the ground-truth
MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload `results.mztab` for scoring and `config.yaml` for public submission.

From `results.mztab`, ProteoBench reads `spectra_ref` (spectrum ID, from `index=<number>`),
`sequence` (prediction), `search_engine_score[1]` (peptide score), and
`opt_ms_run[1]_aa_scores` (amino-acid scores).
:::

:::{dropdown} Casanovo
Set up [Casanovo](https://casanovo.readthedocs.io/en/latest/) and run it on the ground-truth MGF. **Be sure not to change the file name or the spectrum identifiers**.
Upload `results.mztab` for scoring and `config.yaml` for public submission.

From `results.mztab`, ProteoBench reads `spectra_ref` (spectrum ID, from `index=<number>`),
`sequence`, `search_engine_score[1]`, and `opt_ms_run[1]_aa_scores`.
:::

:::{dropdown} ContraNovo
Set up [ContraNovo](https://github.com/BEAM-Labs/ContraNovo) and run it on the ground-truth MGF. **Be sure not to change the file name or the spectrum identifiers**.
Upload `results.mztab` for scoring and `config.yaml` for public submission.

From `results.mztab`, ProteoBench reads `spectra_ref` (spectrum ID, from `scan=<number>`),
`sequence`, `search_engine_score[1]`, and `opt_ms_run[1]_aa_scores`.
:::

:::{dropdown} DeepNovo
Best run through [this pipeline](https://github.com/denisbeslic/denovopipeline) on the ground-truth
MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload the output `.tab` file; no parameter file is required.

From the `.tab` file, ProteoBench reads `scan` (spectrum ID), `output_seq` (prediction),
`output_score`, and `aa_score` (precision-coverage curve support for the latter two is not yet
implemented). DeepNovo's special tokens for modified residues (`Cmod`, `Mmod`, `Nmod`, `Qmod`) are
converted to ProForma automatically.
:::

:::{dropdown} InstaNovo
Set up [InstaNovo](https://instanovo.ai/) and run it on the ground-truth MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload `results.csv`
for scoring and `config.yaml` for public submission.

From `results.csv`, ProteoBench reads `spectrum_id` (trailing number after the last colon, e.g.
`filename:1234` → `1234`), `predictions`, `log_probs`, and `token_log_probs`.
:::

:::{dropdown} NovoB
Set up [NovoB](https://github.com/ProteomeTeam/NovoB) and run it on the ground-truth MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload the
output CSV; no parameter file is required.

ProteoBench reads `spectrum_id` (first integer in the identifier string), `sequence`, and `score`.
NovoB treats all cysteines as carbamidomethylated and uses lowercase letters for variable
modifications (`m`, `n`, `q`, `s`, `t`, `y`), converted to ProForma automatically. NovoB does not
provide amino-acid-level scores.
:::

:::{dropdown} PepNet
Set up [PepNet](https://github.com/lkytal/PepNet) and run it on the ground-truth MGF, or use the
[web interface](https://denovo.predfull.com/) directly. **Be sure not to change the file name or the spectrum identifiers**. Upload `results.tsv`; no parameter file is
required.

ProteoBench reads `TITLE` (spectrum ID, from `scan=<number>`), `DENOVO` (prediction), `Score`, and
`Positional Score` (precision-coverage curve support not yet implemented).
:::

:::{dropdown} π-HelixNovo
Set up [π-HelixNovo](https://github.com/PHOENIXcenter/pi-HelixNovo/tree/pi-HelixNovo) and run it on
the ground-truth MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload `results.tsv` for scoring and `config.yaml` for public submission.

Columns `0` (spectrum ID, from `scan=<number>`), `1` (prediction), and `2` (score) are read;
positional scores are set equal to the amino-acid scores.

π-HelixNovo does not report a per-residue confidence score, so ProteoBench broadcasts the peptide-level score to every amino-acid position instead (the same fallback used for any tool without amino acid-level scores). Note that other versions of π-HelixNovo have this option.
:::

:::{dropdown} π-PrimeNovo
Set up [π-PrimeNovo](https://github.com/PHOENIXcenter/pi-PrimeNovo) and run it on the ground-truth
MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload `results.tsv` for scoring and `config.yaml` for public submission.

ProteoBench reads `label` (spectrum ID, from `scan=<number>`), `prediction`, and `score`; positional
scores are set equal to the amino-acid scores.

π-PrimeNovo does not report a per-residue confidence score, so ProteoBench broadcasts the peptide-level score to every amino-acid position instead (the same fallback used for any tool without amino acid-level scores).
:::

:::{dropdown} PointNovo
Best run through [this pipeline](https://github.com/denisbeslic/denovopipeline) on the ground-truth
MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload the output file (typically named with a `.pointnovo_output`-style extension); no
parameter file is required.

ProteoBench reads `feature_id` (spectrum ID), `predicted_sequence`, `predicted_score`, and
`predicted_position_score` (precision-coverage curve support not yet implemented). PointNovo's
spelled-out modification names (e.g. `C(Carbamidomethylation)`) are converted to ProForma
automatically.
:::

:::{dropdown} SMSNet
Best run through [this pipeline](https://github.com/denisbeslic/denovopipeline) on the ground-truth
MGF. **Be sure not to change the file name or the spectrum identifiers**. Upload **two** output files (`results` and `results_prob`); no parameter file is required.

ProteoBench reads `index` (spectrum ID), `sequence`, `peptide_score`, and `aa_scores`
(precision-coverage curve support not yet implemented). SMSNet uses the same lowercase-modification
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
length), `match_type_il`, `aa_exact_gt_il`, `aa_exact_dn_il` (same, but computed with I-L treated as equivalent), `match_type_deam`, `aa_exact_gt_deam`, `aa_exact_dn_deam` (same, but with deamidated Q/N treated as equivalent to E/D), `match_type_both`, `aa_exact_gt_both`, `aa_exact_dn_both` (same, with both ambiguities allowed at once), `bare` (predicted sequence with all I replaced by L), `category` (correct|in_fasta|not_in_fasta).

`aa_matches_gt`/`aa_matches_dn`/`pep_match` are mass-based and therefore identical regardless of the ambiguity toggles (I/L are already isomeric and deamidated Q/N are already isobaric with E/D under mass-based matching), so they are not duplicated per ambiguity combination the way `match_type`/`aa_exact_gt`/`aa_exact_dn` are.

**Spectrum characteristics** (precomputed): `peptide_length`, `missing_frag_sites`,
`missing_frag_pct`, `explained_y_pct`, `explained_b_pct`, `explained_by_pct`, `explained_all_pct`,
`cos`, `cos_ionb`, `cos_iony`, `spec_pearson`, `dotprod`, .

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
