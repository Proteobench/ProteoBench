# Parameters parsed for public submission

We automatically retrieve the parameters used for a specific worklow run in the parameter file submitted next to the 
result. The parsing depends on the tool and are described below. If you have any suggestions or concerns related to 
how we parse these parameters, please let us know by creating a 
[GitHub issue](https://github.com/Proteobench/ProteoBench/issues).

A single-table overview of the parsing methodology of supported tools can be found 
[here](https://github.com/Proteobench/ProteoBench/tree/main/docs/parsing_overview.tsv).

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
| precursor_mass_tolerance | Precursor mass tolerance used for identification (in the format **[-20 ppm, 20 ppm]**).                                                                                                                                        |
| fragment_mass_tolerance  | Fragment mass tolerance used for identification (in the format **[-50 ppm, 50 ppm]**).                                                                                                                                         |
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
*Parsed parameter file: log.txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/log_alphadia_1.txt).* 

| Parameter                | Parsed value |
|--------------------------|-------|
| software_name            |    AlphaDIA (fixed)   |
| software_version         |   Parsed from log file header    |
| search_engine            |    AlphaDIA (fixed)   |
| search_engine_version    |   Not parsed as no difference with software_version    |
| ident_fdr_psm            |   **fdr** setting in **fdr** section of the config    |
| ident_fdr_peptide        |   Not parsed as not an option    |
|ident_fdr_protein         |   **fdr** setting in **fdr** section of the config    | 
| enable_match_between_runs|    Set to true if MBR step enabled, else False   |
| precursor_mass_tolerance |   **target_ms1_tolerance** setting in **search** section of the config    |
| fragment_mass_tolerance  |   **target_ms2_tolerance** setting in **search** section of the config   |
| enzyme                   |   **enzyme** setting in **library_prediction** section of the config   |
| allowed_miscleavages     |   **missed_cleavages** setting in **library_prediction** section of the config    |
| min_peptide_length       |   Minimum value in **precursor_len** setting in **library_prediction** section of the config    |
| max_peptide_length       |    Maximum value in **precursor_len** setting in **library_prediction** section of the config   |
| fixed_mods               |    **fixed_modifications** setting in **library_prediction** section of the config   |
| variable_mods            |   **variable_modifications** setting in **library_prediction** section of the config    |
| max_mods                 |    **max_var_mod_num** setting in **library_prediction** section of the config   |
| min_precursor_charge     |    Minimum value in **precursor_charge** setting in **library_prediction** section of the config   |
| max_precursor_charge     |   Maximum value in **precursor_charge** setting in **library_prediction** section of the config    |
| quantification_method    |    DirectLFQ (fixed)   |
| protein_inference        |   **inference_strategy** in **fdr** section of the config    |
| predictors_library       |   AlphaPeptDeep (fixed)    |
| scan_window              |   Not parsed    |

### AlphaPept
*Parsed parameter file: .yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/alphapept_0.4.9.yaml).*
| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |       AlphaPept (fixed)      |
| software_version         |      **version** in **summary** section of the config       |
| search_engine            |      AlphaPept (fixed)       |
| search_engine_version    |      **version** in **summary** section of the config       |
| ident_fdr_psm            |       **peptide_fdr** in **search** section of the config      |
| ident_fdr_peptide        |       Not parsed as not an option   |
| ident_fdr_protein        |      **protein_fdr** in **search** section of the config       | 
| enable_match_between_runs|       True if **match** is enabled in **workflow** section of the config, else False      |
| precursor_mass_tolerance |      **prec_tol** in **search** section of the config       |
| fragment_mass_tolerance  |      **frag_tol** in **search** section of the config       |
| enzyme                   |      **protease** in **fasta** section of the config       |
| allowed_miscleavages     |      **n_missed_cleavages** in **fasta** section of the config       |
| min_peptide_length       |      **pep_length_min** in **fasta** section of  the config       |
| max_peptide_length       |      **pep_length_max** in **fasta** section of the config       |
| fixed_mods               |       **mods_fixed** & **mods_fixed_terminal** & **mods_fixed_terminal_prot** in **fasta** section of the config      |
| variable_mods            |      **mods_variable** & **mods_variable_terminal** & **mods_variable_terminal_prot** in **fasta** section of the config      |
| max_mods                 |      **n_modifications_max** in **fasta** section of the config       |
| min_precursor_charge     |      **iso_charge_min** in **features** section of the config       |
| max_precursor_charge     |      **iso_charge_max** in **features** section of the config       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed as not applicable       |
| scan_window              |      Not parsed       |

### DIA-NN
*Parsed parameter file: log.txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/DIA-NN_cfg_directq.txt).*
DIA-NN parameters are parsed either from the command line string found in the log file or, if the --cfg flag is used (meaning a custom configuration file was used, which we do not have access to), the parameters are parsed from the free text underneath the command line string. For robust parameter parsing, we recommend not using the --cfg flag.

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      DIA-NN (fixed)       |
| software_version         |      Parsed from log file header       |
| search_engine            |       DIA-NN (fixed)      |
| search_engine_version    |      Parsed from log file header       |
| ident_fdr_psm            |      No --cfg: value set for **--qvalue**<br>--cfg: parsed from line **Output will be filtered at X FDR**       |
| ident_fdr_peptide        |      Not parsed as not an option       |
| ident_fdr_protein        |      Not parsed as not an option       | 
| enable_match_between_runs|      No --cfg: True if **--reanalyse** is set, else false<br>--cfg: True if **reanalyse them** (version <1.8) or **MBR enabled** (version >1.8) is mentioned       |
| precursor_mass_tolerance |      Value set for **--mass-acc-ms1**. If this parameter is not set, it means tolerance optimization<br>will be performed. In that case,as well as if --cfg is set, the value will be parsed from the first<br> occurence of the line **Recommended MS1 mass accuracy setting: X ppm**      |
| fragment_mass_tolerance  |      Value set for **--mass-acc**. If this parameter is not set, it means tolerance optimization will<br> be performed. In that case, as well as if --cfg is set, the value will be parsed from line <br>**Optimised mass accuracy: X ppm**      |
| enzyme                   |     No --cfg: value set for **--cut**<br>--cfg: parsed from line **In silico digest will involve cuts at X but excluding cuts at X**        |
| allowed_miscleavages     |     No --cfg: value set for **--missed-cleavages**<br>--cfg: parsed from line **Maximum number of missed cleavages set to X**        |
| min_peptide_length       |     No --cfg: value set for **--min-pep-len**<br>--cfg: parsed from the line **Min peptide length set to X**        |
| max_peptide_length       |     No --cfg: value set for **--max-pep-len**<br>--cfg: parsed from the line **Max peptide length set to X**        |
| fixed_mods               |     No --cfg: value set for **--mod**<br>--cfg: parsed from the lines **X enabled as a fixed modification** and **Modification X with mass<br> delta X at X will be considered as fixed        |
| variable_mods            |     No --cfg: value set for **--var-mod**<br>--cfg: parsed form line **Modification X with mass delta X at X will be considered as variable**        |
| max_mods                 |      No --cfg: value set for **var-mods**<br>--cfg: parsed from line **Maximum number of variable modifications set to X**       |
| min_precursor_charge     |      No --cfg: value set for **min-pr-charge**<br>--cfg: parsed from line **Min precursor charge set to X**      |
| max_precursor_charge     |      No --cfg: value set for **max-pr-charge**<br>--cfg: parsed from line **Max precursor charge set to X**      |
| quantification_method    |     No --cfg: either **Legacy** (if --direct-quant set), **QuantUMS high-accuracy if --high-acc set<br>or **QuantUMS high-precision (default)<br>--cfg: parsed from line **X quantification mode**       |
| protein_inference        |      No --cfg: value set for **--pg-level** or **no-prot-inf**, with the mapping {**0**: **Isoforms**, **1**: **Protein_names**, **2**: **Genes**}<br>--cfg: parsed from line **Implicit protein grouping: X**       |
| predictors_library       |      No --cfg: either **DIA-NN** if **--predictor** is set, or **User defined** if **--lib** is set to a path     |
| scan_window              |       Parsed from line **Scan window radius set to X**      |

### FragPipe
*Parsed parameter file: .workflow
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/fragpipe_older.workflow).*
| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Either FragPipe or FragPipe (DIA-NN quant), depending on input        |
| software_version         |      Parsed from header        |
| search_engine            |      MSFragger (fixed)       |
| search_engine_version    |      Parsed either from header or from MSFragger binary path       |
| ident_fdr_psm            |      If not DIA-NN quant, parsed from **phi-report.filter**<br>if DIA-NN quant, parsed from **diann.q-value**       |
| ident_fdr_peptide        |      If not DIA-NN quant, parsed from **phi-report.filter**<br>if DIA-NN quant, not parsed      |
| ident_fdr_protein        |      If not DIA-NN quant, parsed from **phi-report.filter**<br>if DIA-NN quant, parsed from **diann.q-value**       | 
| enable_match_between_runs|      If not DIA-NN quant, parsed from **ionquant.mbr**<br>if DIA-NN quant, parsed by checking if **--reanalyse** is present in diann.fragpipe.cmd-opts        |
| precursor_mass_tolerance |     Parsed from msfragger.precursor_mass_lower and msfragger.precursor_mass_upper        |
| fragment_mass_tolerance  |     Parsed from msfragger.fragment_mass_tolerance      |
| enzyme                   |     Parsed from msfragger.search_enzyme_name_1 and msfragger.search_enzyme_name_2        |
| allowed_miscleavages     |     Parsed from msfragger.allowed_missed_cleavage_1        |
| min_peptide_length       |     Parsed from msfragger.digest_min_length        |
| max_peptide_length       |     Parsed from msfragger.digest_max_length        |
| fixed_mods               |     Parsed from msfragger.table.fix-mods        |
| variable_mods            |     Parsed from msfragger.table.var-mods        |
| max_mods                 |     Parsed from msfragger.max_variable_mods_per_peptide        |
| min_precursor_charge     |     FragPipe uses charge state information from data, if present. <br>So this value is set to 1 by default, but overwritten using **msfragger.misc.fragger.precursor-charge-lo** if **msfragger.override_charge** is set to True        |
| max_precursor_charge     |     FragPipe uses charge state information from data, if present. <br>So this value is set to None by default, but overwritten using **msfragger.misc.fragger.precursor-charge-lo** if **msfragger.override_charge** is set to True        |
| quantification_method    |     If not DIA-NN quant, not parsed (TODO)<br>if DIA-NN quant, parsed from **diann.quantification-strategy**        |
| protein_inference        |     Parsed from protein-prophet.cmd-opts        |
| predictors_library       |     Not parsed        |
| scan_window              |     Not parsed        |

### i2MassChroQ
*Parsed parameter file: Project parameters.tsv
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/i2mq_result_parameters.tsv).*
| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      i2MassChroQ (fixed)       |
| software_version         |      Parsed from **i2MassChroQ_VERSION**       |
| search_engine            |      Parsed from **AnalysisSoftware_name**       |
| search_engine_version    |      Parsed from **AnalysisSoftware_version**       |
| ident_fdr_psm            |      Parsed from **psm_fdr**       |
| ident_fdr_peptide        |      Parsed from **peptide_fdr**       |
| ident_fdr_protein        |      Parsed from **protein_fdr**       | 
| enable_match_between_runs|      Parsed from **mcq_mbr**       |
| precursor_mass_tolerance |      Parsed from either **sage_precursor_tol** or **spectrum, parent monoisotopic mass error minus/plus**,<br> depending on search engine used       |
| fragment_mass_tolerance  |      Parsed from either **sage_fragment_tol** or **spectrum, fragment monoisotopic mass error minus/plus**,<br> depending on search engine used       |
| enzyme                   |      If Sage is used: parsed from **sage_database_enzyme_cleave_at**, **sage_data_enzyme_restrict**, **sage_database_enzyme_c_terminal**<br>if X!Tandem is used: parsed from **protein, cleavage site**       |
| allowed_miscleavages     |      Parsed from either **sage_database_enzyme_missed_cleavages** or **scoring, maximum missed cleavage sites**,<br> depending on search engine used       |
| min_peptide_length       |       Not parsed if X!Tandem is used <br> parsed from **sage_database_enzyme_min_len** if Sage is used      |
| max_peptide_length       |       Not parsed if X!Tandem is used <br> parsed from **sage_database_enzyme_max_len** if Sage is used      |
| fixed_mods               |       Parsed from either **sage_database_static_mods or **residue, modification mass**, depending on search engine used      |
| variable_mods            |       Parsed from either **sage_database_variable_mods** or **residue, potential modification mass**, depending on search engine used      |
| max_mods                 |       Not parsed if X!Tandem is used <br> parsed from **sage_database_max_variable_mods** if Sage is used      |
| min_precursor_charge     |       Not parsed if X!Tandem is used <br> parsed from **sage_precursor_charge** if Sage is used       |
| max_precursor_charge     |       Parsed from either **sage_precursor_charge** or **spectrum, maximum parent charge**, depending on search engine used      |
| quantification_method    |       Not parsed      |
| protein_inference        |       Not parsed      |
| predictors_library       |       Not parsed      |
| scan_window              |       Not parsed      |

### MaxQuant
*Parsed parameter file: mqpar.xml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/mqpar1.5.3.30_MBR.xml).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      MaxQuant (fixed)       |
| software_version         |      Parsed from **maxQuantVersion**       |
| search_engine            |      Andromeda (fixed)       |
| search_engine_version    |      Not parsed       |
| ident_fdr_psm            |      Parsed from **peptideFdr***       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Parsed from **proteinFdr**       | 
| enable_match_between_runs|      Parsed from **matchBetweenRuns**       |
| precursor_mass_tolerance |      Parsed from **mainSearchTol**       |
| fragment_mass_tolerance  |      Parsed from **MatchTolerance**       |
| enzyme                   |      Parsed from **\<enzymes>\<string\>**       |
| allowed_miscleavages     |      Parsed from **maxMissedCleavages**       |
| min_peptide_length       |      Parsed from **minPepLen** (version < 2.6) or **minPeptideLength** (version >= 2.6)       |
| max_peptide_length       |      Not parsed if not DIA, otherwise parsed from **maxPeptideLengthForUnspecificSearch**      |
| fixed_mods               |      Parsed from **fixedModifications**       |
| variable_mods            |      Parsed from **variableModifications**       |
| max_mods                 |      Parsed from **maxNmods**       |
| min_precursor_charge     |      Not parsed       |
| max_precursor_charge     |      Parsed from **maxCharge**       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

\*This may seem incorrect. However, when the setting **PSM FDR** is changed in the GUI, this affects the peptideFdr setting in the mqpar.xml.<br>There does not seem to be a peptide FDR setting in the GUI.

### MSAID*
*Parsed parameter file: experiment_details.csv
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/MSAID_default_params.csv)*.

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      MSAID (default)       |
| software_version         |      Not parsed       |
| search_engine            |      Parsed from **Algorithm**       |
| search_engine_version    |      Parsed from **Algorithm**       |
| ident_fdr_psm            |      0.01 (fixed)       |
| ident_fdr_peptide        |      0.01 (fixed)       |
| ident_fdr_protein        |      0.01 (fixed)       | 
| enable_match_between_runs|      True if **Quan in all file** or **MBR** is found in **quantification_method**      |
| precursor_mass_tolerance |      Not parsed       |
| fragment_mass_tolerance  |      Parsed from **Fragment Mass Tolerance**       |
| enzyme                   |      Parsed from **Enzyme**       |
| allowed_miscleavages     |      Parsed from **Max. Missed Cleavage Sites**       |
| min_peptide_length       |      Parsed from **Min. Peptide Length**       |
| max_peptide_length       |      Parsed from **Max. Peptide Length**       |
| fixed_mods               |      Parsed from **Static Modifications**       |
| variable_mods            |      Parsed from **Variable Modifications**       |
| max_mods                 |      Parsed from **Maximum Number of Modifications**       |
| min_precursor_charge     |      Parsed from **Min. Peptide Charge**       |
| max_precursor_charge     |      Parsed from **Max. Peptide Charge**       |
| quantification_method    |      Parsed from **Quantification Type**       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

*ProteoBench's compatibility with MSAID output is still a work in progress.

### MSAngel
*Parsed parameter file: .json
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/MSAngel_Xtandem-export-param.json).*


| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      MSAngel (fixed)       |
| software_version         |      Parsed from **msAngelVersion**       |
| search_engine            |      Parsed from **searchEnginesWithForms**       |
| search_engine_version    |      Not parsed       |
| ident_fdr_psm            |      Parsed from **psmExpectedFdr**       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Not parsed       | 
| enable_match_between_runs|      True (fixed)      |
| precursor_mass_tolerance |      Parsed from **TOL** and **TOLU** in the **paramMap** section if Mascot is used<br> Parsed from **precursorTolerance** and **precursorAccuracyType** in the **paramMap** section if X!Tandem is used       |
| fragment_mass_tolerance  |      Not parsed if Mascot is used<br>Parsed from **fragmentIonMZTolerance** and **fragmentAccuraccyType**  in the **paramMap** section if X!Tandem is used       |
| enzyme                   |      Parsed from **CLE** in the **paramMap** section if Mascot is used<br>Parsed from **enzymes** in **digestionParameters** in the **paramMap** section if X!Tandem is used       |
| allowed_miscleavages     |      Parsed from **PFA** in the **paramMap** section if Mascot is used<br>Parsed from **nMissedCleavages** in **digestionParameters** in the **paramMap** section if X!Tandem is used       |
| min_peptide_length       |      Not parsed       |
| max_peptide_length       |      Not parsed      |
| fixed_mods               |      Parsed from **MODS** in the **paramMap** section if Masscot is used<br>Parsed from **fixedModifications** in **modificationParameters** in the **paramMap** section if X!Tandem is used      |
| variable_mods            |      Parsed from **IT_MODS** in the **paramMap** section if Masscot is used<br>Parsed from **variableModifications** in **modificationParameters** in the **paramMap** section if X!Tandem is used.<br> Special parsing of the **data** section if proteinQuickAcetyl and/or quickPyrolidone are toggled       |
| max_mods                 |      Not parsed       |
| min_precursor_charge     |      Not parsed       |
| max_precursor_charge     |      Not parsed       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### PEAKS
*Parsed parameter file: parameters.txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/PEAKS_diaPASEF.txt).*
| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      PEAKS (fixed)       |
| software_version         |      Parsed from line **PEAKS Version: X**       |
| search_engine            |       PEAKS (fixed)      |
| search_engine_version    |      Parsed from line **PEAKS Version: X**       |
| ident_fdr_psm            |      Parsed from either **PSM FDR: X** or **Precusor FDR: X**       |
| ident_fdr_peptide        |      Parsed from line **Peptide FDR: X**       |
| ident_fdr_protein        |      Parsed from line **Protein Group FDR: X**       | 
| enable_match_between_runs|      Parsed from line **Match Between Run: X**      |
| precursor_mass_tolerance |      Parsed from line **Precursor Mass Error Tolerance: X**       |
| fragment_mass_tolerance  |      Parsed from line **Fragment Mass Error Tolerance: X**       |
| enzyme                   |      Parsed from line **Enzyme: X**       |
| allowed_miscleavages     |      Parsed from line **Max Missed Cleavage: X**       |
| min_peptide_length       |      Parsed from line **Peptide Length between: X** or **Peptide Length Range: X**       |
| max_peptide_length       |      Parsed from line **Peptide Length between: X** or **Peptide Length Range: X**     |
| fixed_mods               |      Parsed as the elements between **Fixed Modifications:** and **Variable Modifications**      |
| variable_mods            |      Parsed as the elements between **Variable Modifications:** and **Database:**       |
| max_mods                 |      Parsed from line **Max Variable PTM per Peptide: X**       |
| min_precursor_charge     |      Parsed from line **Precursor Charge between: X** or **Precursors Charge between: X**       |
| max_precursor_charge     |      Parsed from line **Precursor Charge between: X** or **Precursors Charge between: X**       |
| quantification_method    |      Parsed from line **LFQ Method: X**       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### ProlineStudio
*Parsed parameter file: .xlsx
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/ProlineStudio_241024.xlsx).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      ProlineStudio (fixed)       |
| software_version         |      If there is a **Dataset statistics and infos** sheet, it is parsed from **version**, otherwise not parsed       |
| search_engine            |      Parsed from **software_name** on **Search settings and infos** sheet       |
| search_engine_version    |      Parsed from **software_version** on **Search settings and infos** sheet       |
| ident_fdr_psm            |      Parsed from **psm_filter_expected_fdr** on **Import and filters** sheet       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Not parsed       | 
| enable_match_between_runs|      Set to true if **cross assignment** is present in the rows of the **Quant config** sheet, else False      |
| precursor_mass_tolerance |      Parsed from **peptide_mass_error_tolerance** on **Search settings and infos** sheet       |
| fragment_mass_tolerance  |      Parsed from **fragment_mass_error_tolerance** on **Search settings and infos** sheet       |
| enzyme                   |      Parsed from **enzymes** on **Search settings and infos** sheet       |
| allowed_miscleavages     |      Parsed from **max_missed_cleavages** on **Search settings and infos** sheet       |
| min_peptide_length       |      Parsed from **psm_filter_2** on **Import and filters** sheet       |
| max_peptide_length       |      Not parsed      |
| fixed_mods               |      Parsed from **fixed_ptms** on **Search settings and infos** sheet       |
| variable_mods            |      Parsed from **variable_ptms** on **Search settings and infos** sheet      |
| max_mods                 |      Not parsed       |
| min_precursor_charge     |      Parsed as the minimal charge state found in **peptide_charge_states** on **Search settings and infos** sheet       |
| max_precursor_charge     |      Parsed as the maximal charge state found in **peptide_charge_states** on **Search settings and infos** sheet       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### QuantMS 
*QuantMS requires three files to be uploaded: a json file, a yml file with version information and an optional sdrf file.
Example json [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/quantms_1-3_dev.json).
Example yml [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/quantms_1-3_test-versions.yml).
Example sdrf [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/quantms_1-3.sdrf_config.tsv).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      quantms (fixed)    |
| software_version         |      Parsed as the bigbio or nf-core/quantms version from the yml file       |
| search_engine            |      Parsed as a list of all the search engines found under the keys in the yml file that start with **SEARCHENGINE**      |
| search_engine_version    |      Parsed as a list of the versions of all the search engines under the keys in the yml file that start with **SEARCHENGINE**       |
| ident_fdr_psm            |      Parsed from **psm_level_fdr_cutoff** from the json file       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Parsed from **protein_level_fdr_cutoff** from the json file      | 
| enable_match_between_runs|      Not parsed      |
| precursor_mass_tolerance |      Parsed from **precursor_mass_tolerance** from the json file      |
| fragment_mass_tolerance  |      Parsed from **fragment_mass_tolerance** from the json file      |
| enzyme                   |      Parsed from **enzyme** from the json file       |
| allowed_miscleavages     |      Parsed from **allowed_missed_cleavages** from the json file       |
| min_peptide_length       |      Parsed from **min_peptide_length** from the json file       |
| max_peptide_length       |      Parsed from **max_peptide_length** from the json file     |
| fixed_mods               |      Parsed from **fixed_mods** from the json file      |
| variable_mods            |      Parsed from **variable_mods** from the json file       |
| max_mods                 |      Parsed from **max_mods** from the json file       |
| min_precursor_charge     |      Parsed from **min_precursor_charge** from the json file       |
| max_precursor_charge     |      Parsed from **max_precursor_charge** from the json file       |
| quantification_method    |      Parsed from **quantification_method** from the json file       |
| protein_inference        |      Parsed from **protein_inference_method** from the json file        |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### Sage
*Parsed parameter file: .json
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/sage_results.json).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Sage (fixed)      |
| software_version         |      Parsed from **version**       |
| search_engine            |      Sage (fixed)       |
| search_engine_version    |      Parsed from **version**       |
| ident_fdr_psm            |      Not parsed       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Not parsed       | 
| enable_match_between_runs|      True (fixed)      |
| precursor_mass_tolerance |      Parsed from **precursor_tol**       |
| fragment_mass_tolerance  |      Parsed from **fragment_tol**       |
| enzyme                   |      Parsed from **cleave_at** and **restrict** in the **database[enzyme]** section in the config       |
| allowed_miscleavages     |      Parsed from **missed_cleavages** in the **database[enzyme]** section in the config       |
| min_peptide_length       |      Parsed from **min_len** in the **database[enzyme]** section in the config       |
| max_peptide_length       |      Parsed from **max_len** in the **database[enzyme]** section in the config      |
| fixed_mods               |      Parsed from **static_mods** in the **database** section in the config      |
| variable_mods            |      Parsed from **variable_mods** in the **database** section in the config       |
| max_mods                 |      Parsed from **max_variable_mods** in the **database** section in the config       |
| min_precursor_charge     |      Parsed as first value from **precursor_charge** list       |
| max_precursor_charge     |      Parsed as last value from **precursor_charge** list       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed        |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### Spectronaut
*Parsed parameter file: .txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/spectronaut_Experiment1_ExperimentSetupOverview_BGS_Factory_Settings.txt).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Spectronaut (fixed)      |
| software_version         |     Parsed from first line        |
| search_engine            |     Spectronaut (fixed)        |
| search_engine_version    |     Parsed from first line        |
| ident_fdr_psm            |     Parsed from line **Precursor Qvalue Cutoff: X**        |
| ident_fdr_peptide        |     Not parsed        |
| ident_fdr_protein        |     Parsed from line **Protein Qvalue Cutoff: X**        | 
| enable_match_between_runs|     False (fixed)       |
| precursor_mass_tolerance |     Set to **Dynamic**, if the calibration method is set to **Dynamic**<br>If the calibration method is set to **Static** or **Relative**, tolerances are extracted from line **MS1 Tolerance: X**, with Th or ppm units, respectively       |
| fragment_mass_tolerance  |     Set to **Dynamic**, if the calibration method is set to **Dynamic**<br>If the calibration method is set to **Static** or **Relative**, tolerances are extracted from line **MS2 Tolerance: X**, with Th or ppm units, respectively        |
| enzyme                   |     Parsed from line **Enzymes / Cleavage Rules: X**        |
| allowed_miscleavages     |     Parsed from line **Missed Cleavages: X**        |
| min_peptide_length       |     Parsed from line **Min Peptide Length: X**        |
| max_peptide_length       |     Parsed from line **Max Peptide Length: X**       |
| fixed_mods               |     Parsed from line **Fixed Modifications: X**       |
| variable_mods            |     Parsed from line **Variable Modifications: X**        |
| max_mods                 |     Parsed from line **Max Variable Modifiations: X**        |
| min_precursor_charge     |     If Peptide Charge is set to False, not parsed<br>If not, parsed from line **Peptide Charge: X**        |
| max_precursor_charge     |     If Peptide Charge is set to False, not parsed<br>If not, parsed from line **Peptide Charge: X**        |
| quantification_method    |     Parsed from line **Quantity MS Level: X**        |
| protein_inference        |     Parsed from line **Inference Algorithm: X**        |
| predictors_library       |     Not parsed        |
| scan_window              |     Parsed from line **Cross-Run Normalization: X**        |

### Wombat
*Parsed parameter file: .yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/wombat_params.yaml).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Wombat (fixed)       |
| software_version         |       Parsed from **version**      |
| search_engine            |      various (fixed)       |
| search_engine_version    |      Not parsed       |
| ident_fdr_psm            |      Parsed from **ident_fdr_psm**       |
| ident_fdr_peptide        |      Parsed from **ident_fdr_peptide**       |
| ident_fdr_protein        |       Parsed from **ident_fdr_protein**      | 
| enable_match_between_runs|      Parsed from **enable_match_between_runs**      |
| precursor_mass_tolerance |       Parsed from **precursor_mass_tolerance**      |
| fragment_mass_tolerance  |      Parsed from **fragment_mass_tolerance**       |
| enzyme                   |     Parsed from **enzyme**        |
| allowed_miscleavages     |      Parsed from **miscleavages**       |
| min_peptide_length       |      Parsed from **min_peptide_length**       |
| max_peptide_length       |      Parsed from **max_peptide_length**      |
| fixed_mods               |     Parsed from **fixed_mods**       |
| variable_mods            |     Parsed from **variable_mods**       |
| max_mods                 |      Parsed from **max_mods**       |
| min_precursor_charge     |      Parsed from **min_precursor_charge**       |
| max_precursor_charge     |      Parsed from **max_precursor_charge**       |
| quantification_method    |      Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |
