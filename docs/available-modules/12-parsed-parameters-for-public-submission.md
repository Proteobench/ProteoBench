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
*Parsed parameter file: log.txt* #TODO: add link to examples for each of the parsed files (link to GitHub test files)

| Parameter                | Parsed value |
|--------------------------|-------|
| software_name            |    AlphaDIA (fixed)   |
| software_version         |   Parsed from log file header    |
| search_engine            |    AlphaDIA (fixed)   |
| search_engine_version    |   Not parsed as no difference with software_version    |
| ident_fdr_psm            |   "fdr" setting in "fdr" section of the config    |
| ident_fdr_peptide        |   Not parsed as not an option    |
|ident_fdr_protein         |   "fdr" setting in "fdr" section of the config    | 
| enable_match_between_runs|    Set to true if MBR step enabled, else False   |
| precursor_mass_tolerance |   "target_ms1_tolerance" setting in "search" section of the config    |
| fragment_mass_tolerance  |   "target_ms2_tolerance" setting in "search" section of the config   |
| enzyme                   |   "enzyme" setting in "library_prediction" section of the config   |
| allowed_miscleavages     |   "missed_cleavages" setting in "library_prediction" section of the config    |
| min_peptide_length       |   Minimum value in "precursor_len" setting in "library_prediction" section of the config    |
| max_peptide_length       |    Maximum value in "precursor_len" setting in "library_prediction" section of the config   |
| fixed_mods               |    "fixed_modifications" setting in "library_prediction" section of the config   |
| variable_mods            |   "variable_modifications" setting in "library_prediction" section of the config    |
| max_mods                 |    "max_var_mod_num" setting in "library_prediction" section of the config   |
| min_precursor_charge     |    Minimum value in "precursor_charge" setting in "library_prediction" section of the config   |
| max_precursor_charge     |   Maximum value in "precursor_charge" setting in "library_prediction" section of the config    |
| quantification_method    |    DirectLFQ (fixed)   |
| protein_inference        |   "inference_strategy" in "fdr" section of the config    |
| predictors_library       |   AlphaPeptDeep (fixed)    |
| scan_window              |   Not parsed    |

### AlphaPept
*Parsed parameter file: .yaml*
| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |       AlphaPept (fixed)      |
| software_version         |      "version" in "summary" section of the config       |
| search_engine            |      AlphaPept (fixed)       |
| search_engine_version    |      "version" in "summary" section of the config       |
| ident_fdr_psm            |       "peptide_fdr" in "search" section of the config      |
| ident_fdr_peptide        |       Not parsed as not an option   |
| ident_fdr_protein        |      "protein_fdr" in "search" section of the config       | 
| enable_match_between_runs|       True if "match" is enabled in "workflow" section of the config, else False      |
| precursor_mass_tolerance |      "prec_tol" in "search" section of the config       |
| fragment_mass_tolerance  |      "frag_tol" in "search" section of the config       |
| enzyme                   |      "protease" in "fasta" section of the config       |
| allowed_miscleavages     |      "n_missed_cleavages" in "fasta" section of the config       |
| min_peptide_length       |      "pep_length_min" in "fasta" section of  the config       |
| max_peptide_length       |      "pep_length_max" in "fasta" section of the config       |
| fixed_mods               |       "mods_fixed" & "mods_fixed_terminal" & "mods_fixed_terminal_prot" in "fasta" section of the config      |
| variable_mods            |      "mods_variable" & "mods_variable_terminal" & "mods_variable_terminal_prot" in "fasta" section of the config      |
| max_mods                 |      "n_modifications_max" in "fasta" section of the config       |
| min_precursor_charge     |      "iso_charge_min" in "features" section of the config       |
| max_precursor_charge     |      "iso_charge_max" in "features" section of the config       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed as not applicable       |
| scan_window              |      Not parsed       |

### DIA-NN
*Parsed parameter file: log.txt*
DIA-NN parameters are parsed either from the command line string found in the log file or, if the --cfg flag is used (meaning a custom configuration file was used, which we do not have access to), the parameters are parsed from the free text underneath the command line string. For robust parameter parsing, we recommend not using the --cfg flag.

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      DIA-NN (fixed)       |
| software_version         |      Parsed from log file header       |
| search_engine            |       DIA-NN (fixed)      |
| search_engine_version    |      Parsed from log file header       |
| ident_fdr_psm            |      No --cfg: value set for "--qvalue"<br>--cfg: parsed from line "Output will be filtered at X FDR"       |
| ident_fdr_peptide        |      Not parsed as not an option       |
| ident_fdr_protein        |      Not parsed as not an option       | 
| enable_match_between_runs|      No --cfg: True if "--reanalyse" is set, else false<br>--cfg: True if "reanalyse them" (version <1.8) or "MBR enabled" (version >1.8) is mentioned       |
| precursor_mass_tolerance |      Value set for "--mass-acc-ms1". If this parameter is not set, it means tolerance optimization<br>will be performed. In that case,as well as if --cfg is set, the value will be parsed from the first<br> occurence of the line "Recommended MS1 mass accuracy setting: X ppm"      |
| fragment_mass_tolerance  |      Value set for "--mass-acc". If this parameter is not set, it means tolerance optimization will<br> be performed. In that case, as well as if --cfg is set, the value will be parsed from line <br>"Optimised mass accuracy: X ppm"      |
| enzyme                   |     No --cfg: value set for "--cut"<br>--cfg: parsed from line "In silico digest will involve cuts at X but excluding cuts at X"        |
| allowed_miscleavages     |     No --cfg: value set for "--missed-cleavages"<br>--cfg: parsed from line "Maximum number of missed cleavages set to X"        |
| min_peptide_length       |     No --cfg: value set for "--min-pep-len"<br>--cfg: parsed from the line "Min peptide length set to X"        |
| max_peptide_length       |     No --cfg: value set for "--max-pep-len"<br>--cfg: parsed from the line "Max peptide length set to X"        |
| fixed_mods               |     No --cfg: value set for "--mod"<br>--cfg: parsed from the lines "X enabled as a fixed modification" and "Modification X with mass<br> delta X at X will be considered as fixed        |
| variable_mods            |     No --cfg: value set for "--var-mod"<br>--cfg: parsed form line "Modification X with mass delta X at X will be considered as variable"        |
| max_mods                 |      No --cfg: value set for "var-mods"<br>--cfg: parsed from line "Maximum number of variable modifications set to X"       |
| min_precursor_charge     |      No --cfg: value set for "min-pr-charge"<br>--cfg: parsed from line "Min precursor charge set to X"      |
| max_precursor_charge     |      No --cfg: value set for "max-pr-charge"<br>--cfg: parsed from line "Max precursor charge set to X"      |
| quantification_method    |     No --cfg: either "Legacy" (if --direct-quant set), "QuantUMS high-accuracy if --high-acc set<br>or "QuantUMS high-precision (default)<br>--cfg: parsed from line "X quantification mode"       |
| protein_inference        |      No --cfg: value set for "--pg-level" or "no-prot-inf", with the mapping {"0": "Isoforms", "1": "Protein_names", "2": "Genes"}<br>--cfg: parsed from line "Implicit protein grouping: X"       |
| predictors_library       |      No --cfg: either "DIA-NN" if "--predictor" is set, or "User defined" if "--lib" is set to a path     |
| scan_window              |       Parsed from line "Scan window radius set to X"      |



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