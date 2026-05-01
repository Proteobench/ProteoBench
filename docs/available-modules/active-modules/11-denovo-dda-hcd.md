# *De Novo* - DDA - HCD 

This module compares the peptide sequencing accuracy of *de novo* models and algorithms for data acquired with data-dependent acquisition (DDA) on orbitrap instruments. Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

**Beware, deep learning models can be trained (and thus overfit) on the provided test data, which will result in a biased performance comparison. Therefore, if you retrained any of the models compatible with ProteoBench, we advise to explicitly describe the training data and training procedure used in the `Comments for submission` field before uploading the datapoint.**

We believe the module can be used to evaluate the impact of the following characteristics on the identification accuracy of the *de novo* tools:

- Post-translational modifications (PTMs)
- Missing fragments
- Peptide length
- Levels of noise relative to the signal from the precursor ion
- Species-specific sequence biases

This module will also reflect which tools outperform others in specific scenarios as defined above. Additionally, the effect of post-processing the *de novo* results can be investigated side-by-side with the original results (if uploaded separately). If post-processed, a description of how the original *de novo* results were acquired and the used post-processing method must be explicitly stated in the metadata section to safeguard transparency.

*If metadata for specific (post-processing) tools are not supported, feel free to [contact](mailto:proteobench@eubic-ms.org) the team of ProteoBench or create a [pull request](https://github.com/Proteobench/ProteoBench/pulls) to propose this feature yourself.*

## Data set

The widely used 'balanced' nine species dataset from [Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2) (first used here: [Li et al., 2017](https://pubmed.ncbi.nlm.nih.gov/28720701/)) was used as a benchmark dataset. This dataset is composed of nine species, generated in different research groups (see Table 1) and was searched using Tide-Percolator. The PSMs were filtered at PSM-level FDR at 1% and all peptides shared between any species were removed. Further downsampling of the data ultimatly results in 779,879 PSMs. For more detailed information on how the nine-species benchmark was developed, see [Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2).

**Table 1: Benchmark dataset statistics ([Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2))**

| PRIDE                                                               | Species                   | Instrument             | Spectra    | PSMs        |
| ------------------------------------------------------------------- | ------------------------- | ---------------------- | ---------- | ----------- |
| [PXD005025](https://www.ebi.ac.uk/pride/archive/projects/PXD005025) | *Vigna Mungo*             | QExactive              | 932,848    | **102,255** |
| [PXD004948](https://www.ebi.ac.uk/pride/archive/projects/PXD004948) | *Mus musculus*            | LTQ-Orbitrap Velos     | 306,786    | **25,522**  |
| [PXD004325](https://www.ebi.ac.uk/pride/archive/projects/PXD004325) | *Methanosarcina mazei*    | QExative Plus          | 3,728,183  | **100,485** |
| [PXD004565](https://www.ebi.ac.uk/pride/archive/projects/PXD004565) | *Bacillus subtilis*       | QExactive              | 4,336,428  | **113,234** |
| [PXD004536](https://www.ebi.ac.uk/pride/archive/projects/PXD004536) | *Candidatus endoloripes*  | Q Exactive Plus Hybrid | 2,272,023  | **82,514**  |
| [PXD004947](https://www.ebi.ac.uk/pride/archive/projects/PXD004947) | *Solanum lycopersicum*    | QExactive              | 603,506    | **100,056** |
| [PXD003868](https://www.ebi.ac.uk/pride/archive/projects/PXD003868) | *Saccharomyces cervisiae* | Q-Exactive Plus        | 1,477,397  | **108,973** |
| [PXD004467](https://www.ebi.ac.uk/pride/archive/projects/PXD004467) | *Apis mellifera*          | QExactive              | 823,169    | **102,285** |
| [PXD004424](https://www.ebi.ac.uk/pride/archive/projects/PXD004424) | *Homo sapiens*            | QExactive              | 684,821    | **44,555**  |
| Total                                                               |                           |                        | 15,165,161 | **779,879** |

To build the benchmark dataset, the file (nine-species-balanced.zip) was downloaded from here: [zenodo](https://zenodo.org/records/13685813). In this zip-file, each species is represented by a separate mgf-file. We combined the mgf-files and reannotate the spectrum identifiers to prevent duplicate identifiers.

We recommend downloading the parsed and combined dataset from the ProteoBench server here: [Data](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/)


## Metric calculation

The performance is evaluated at both the amino acid and peptide level. As introduced by [DeepNovo](https://www.pnas.org/doi/10.1073/pnas.1705691114), a correct amino acid whose mass differs by less than 0.1 Da from the corresponding ground truth amino acid. Additionally, this predicted amino acid must have either a prefix or suffix that differs by no more than 0.5 Da in mass from the corresponding amino acid sequence in the ground truth peptide. Correct peptides are defined as sequences where all amino acid predictions meet these criteria, ensuring that only fully accurate predictions are considered correct at the peptide level. In the module, this mode of evaluation is called '**mass-based**'. However, a more strict evaluation mode can be selected and is termed '**exact mode**'. In this mode, the two sequences should be exactly the same, where also cases such as deamidated-Q and E are considered incorrect. Only isoleucine and leucine substitutions are allowed.

### Main benchmarking plot

The main accuracy plot provides a **global overview of de novo sequencing performance** across the evaluated tools. It visualizes the relationship between **peptide-level identification performance** and **amino-acid level sequence accuracy**. Each point in the plot corresponds to a de novo sequencing tool and shows the amino acid and peptide level accuracy. The plot combines two levels of evaluation:

**X-axis – Peptide-level metric**  
The x-axis displays either peptide-level **precision** or **recall**, depending on the selected setting.

**Y-axis – Amino-acid level metric**  
The y-axis always shows the corresponding **amino-acid level metric**, measuring how accurately the individual residues in the predicted sequences match the ground truth.

This design allows the plot to simultaneously capture both **identification reliability** and **sequence-level correctness**.

The **Precision vs Recall** setting determines which peptide-level metric is shown on the x-axis.
Precision measures how many reported peptide predictions are correct:

    Precision = correct predictions ÷ predictions above threshold

This view emphasizes the **reliability of reported identifications**. Tools that achieve high precision produce predictions that are more likely to be correct.

Recall measures how many spectra were successfully identified:

    Recall = correct predictions ÷ total number of spectra

This view emphasizes the **coverage of the dataset**, indicating how many spectra a tool can successfully sequence.

The **evaluation mode** determines how predictions are classified as correct.

In **exact** evaluation mode, a prediction is considered correct only if the predicted peptide sequence **exactly matches the ground-truth sequence**, including both amino acids and modifications. This represents the **strictest accuracy definition**. In **mass-based** evaluation mode, predictions are considered correct when they match the ground-truth sequence based on **cumulative fragment masses**, even if the exact amino-acid sequence differs.
The algorithm identifies the longest **mass-matching prefix and suffix** between the predicted and reference peptide sequences. Two mass tolerances are used during this process:

- **Cumulative mass threshold** – maximum allowed difference between cumulative fragment masses (50 ppm)  
- **Individual mass threshold** – maximum allowed difference between individual amino-acid masses (20 ppm)

This evaluation accounts for typical ambiguities in mass spectrometry data. Match-based evaluation therefore counts both **exact matches and mass-equivalent matches**, while exact evaluation only counts **perfect sequence matches**.


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
- % Explained intensity: Serves as an inverse of the noise. Defined as the proportion of the intensity of annotated peaks over all peaks (TIC)

The precision is calculated on the peptide level as the proportion of correct peptides among the predictions made by the *de novo* tool

#### Species

Protein sequences can differ considerably between species. Therefore, particularly for deep learning methods, models trained on data from one species might not be directly applicable to predict peptide sequences from other species. To roughly explore these differences, precision is calculated as above for each species separately.

Beware, this set up was meant to work as training-test split procedure, where the data of eight species was used to train a model and evaluated on the unseen spectra from the excluded species. Here, we do not use it as intented since training the models is not directly supported in ProteoBench. If the user wants to use this feature as intented, the predictions should be generated accordingly as described. The results should be concatenated into a single result file in the format compatible with ProteoBench (see below).

## How to use

### Input data for private visualization of your benchmark run(s)

The module is flexible in terms of what workflow the participants can run. However, to ensure a fair comparison of the different *de novo* models, we suggest supporting the PTMs listed in Table 2.

### Submit your run for public usage

When you have successfully uploaded and visualized a benchmark run, we strongly encourage you to add the result to the online repository. This way, your run will be available to the entire community and can be compared to all other uploaded benchmark runs. By doing so, your workflow outputs, parameters and calculated metrics will be stored and publicly available.

To submit your run for public usage, you need to upload the parameter file associated to your run in the field Meta data for searches. Currently, we accept outputs from AdaNovo, Casanovo, InstaNovo, PepNet, π-HelixNovo, and π-PrimeNovo. Please fill the Comments for submission if needed, and confirm that the metadata is correct (corresponds to the benchmark run) before checking the button I confirm that the metadata is correct. Then the button I really want to upload it will appear to trigger the submission.

## Important tool-specific settings

Table 3 provides an overview of the required input files for public submission. More detailed instructions are provided for each individual tool in the following section.


**Table 3. Overview of input files required for metric calculation and public submission**

| Tool        | Input file    | Parameter File |
| ----------- | ------------- | -------------- |
| AdaNovo     | results.mztab | config.yaml    |
| Casanovo    | results.mztab | config.yaml    |
| InstaNovo   | results.csv   | config.yaml    |
| PepNet      | results.tsv   | / *             |
| π-HelixNovo | results.tsv   | config.yaml    |
| π-PrimeNovo | results.tsv   | config.yaml    |

\* PepNet does not have adaptable parameters, so no parameter file is required

### [AdaNovo](https://github.com/Westlake-OmicsAI/adanovo_v1)

> **[FLAG for review]** Add AdaNovo-specific instructions and the column names parsed from `results.mztab`. Verify the GitHub/documentation URL to link the tool name.

To generate data compatible with ProteoBench:
1. Set up Casanovo according to the developers instructions [here](https://github.com/Westlake-OmicsAI/adanovo_v1) and run the model on the provided [MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/). **Be sure not to change the file name or the spectrum identifiers**.
2. Upload `results.mztab` for metric calculation in the ProteoBench platform. For public submission, also provide `config.yaml`.

Once uploaded to ProteoBench, the following columns from `results.mztab` are considered:

- spectra_ref: Contains the spectrum identifier to map the ground-truth identifications with. The spectrum identifier is extracted as the number in `index=<number>`
- sequence: The predicted *de novo* sequence.
- search_engine_score[1]: The peptide confidence score. Used for precision-recall curve construction (*Currently not implemented*).
- opt_ms_run[1]_aa_scores: Amino acid-level confidence scores. Used for precision-recall curve construction (*Currently not implemented*).

### [Casanovo](https://casanovo.readthedocs.io/en/latest/)

To generate data compatible with ProteoBench:
1. Set up Casanovo according to the developers instructions [here](https://casanovo.readthedocs.io/en/latest/) and run the model on the provided [MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/). **Be sure not to change the file name or the spectrum identifiers**.
2. Upload `results.mztab` for metric calculation in the ProteoBench platform. For public submission, also provide `config.yaml`.

Once uploaded to ProteoBench, the following columns from `results.mztab` are considered:

- spectra_ref: Contains the spectrum identifier to map the ground-truth identifications with. The spectrum identifier is extracted as the number in `index=<number>`
- sequence: The predicted *de novo* sequence.
- search_engine_score[1]: The peptide confidence score. Used for precision-recall curve construction (*Currently not implemented*).
- opt_ms_run[1]_aa_scores: Amino acid-level confidence scores. Used for precision-recall curve construction (*Currently not implemented*).

### [InstaNovo](https://instanovo.ai/) (coming soon)

### [PepNet](https://denovo.predfull.com/)

To generate data compatible with ProteoBench:
1. Set up PepNet according to the developers instructions [here](https://github.com/lkytal/PepNet) and run the model on the the provided [MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/) or use the [webpage](https://denovo.predfull.com/) and provide the spectra from the [MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/) or use the [webpage](https://denovo.predfull.com/). **Be sure not to change the file name or the spectrum identifiers**.
2. Upload `results.tsv` for metric calculation. No parameter file is required for PepNet, as it does not have adaptable parameters.

Once uploaded to ProteoBench, the following columns from `results.tsv` are considered:
- TITLE: Contains the spectrum identifier to map the ground-truth identifications with. The spectrum identifier is extracted as the number in `scan=<number>`
- DENOVO: The predicted *de novo* sequence.
- Score: The peptide confidence score. Used for precision-recall curve construction (*Currently not implemented*).
- Positional Score: Amino acid-level confidence scores. Used for precision-recall curve construction (*Currently not implemented*).

### [π-HelixNovo](https://github.com/PHOENIXcenter/pi-HelixNovo)

To generate data compatible with ProteoBench:
1. Set up π-HelixNovo according to the developers instructions [here](https://github.com/PHOENIXcenter/pi-HelixNovo/tree/pi-HelixNovo) and run the model on the provided [MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/). **Be sure not to change the file name or the spectrum identifiers**.
2. Upload `results.tsv` for metric calculation in the ProteoBench platform. For public submission, also provide `config.yaml`.

Once uploaded to ProteoBench, the following columns from `results.tsv` are considered:
- 0: Contains the spectrum identifier to map the ground-truth identifications with. The spectrum identifier is extracted as the number in `scan=<number>`
- 1: The predicted *de novo* sequence.
- 2: The peptide confidence score. Used for precision-recall curve construction (*Currently not implemented*).

The positional scores for this model are set equal to the amino acid scores. Note that other versions of π-HelixNovo have this option.

### [π-PrimeNovo](https://github.com/PHOENIXcenter/pi-PrimeNovo)

To generate data compatible with ProteoBench:
1. Set up π-PrimeNovo according to the developers instructions [here](https://github.com/PHOENIXcenter/pi-PrimeNovo) and run the model on the provided [MGF file](https://proteobench.cubimed.rub.de/raws/DeNovo-HCD/). **Be sure not to change the file name or the spectrum identifiers**.
2. Upload `results.tsv` for metric calculation in the ProteoBench platform. For public submission, also provide `config.yaml`.

Once uploaded to ProteoBench, the following columns from `results.tsv` are considered:
- label: Contains the spectrum identifier to map the ground-truth identifications with. The spectrum identifier is extracted as the number in `scan=<number>`
- prediction: The predicted *de novo* sequence.
- score: The peptide confidence score. Used for precision-recall curve construction (*Currently not implemented*).

The positional scores for this model are set equal to the amino acid scores.

## toml file description

Each software tool produces specific output file formats. We made `.toml` files that describe where to find the information needed in each type of input. These can be found in `proteobench/io/parsing/io_parse_settings`.

- **[mapper]**
mapping between the headers in the input file (left-hand side) and the header of the intermediate file generated by ProteoBench.

  - `"spectrum_id"` = identifier used to match the prediction to the ground-truth PSM
  - `"sequence"` = predicted peptide sequence
  - `"score"` = per-prediction confidence score reported by the *de novo* tool
  - `"aa_scores"` (optional) = per-prediction confidence scores on the amino acid level reported by the *de novo* tool

- **[spectrum_id_mapper]**
Defines a regex on how to extract the spectrum identifier (number) from the `spectrum_id` column.

- **[sequence_mapper.replacement_dict]**
A mapping list which renames modifications from the `sequence` column. This will make uniform modification parsing with outputs from all the supported *de novo* tools more straightforward.

- **[modifications_parser]**
Specifies how to parse the modifications. Parameters:

  - `"parse_column"` = name of the column in the input file that contains the peptide sequence with localised modifications. This column will be parsed and converted to ProForma notation. Example: `"parse_column" = "sequence"`.
  - `"before_aa"` = indicates whether the modification tag appears before the amino acid it modifies in the input file. Set to true for formats like [+57.0215]C (tag precedes the residue), and false for formats like C[+57.0215] (tag follows the residue). This controls both how character positions are counted in the input and where the converted tag is inserted in the output ProForma sequence.
  - `"isalpha"` = when true, only alphabetic characters are retained when stripping the bare sequence from the modified sequence string. Example: from "NE[+57.0214]CVVVIR", the tag [+57.0214] is removed because its characters are non-alphabetic, leaving "NECVVVIR". Set to false if the modification notation uses only letters (e.g., lowercase letters for modifications).
  - `"isupper"` = when true, only uppercase characters are retained when stripping the bare sequence. Use this when modifications or ambiguous residues are represented by lowercase letters in the input. Example: from "NEYpCVVVIR", the lowercase p is removed. Can be combined with isalpha: when both are true, only uppercase alphabetic characters are kept.
  - `"pattern"` = regular expression that identifies and extracts modification tags from the modified sequence string. After removing all matches, only the bare amino acid sequence should remain. Example: "\\[([^]]+)\\]" matches any bracketed tag such as [+57.0215] or [Oxidation]. You can test your Python regex at regex101.com.
  - `"modification_dict"` = mapping from modification tags as they appear in the input file (left-hand side) to their standardised ProForma names (right-hand side). Example: {"+57.0215" = "Carbamidomethyl", "+15.9949" = "Oxidation"}. Tags not present in the dictionary are passed through as-is (still wrapped in brackets in the output). The replacement is applied before ProForma formatting.

## Result Description

After uploading an output file, a table is generated. The table is built by left-joining the de novo predictions onto the ground-truth dataset: every ground-truth spectrum is retained, and rows where the tool made no prediction will have `NaN` for the prediction columns. It contains the following columns:

**Identification**

| Column | Description |
| ------ | ----------- |
| `spectrum_id` | Integer scan ID extracted from the spectrum identifier, used to join predictions to ground-truth PSMs |
| `proforma` | Predicted peptide sequence in ProForma notation |
| `peptidoform_ground_truth` | Ground-truth peptide sequence in ProForma notation |
| `score` | Per-peptide confidence score reported by the *de novo* tool |
| `aa_scores` | List of per-amino-acid confidence scores; if not provided by the tool, the peptide score is used for each position |
| `title` | Raw spectrum title from the ground-truth MGF file |
| `precursor_mz` | Precursor m/z of the spectrum |
| `retention_time` | Retention time of the spectrum |
| `collection` | Species/dataset the spectrum originates from |

**Match evaluation** (added by the scoring module)

| Column | Description |
| ------ | ----------- |
| `match_type` | `"exact"` — prediction and ground truth are identical `Peptidoform` objects; `"mass"` — mass-based prefix+suffix match passes both tolerances; `"mismatch"` — neither criterion is met |
| `pep_match` | `True` if the prediction is a correct peptide match (exact or mass-based) |
| `aa_matches_gt` | Boolean array indexed to the **ground-truth** sequence length; `True` at each position where the amino acid is a mass-based match |
| `aa_matches_dn` | Boolean array indexed to the **predicted** sequence length; `True` at each position where the amino acid is a mass-based match |
| `aa_exact_gt` | Boolean array indexed to the ground-truth sequence; `True` at each position where the amino acid is an exact match |
| `aa_exact_dn` | Boolean array indexed to the predicted sequence; `True` at each position where the amino acid is an exact match |

**Spectrum characteristics** (pre-computed in the ground-truth file)

| Column | Description |
| ------ | ----------- |
| `peptide_length` | Length of the ground-truth peptide; N-terminal modification tokens are counted separately |
| `missing_frag_sites` | Number of missing complementary b/y ion pairs in the spectrum |
| `missing_frag_pct` | Fraction of fragmentation sites that are missing |
| `explained_y_pct` | Fraction of total intensity (TIC) explained by annotated y-ions |
| `explained_b_pct` | Fraction of TIC explained by annotated b-ions |
| `explained_by_pct` | Fraction of TIC explained by annotated b- and y-ions combined |
| `explained_all_pct` | Fraction of TIC explained by all annotated peaks |
| `cos` | Cosine similarity between observed and MS2PIP-predicted spectrum |
| `cos_ionb` | Cosine similarity for b-ions only |
| `cos_iony` | Cosine similarity for y-ions only |
| `spec_pearson` | Pearson correlation between observed and predicted spectrum |
| `dotprod` | Dot product between observed and predicted spectrum |

**PTM flags — ground truth** (`True` if the PTM is present in the ground-truth peptide)

| Column | Modification |
| ------ | ------------ |
| `M-Oxidation` | Methionine oxidation (`M[UNIMOD:35]`) |
| `Q-Deamidation` | Glutamine deamidation (`Q[UNIMOD:7]`) |
| `N-Deamidation` | Asparagine deamidation (`N[UNIMOD:7]`) |
| `N-term Acetylation` | N-terminal acetylation (`[UNIMOD:1]-`) |
| `N-term Carbamylation` | N-terminal carbamylation (`[UNIMOD:5]-`) |
| `N-term Ammonia-loss` | N-terminal ammonia loss (`[UNIMOD:385]-`) |

**PTM flags — de novo prediction** (`True` if the PTM is present in the predicted peptide; `None` if the prediction could not be parsed)

| Column | Modification |
| ------ | ------------ |
| `M-Oxidation (denovo)` | Methionine oxidation |
| `Q-Deamidation (denovo)` | Glutamine deamidation |
| `N-Deamidation (denovo)` | Asparagine deamidation |
| `N-term Acetylation (denovo)` | N-terminal acetylation |
| `N-term Carbamylation (denovo)` | N-terminal carbamylation |
| `N-term Ammonia-loss (denovo)` | N-terminal ammonia loss |

## Define Parameters

To make the results available to the entire community, you need to provide the parameter file that corresponds to your analysis. You can upload it in the drag and drop area in the "Add results to online repository" section (under "Download calculated metrics").
See [here](#important-tool-specific-settings) for all compatible parameter files.

In this module, we keep track of the following parameters. If you feel that some important information is missing, please add it in the `Comments for submission` field.

| Parameter | Description |
| --------- | ----------- |
| Software name | Name of the *de novo* sequencing tool used |
| Software tool version | Version of the tool |
| Model checkpoint identifier | Identifier of the model weights or checkpoint used (e.g. a filename, tag, or URL) |
| Number of beams | Number of beams used during beam-search decoding |
| Number of peaks considered in the spectrum | Maximum number of peaks retained per spectrum before prediction |
| Precursor mass tolerance | Precursor mass tolerance applied, including the unit (e.g. `10 ppm` or `0.02 Da`) |
| Minimum peptide length | Minimum peptide length considered for prediction |
| Maximum peptide length | Maximum peptide length considered for prediction |
| Minimum m/z value | Minimum fragment m/z value considered |
| Maximum m/z value | Maximum fragment m/z value considered |
| Minimum intensity value | Minimum fragment intensity threshold applied |
| Maximum intensity value | Maximum fragment intensity threshold applied |
| Tokens | The set of amino acids and modifications the model can predict (its vocabulary) |
| Minimum precursor charge | Minimum precursor charge state considered |
| Maximum precursor charge | Maximum precursor charge state considered |
| Remove precursor peaks | Whether precursor peaks are removed from the spectrum before prediction |
| Isotope error range | Allowed isotope error range during precursor matching |
| Decoding strategy | Strategy used to generate predictions (e.g. beam search, greedy) |

Once you confirm that the metadata is correct (and corresponds to the results file you uploaded before generating the plots), a button will appear. Press it to submit.

**If some parameters are not captured by the parameter file, it is important that you provide them in the "Comments for submission" field.**

Once submitted, you will see a weblink directing you to a pull request on the GitHub repository of the module. Please write down its number to keep track of your submission. If everything looks good, one of the reviewers will accept it and make your data public. This will take a few working days.

Please contact us if you have any issue. To do so, you can create an [issue](https://github.com/Proteobench/ProteoBench/issues/new) on our GitHub, or [send us an email](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).