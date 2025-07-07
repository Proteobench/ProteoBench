# Parameters parsed for public submission

We automatically retrieve the parameters used for a specific worklow run in the parameter file submitted next to the result. The parsing depends on the tool and are described below. If you have any suggestions or concerns related to how we parse these parameters, please let us know by creating a [GitHub issue](https://github.com/Proteobench/ProteoBench/issues).

## General comments on the parameters that are retrieved by ProteoBench

The parameters that are retrieved from the parameter files are the following:

| Parameter                | Description                                                                                                                                                                                                                   |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| software_name            | Name of the software tool.                                                                                                                                                                                                   |
| software_version         | Version of the software tool used to generate the run.                                                                                                                                                                       |
| search_engine            | Name of the search engine used for MS-based identification. Often the same as the software name, but is relevant for data analysis workflows that allow multiple search engines to be used (e.g. quantms).                   |
| search_engine_version    | Version of the search engine.                                                                                                                                                                                                |
| ident_fdr_psm            | Target or obtained FDR at PSM level.                                                                                                                                                                                         |
| ident_fdr_peptide        | Target or obtained FDR at peptide level|
|ident_fdr_protein         | Target or obtained FDR at protein level|
| enable_match_between_runs| TRUE if match between run is enabled.                                                                                                                                                                                        |
| precursor_mass_tolerance | Precursor mass tolerance used for identification (in the format "[-20 ppm, 20 ppm]").                                                                                                                                        |
| fragment_mass_tolerance  | Fragment mass tolerance used for identification (in the format "[-50 ppm, 50 ppm]").                                                                                                                                         |
| enzyme                   | Enzyme used for digesting peptides.                                                                                                                                                                                          |
| allowed_miscleavages     | Number of maximum missed cleavages allowed per peptide.                                                                                                                                                                      |
| min_peptide_length       | Minimum peptide length considered in the analysis.                                                                                                                                                                           |
| max_peptide_length       | Maximum peptide length considered in the analysis.                                                                                                                                                                           |
| fixed_mods               | List of fixed modifications (PTMs) considered in the analysis.                                                                                                                                                               |
| variable_mods            | List of variable modifications (PTMs) considered in the analysis.                                                                                                                                                            |
| max_mods                 | Maximum number of modifications per peptide considered in the analysis.                                                                                                                                                      |
| min_precursor_charge     | Minimum precursor charge considered in the analysis.                                                                                                                                                                         |
| max_precursor_charge     | Maximum precursor charge considered in the analysis.                                                                                                                                                                         |
| quantification_method    | Quantification method. This applies to software tools that offer different strategies for quantification.                                                                                                                     |
| protein_inference        | Protein inference method.                                                                                                                                                                                                    |
| predictors_library       | Library used for the analysis in DIA. With the current module, we do not support experimentally generated libraries, but some software tools allow use of different in-silico-generated libraries.                            |
| scan_window              | Scan window settings.                                                                                                                                                                                                        |

## Tool-specific information
### AlphaDIA
*Parsed parameter file: log.txt*

| Parameter                | Parsed value |
|--------------------------|-------|
| software_name            |    AlphaDIA (fixed)   |
| software_version         |   Parsed from log file header    |
| search_engine            |    AlphaDIA (fixed)   |
| search_engine_version    |   Not parsed as no difference with software_version    |
| ident_fdr_psm            |   "fdr" setting in "fdr" branch of the config    |
| ident_fdr_peptide        |   Not parsed as not an option    |
|ident_fdr_protein         |   "fdr" setting in "fdr" branch of the config    | 
| enable_match_between_runs|    Set to true if MBR step enabled, else False   |
| precursor_mass_tolerance |   "target_ms1_tolerance" setting in "search" branch of the config    |
| fragment_mass_tolerance  |   "target_ms2_tolerance" setting in "search" branch of the config   |
| enzyme                   |   "enzyme" setting in "library_prediction" branch of the config   |
| allowed_miscleavages     |   "missed_cleavages" setting in "library_prediction" branch of the config    |
| min_peptide_length       |   Minimum value in "precursor_len" setting in "library_prediction" branch of the config    |
| max_peptide_length       |    Maximum value in "precursor_len" setting in "library_prediction" branch of the config   |
| fixed_mods               |    "fixed_modifications" setting in "library_prediction" branch of the config   |
| variable_mods            |   "variable_modifications" setting in "library_prediction" branch of the config    |
| max_mods                 |    "max_var_mod_num" setting in "library_prediction" branch of the config   |
| min_precursor_charge     |    Minimum value in "precursor_charge" setting in "library_prediction" branch of the config   |
| max_precursor_charge     |   Maximum value in "precursor_charge" setting in "library_prediction" branch of the config    |
| quantification_method    |    DirectLFQ (fixed)   |
| protein_inference        |   "inference_strategy" in "fdr" branch of the config    |
| predictors_library       |   AlphaPeptDeep (fixed)    |
| scan_window              |   Not parsed    |

### AlphaPept

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |             |
| software_version         |             |
| search_engine            |             |
| search_engine_version    |             |
| ident_fdr_psm            |             |
| ident_fdr_peptide        |             |
| ident_fdr_protein        |             | 
| enable_match_between_runs|             |
| precursor_mass_tolerance |             |
| fragment_mass_tolerance  |             |
| enzyme                   |             |
| allowed_miscleavages     |             |
| min_peptide_length       |             |
| max_peptide_length       |             |
| fixed_mods               |             |
| variable_mods            |             |
| max_mods                 |             |
| min_precursor_charge     |             |
| max_precursor_charge     |             |
| quantification_method    |             |
| protein_inference        |             |
| predictors_library       |             |
| scan_window              |             |
### DIA-NN

We use the log file and extract the software version. Then, find the command line string that was used to run DIA-NN and parse it to extract settings.
Default values are set for parameters that are not specified in the command line:

- "enable_match_between_runs": False
- "quantification_method": "QuantUMS high-precision"
- "protein_inference": "Genes"

If the --cfg flag is used (meaning a configuration file was used), the parameters are parsed from the free text underneath the cmd line.

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |             |
| software_version         |             |
| search_engine            |             |
| search_engine_version    |             |
| ident_fdr_psm            |             |
| ident_fdr_peptide        |             |
| ident_fdr_protein        |             | 
| enable_match_between_runs|             |
| precursor_mass_tolerance |             |
| fragment_mass_tolerance  |             |
| enzyme                   |             |
| allowed_miscleavages     |             |
| min_peptide_length       |             |
| max_peptide_length       |             |
| fixed_mods               |             |
| variable_mods            |             |
| max_mods                 |             |
| min_precursor_charge     |             |
| max_precursor_charge     |             |
| quantification_method    |             |
| protein_inference        |             |
| predictors_library       |             |
| scan_window              |             |