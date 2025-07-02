# *De Novo* - DDA - HCD (**We are working on the documentation: come back soon.**)

This module compares the peptide sequencing accuracy of *de novo* models and algorithms for data acquired with data-dependent acquisition (DDA) on orbitrap instruments. Users can load their data and inspect the results privately. They can also make their outputs public by providing the associated parameter file and submitting the benchmark run to ProteoBench. By doing so, their workflow output will be stored alongside all other benchmark runs in ProteoBench and will be accessible to the entire community.

**Beware, deep learning models can be trained (and thus overfit) on the provided test data, which will result in a biased performance comparison. Therefore, in the case of using deep learning models, we advise to explicitly descripe the training data and training procedure used in the `Comments for submission` field before uploading the datapoint.**

We believe the module can be used to evaluate the impact of the following characteristics on the identification accuracy of the *de novo* tools:
- Post-translational modifications (PTMs)
- Missing fragments
- Peptide length
- Levels of noise relative to the signal from the precursor ion
- Species-specific sequence biases

This module will also reflect which tools outperform others in specific scenario's as defined above. Additionally, the effect of post-processing the *de novo* results can be investigated side-by-side with the original results (if uploaded seperatly). If post-processed, a description of how the original *de novo* results were acquired and the used post-processing method must be explicitly stated in the metadata section to safeguard transparency.

*If metadata for specific (post-processing) tools are not supported, feel free to [contact](proteobench@eubic-ms.org) the team of ProteoBench or create a [pull request](https://github.com/Proteobench/ProteoBench/pulls) to propose this feature yourself.*

## Data set

The widely used 'balanced' nine species dataset from [Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2) (first used here: [Li et al., 2017](https://pubmed.ncbi.nlm.nih.gov/28720701/)) was used as a benchmark dataset. This dataset is composed of nine species, generated in different research groups (see Table 1) and was searched using Tide-Percolator. The PSMs were filtered at PSM-level FDR at 1% and all peptides shared between any species were removed. Further downsampling of the data ultimatly results in 779,879 PSMs. For more detailed information on how the nine-species benchmark was developed, see [Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2).

**Table 1: Benchmark dataset statistics ([Noble et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549408/#notes2))**

|PRIDE|Species|Instrument|Spectra|PSMs|
|-----|-----|-----|-----|-----|
|[PXD005025](https://www.ebi.ac.uk/pride/archive/projects/PXD005025)|*Vigna Mungo*|QExactive|932,848|**102,255**|
|[PXD004948](https://www.ebi.ac.uk/pride/archive/projects/PXD004948)|*Mus musculus*|LTQ-Orbitrap Velos|306,786|**25,522**|
|[PXD004325](https://www.ebi.ac.uk/pride/archive/projects/PXD004325)|*Methanosarcina mazei*|QExative Plus|3,728,183|**100,485**|
|[PXD004565](https://www.ebi.ac.uk/pride/archive/projects/PXD004565)|*Bacillus subtilis*|QExactive|4,336,428|**113,234**|
|[PXD004536](https://www.ebi.ac.uk/pride/archive/projects/PXD004536)|*Candidatus endoloripes*|Q Exactive Plus Hybrid|2,272,023|**82,514**|
|[PXD004947](https://www.ebi.ac.uk/pride/archive/projects/PXD004947)|*Solanum lycopersicum*|QExactive|603,506|**100,056**|
|[PXD003868](https://www.ebi.ac.uk/pride/archive/projects/PXD003868)|*Saccharomyces cervisiae*|Q-Exactive Plus|1,477,397|**108,973**|
|[PXD004467](https://www.ebi.ac.uk/pride/archive/projects/PXD004467)|*Apis mellifera*|QExactive|823,169|**102,285**|
|[PXD004424]()|*Homo sapiens*|QExactive|684,821|**44,555**|
|Total|||15,165,161|**779,879**|

The benchmark dataset (nine-species-balanced.zip) can be downloaded here: [zenodo](https://zenodo.org/records/13685813). In this zip-file, each species is represented by a seperate mgf-file. We used this [script](https://github.com/Proteobench/ProteoBench/tree/denovo_module/proteobench/io/data) to combine the mgf-files and reannotate the spectrum identifiers to prevent duplicate identifiers.


## Metric calculation

The performance is evaluated at both the amino acid and peptide level. As introduced by [DeepNovo](https://www.pnas.org/doi/10.1073/pnas.1705691114), a correct amino acid whose mass differs by less than 0.1 Da from the corresponding ground truth amino acid. Additionally, this predicted amino acid must have either a prefix or suffix that differs by no more thatn 0.5 Da in mass from the corresponding amino acid sequence in the ground truth peptide. Correct peptides are defined as sequences where all amino acid predictions meet these criteria, ensuring that only fully accurate predictions are considered correct at the peptide level. In the module, this mode of evaluation is called '**mass-based**'. However, a more strict evaluation mode can be selected and is termed '**exact mode**'. In this mode, the two sequences should be exactly the same, where also cases such as deamidated-Q and E are considered incorrect. Only isoleucine and leucine substitutions are allowed.

### Main benchmarking plot

In the main benchmarking results plot, *precision* is calculated as the proportions of correct predictions among the predictions made by the *de novo* tool. This metric is plotted against the *coverage*, defined as the proportion of predictions made, which accounts for the fact that some *de novo* tools don't report results for all spectra. In this plot, the user can toggle between amino acid-level or peptide-level accuracy.

### In-depth plots

The in-depth section provides a more detailed picture of the (relative) performance of the *de novo* tools.


#### PTMs

Firstly, the ability of the tool to accuratly predict several **PTM's** can be evaluated. Since the ground-truth dataset was generated by searching against specific modifications, only these are supported. In Table 2, an overview of supported PTMs and their statistics are stated. Two types of plots are created for this: (i) an overview plot and (ii) PTM-specific plots. In the overview plot, the precision across all modifications are plotted together where precision is defined as the proportion of correctly predicted modifications over all peptides containing this modification in the ground-truth. A correct prediction does not require a fully correctly predicted peptide, only the specific amino acid with its PTM at the correct position. In the PTM-specific plots, this precision is plotted against the precision calculated as the proportion over all peptides containing this modification in the predicted peptide list. By doing so, biased precision estimates are handled in cases when the *de novo* tool would predict PTMs abundantly yet spuriously.

**Table 2. PTMs in the ground-truth dataset**
|PTM|Occurences|
|---------|-----|
|Methionine Oxidation|62815|
|Endopeptidase|Trypsin/P|
|Fixed modifications|Carbamidomethylation (C)|
|Variable modifications|Oxidation (M), Acetyl (Protein N-term)|
|Precursor mass tolerance|10 ppm|
|Fragment mass tolerance|0.02 Da|
|Minimum peptide length|7 residues|


#### Spectrum characteristics

Secondly, the ability of the tool to correctly predict spectra with specific characteristics can be evaluated. As shown in previous benchmark publications ([Denis et al](https://doi.org/10.1093/bib/bbac542), [Muth et al](https://doi.org/10.1093/bib/bbx033), [McDonnel et al](https://doi.org/10.1016/j.csbj.2022.03.008)), the accuracy of any *de novo* tool is dependent on several spectrum properties. To show this effect, we calculate precision on a selection of PSMs subsetted by each of the following characteristics:
- Missing fragmentation sites: The number of missing complementary (b and y) ions
- Peptide length: Not specifically a spectrum characteristic, but reported to impact the performance of *de novo* tools
- % Explained intensity: Serves as an inverse of the noise. Defined as the proportion of the intensity of annotated peaks over all peaks (TIC)

The precision is calculated on the peptide level as the proportion of correct peptides among the predictions made by the *de novo* tool

#### Species

Protein sequences can differ considerably between species. Therefore, particularly for deep learning methods, models trained on data from one species might not be directly applicable to predict peptide sequences from other species. To roughly explore these differences, precision is calculated as above for each species seperately.

Beware, this set up was meant to work as training-test split procedure, where the data of eight species was used to train a model and evaluated on the unseen spectra from the excluded species. Here, we do not use it as intented since training the models is not directly supported in ProteoBench. If the user wants to use this feature as intented, the predictions should be generated accordingly as described. The results should be concatenated into a single result file in the format compatible with ProteoBench (see below).

#### Spectrum identification overlap

TODO

## How to use

The module is flexible in terms of what workflow the participants can run. To ensure fair comparison, we suggest PTM support as stated in table 2.

### Input data for private visualization of your benchmark run(s)

The module is flexible of what workflow the participants can run. However, to ensure a fair comparison of the different *de novo* models, we suggest using the following general parameters listed in Table 2.

**Table 1. Suggested paramaters**

TODO: Insert table here

### Submit your run for public usage

General description I believe

Description on pull requests for public datapoint submission

## Important tool-specific settings

Table 2 provides an overview of the required input files for public submission. More detailed instructions are provided for each individual tool in the following section.

Table 2: Required input files

Will probably be a bit general for the de novo module

Description of the Custom format and how the format is expected for each supported tool

## toml file description

How the toml file parses the output files

## Result Description

Descripe the table format the of the intermediate

## Define Parameters

Describe the supported parameters