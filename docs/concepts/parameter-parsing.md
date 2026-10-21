# Parameters parsed for public submission

ProteoBench automatically retrieves the parameters used for a workflow run from the parameter file
submitted alongside the results. Parsing depends on the tool, and is described below. If you have
suggestions or concerns about how a parameter is parsed, please
[open a GitHub issue](https://github.com/Proteobench/ProteoBench/issues).

```{admonition} Check your parameter file for personal information
:class: warning
Parameter files can embed file paths (FASTA location, raw data location, tool installation paths)
that may reveal a personal username or institutional directory structure. Review and sanitize
paths before submission.
```

A single-table overview of the parsing methodology for all supported tools is generated from this
page and available as
[`parsing_overview.tsv`](https://github.com/Proteobench/ProteoBench/tree/main/docs/parsing_overview.tsv).

## General comments on the parameters retrieved by ProteoBench

The parameters retrieved from parameter files for the **quantification (LFQ) modules** are:

| Parameter | Description |
|---|---|
| software_name | Name of the software tool. |
| software_version | Version of the software tool used to generate the run. |
| search_engine | Name of the search engine used for MS-based identification. Often the same as the software name, but relevant for workflows that allow multiple search engines (e.g. quantms). |
| search_engine_version | Version of the search engine. |
| ident_fdr_psm | Target or obtained FDR at PSM level. |
| ident_fdr_peptide | Target or obtained FDR at peptide level. |
| ident_fdr_protein | Target or obtained FDR at protein level. |
| enable_match_between_runs | TRUE if match between runs is enabled. |
| precursor_mass_tolerance | Precursor mass tolerance used for identification (format: `[-20 ppm, 20 ppm]`). |
| fragment_mass_tolerance | Fragment mass tolerance used for identification (format: `[-50 ppm, 50 ppm]`). |
| enzyme | Enzyme used for digesting peptides. |
| semi_enzymatic | TRUE if semi-specific (not fully enzymatic) digestion is allowed. |
| allowed_miscleavages | Maximum missed cleavages allowed per peptide. |
| min_peptide_length | Minimum peptide length considered. |
| max_peptide_length | Maximum peptide length considered. |
| fixed_mods | Fixed modifications (PTMs) considered. |
| variable_mods | Variable modifications (PTMs) considered. |
| max_mods | Maximum number of modifications per peptide. |
| min_precursor_charge | Minimum precursor charge considered. |
| max_precursor_charge | Maximum precursor charge considered. |
| min_precursor_mz | Minimum precursor m/z considered. |
| max_precursor_mz | Maximum precursor m/z considered. |
| min_fragment_mz | Minimum fragment m/z considered. |
| max_fragment_mz | Maximum fragment m/z considered. |
| quantification_method | Quantification method, for tools offering multiple strategies. |
| abundance_normalization_ions | Normalization applied to ion/precursor abundances prior to quantification (or a boolean/None where the tool only exposes an on/off switch). |
| protein_inference | Protein inference method. |
| predictors_library | Library used for DIA analysis. ProteoBench does not currently support experimentally generated libraries, but some tools allow different in-silico-generated libraries. |
| scan_window | Scan window settings. |

`min_precursor_mz`/`max_precursor_mz`/`min_fragment_mz`/`max_fragment_mz` and
`predictors_library`/`scan_window` are only meaningful for DIA workflows and are typically "Not
parsed" for DDA-only tools. `semi_enzymatic` is currently only defined in the DDA ion JSON schema
(`json/Quant/quant_lfq_DDA_ion.json`); the DIA schemas don't declare it, though a parser can still
set it dynamically as a plain Python attribute.

## Parameters that will never be parsed

Some submission-form fields can't be retrieved from any tool's parameter or log file, because they
capture information only the submitter knows. These are always left for manual entry, identical
across all modules and tools:

| Parameter | Description |
|---|---|
| postprocessing_performed | Whether any postprocessing (e.g. manual rescoring, custom filtering, merging of results) was applied after the search engine run. |
| postprocessing_description | Free-text description of the postprocessing performed, if any. |

## Tool-specific information

### AlphaDIA
*Parsed parameter file: log.txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/log_alphadia_1.txt).*

| Parameter                | Parsed value |
|--------------------------|-------|
| software_name            |    AlphaDIA (fixed)   |
| software_version         |   Parsed from the first **version** key-value line in the log    |
| search_engine            |    AlphaDIA (fixed)   |
| search_engine_version    |   Not parsed as no difference with software_version    |
| ident_fdr_psm            |   **fdr** setting in **fdr** section of the config    |
| ident_fdr_peptide        |   Not parsed as not an option    |
|ident_fdr_protein         |   **fdr** setting in **fdr** section of the config    |
| enable_match_between_runs|    Set to True if **mbr_step_enabled** is True, else False   |
| precursor_mass_tolerance |   **target_ms1_tolerance** setting in **search** section of the config, formatted as `[-X ppm, X ppm]`    |
| fragment_mass_tolerance  |   **target_ms2_tolerance** setting in **search** section of the config, formatted as `[-X ppm, X ppm]`   |
| enzyme                   |   **enzyme** setting in **library_prediction** section of the config   |
| semi_enzymatic           |   Not parsed   |
| allowed_miscleavages     |   **missed_cleavages** setting in **library_prediction** section of the config    |
| min_peptide_length       |   Minimum value in **precursor_len** setting in **library_prediction** section of the config.<br>Extraction auto-detects older (<1.10) vs newer (≥1.10) AlphaDIA log formats    |
| max_peptide_length       |    Maximum value in **precursor_len** setting, same version-aware extraction as min_peptide_length   |
| fixed_mods               |    **fixed_modifications** setting in **library_prediction** section, homogenized to ProForma-like notation (e.g. `Oxidation@M` → `M[Oxidation]`)   |
| variable_mods            |   **variable_modifications** setting in **library_prediction** section, homogenized to ProForma-like notation    |
| max_mods                 |    **max_var_mod_num** setting in **library_prediction** section of the config   |
| min_precursor_charge     |    Minimum value in **precursor_charge** setting, same version-aware extraction   |
| max_precursor_charge     |   Maximum value in **precursor_charge** setting, same version-aware extraction    |
| min_precursor_mz          |    Minimum value in **precursor_mz** setting in **library_prediction** section, same version-aware extraction   |
| max_precursor_mz          |    Maximum value in **precursor_mz** setting, same version-aware extraction   |
| min_fragment_mz          |    Minimum value in **fragment_mz** setting in **library_prediction** section, same version-aware extraction   |
| max_fragment_mz          |    Maximum value in **fragment_mz** setting, same version-aware extraction   |
| quantification_method    |    DirectLFQ (fixed)   |
| abundance_normalization_ions | **normalization_method** setting in the config; mapped to `DirectLFQ` if the value is `directlfq`, else left as-is |
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
| search_engine_version    |      Same as software_version       |
| ident_fdr_psm            |       **peptide_fdr** in **search** section of the config      |
| ident_fdr_peptide        |       Not parsed as not an option   |
| ident_fdr_protein        |      **protein_fdr** in **search** section of the config       |
| enable_match_between_runs|       **match** in **workflow** section of the config      |
| precursor_mass_tolerance |      **prec_tol** in **search** section of the config; unit is ppm if **ppm** flag (search section) is True, else Da; formatted as `[-X <unit>, X <unit>]`       |
| fragment_mass_tolerance  |      **frag_tol** in **search** section of the config, same unit logic as precursor_mass_tolerance       |
| enzyme                   |      **protease** in **fasta** section of the config; `trypsin` normalized to `Trypsin`       |
| semi_enzymatic           |      Not parsed       |
| allowed_miscleavages     |      **n_missed_cleavages** in **fasta** section of the config       |
| min_peptide_length       |      **pep_length_min** in **fasta** section of  the config       |
| max_peptide_length       |      **pep_length_max** in **fasta** section of the config       |
| fixed_mods               |       **mods_fixed** & **mods_fixed_terminal** & **mods_fixed_terminal_prot** in **fasta** section of the config;<br>known codes homogenized (e.g. `cC`→`C[Carbamidomethyl]`, `oxM`→`M[Oxidation]`, `a<^`→`N-term[Acetyl]`), others kept as-is      |
| variable_mods            |      **mods_variable** & **mods_variable_terminal** & **mods_variable_terminal_prot** in **fasta** section of the config; same homogenization as fixed_mods      |
| max_mods                 |      **n_modifications_max** in **fasta** section of the config       |
| min_precursor_charge     |      **iso_charge_min** in **features** section of the config       |
| max_precursor_charge     |      **iso_charge_max** in **features** section of the config       |
| quantification_method    |      **lfq_ratio_min**, **max_lfq** & **mode** in **quantification** section of the config (optional section), combined into a dict then flattened to a human-readable string       |
| abundance_normalization_ions | Fixed to `None` — AlphaPept has no normalization step |
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
| ident_fdr_protein        |      Not parsed as not an option (explicitly set to `None` when --cfg is used)       |
| enable_match_between_runs|      No --cfg: True if **--reanalyse** is set, else false<br>--cfg: True if **reanalyse them** (version <1.8) or **MBR enabled** (version >1.8) is mentioned       |
| precursor_mass_tolerance |      Value set for **--mass-acc-ms1**. If this parameter is not set, it means tolerance optimization<br>will be performed. In that case, as well as if --cfg is set, the value will be parsed from the first<br>occurence of the line **Recommended MS1 mass accuracy setting: X ppm**      |
| fragment_mass_tolerance  |      Value set for **--mass-acc**. If this parameter is not set, it means tolerance optimization will<br>be performed. In that case, as well as if --cfg is set, the value will be parsed from line<br>**Optimised mass accuracy: X ppm**      |
| enzyme                   |     No --cfg: value set for **--cut** (if absent entirely, defaults to `Trypsin/P`; a bare **--cut** flag with<br>no value means no-digestion mode → `No digestion`); `K*,R*`/`K*,R*,!P` normalized to `Trypsin/P`/`Trypsin`<br>--cfg: reconstructed from lines **In silico digest will involve cuts at X** and **But excluding cuts at X**,<br>then normalized the same way        |
| semi_enzymatic           |     Not parsed        |
| allowed_miscleavages     |     No --cfg: value set for **--missed-cleavages**<br>--cfg: parsed from line **Maximum number of missed cleavages set to X**        |
| min_peptide_length       |     No --cfg: value set for **--min-pep-len** (if not provided, default = 7)<br>--cfg: parsed from the line **Min peptide length set to X**        |
| max_peptide_length       |     No --cfg: value set for **--max-pep-len** (if not provided, default = 30)<br>--cfg: parsed from the line **Max peptide length set to X**        |
| fixed_mods               |     No --cfg: value set for **--mod**, plus any **--unimodN** command tokens (for DIA-NN ≥1.8 these are all<br>treated as fixed mods; for <1.8, `unimod4`/`unimod35` map specifically to fixed-Carbamidomethyl/<br>variable-Oxidation)<br>--cfg: parsed from the lines **X enabled as a fixed modification** and **Modification X with mass<br>delta X at X will be considered as fixed**<br>In both cases the raw value is homogenized to ProForma-like notation via a mapping table<br>(e.g. `unimod4`, `UniMod:4`, `Carbamidomethyl (C)` → `C[Carbamidomethyl]`)        |
| variable_mods            |     No --cfg: value set for **--var-mod**<br>--cfg: parsed from line **Modification X with mass delta X at X will be considered as variable**<br>Homogenized to ProForma-like notation via the same mapping table        |
| max_mods                 |      No --cfg: value set for **var-mods**<br>--cfg: parsed from line **Maximum number of variable modifications set to X**; defaults to `0`<br>if the line is not found       |
| min_precursor_charge     |      No --cfg: value set for **min-pr-charge** (if not provided, default = 1)<br>--cfg: parsed from line **Min precursor charge set to X**      |
| max_precursor_charge     |      No --cfg: value set for **max-pr-charge** (if not provided, default = 4)<br>--cfg: parsed from line **Max precursor charge set to X**      |
| min_precursor_mz          |  No --cfg: value set for **min-pr-mz** (if not provided, default = 300)<br>--cfg: parsed from line **Min precursor m/z set to X**      |
| max_precursor_mz          |  No --cfg: value set for **max-pr-mz** (if not provided, default = 1800)<br>--cfg: parsed from line **Max precursor m/z set to X**     |
| min_fragment_mz          |   No --cfg: value set for **min-fr-mz** (if not provided, default = 200)<br>--cfg: parsed from line **Min fragment m/z set to X**    |
| max_fragment_mz          |   No --cfg: value set for **max-fr-mz** (if not provided, default = 1800)<br>--cfg: parsed from line **Max fragment m/z set to X**    |
| quantification_method    |     No --cfg: either **Legacy** (if --direct-quant set), **QuantUMS high-accuracy** if --high-acc set,<br>or **QuantUMS high-precision** (default)<br>--cfg: parsed from line **X quantification mode** (last match used); defaults to `QuantUMS high-precision`<br>if not found       |
| abundance_normalization_ions | No --cfg: **--no-norm** → `None`; **--global-norm** → `Global normalization`; **--sig-norm** → `RT & signal-dep. normalization`;<br>otherwise `RT-dependent normalization`.\*<br>--cfg: additionally forced to `None` if the log contains **Normalisation disabled** |
| protein_inference        |      No --cfg: value set for **--pg-level** or **--no-prot-inf** (→ `Disabled`), with the mapping<br>{**0**: `Isoforms`, **1**: `Protein_names`, **2**: `Genes`}; defaults to `Genes` if unset<br>--cfg: parsed from line **Implicit protein grouping: X**, mapped via {isoform IDs, protein names, genes};<br>defaults to `Genes` if not matched       |
| predictors_library       |      No --cfg: either **DIA-NN** if **--predictor** is set, or **User defined speclib** if **--lib** is set to a path<br>--cfg: since --lib/--predictor aren't visible on the command line, falls back to the log body:<br>**Deep learning will be used to generate a new in silico spectral library** → DIA-NN;<br>a subsequent **Loading spectral library** line without that message → User defined speclib<br>Internally stored per RT/IM/MS2_int, flattened to a single string by post-processing     |
| scan_window              |       Parsed from line **Scan window radius set to X** (always taken from the log body, both with and<br>without --cfg)      |

\*The `--no-norm`/`--global-norm` checks currently use separate (non-`elif`) `if` statements in the parser, so the final unconditional check on `--sig-norm` can silently overwrite a `--no-norm`/`--global-norm` result unless `--sig-norm` is also present in the log — likely an unintentional bug worth fixing rather than documenting as intended behavior.

### FragPipe
*Parsed parameter file: .workflow
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/fragpipe_older.workflow).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Either FragPipe or FragPipe (DIA-NN quant), depending on input        |
| software_version         |      Parsed from **# FragPipe version** comment line if present; otherwise from the header line via regex `FragPipe \((\d+\.\d+.*)\)`        |
| search_engine            |      MSFragger (fixed)       |
| search_engine_version    |      Parsed from **# MSFragger version** comment line, or extracted from the MSFragger jar filename in **fragpipe-config.bin-msfragger** (regex `MSFragger-(.+)\.jar`)       |
| ident_fdr_psm            |      If not DIA-NN quant, parsed from **phi-report.filter**<br>if DIA-NN quant, parsed from **diann.q-value**       |
| ident_fdr_peptide        |      If not DIA-NN quant, parsed from **phi-report.filter**<br>if DIA-NN quant, not parsed      |
| ident_fdr_protein        |      If not DIA-NN quant, parsed from **phi-report.filter**<br>if DIA-NN quant, parsed from **diann.q-value**       |
| enable_match_between_runs|      If **quantitation.run-label-free-quant** is true, parsed from **ionquant.mbr**<br>if DIA-NN (**diann.run-dia-nn** true), true if **--reanalyse** appears in **diann.fragpipe.cmd-opts** or **diann.cmd-opts**, or if **diann.mbr** is true        |
| precursor_mass_tolerance |     Parsed from **msfragger.precursor_mass_lower** and **msfragger.precursor_mass_upper**; unit (ppm/Da) from **msfragger.precursor_mass_units**        |
| fragment_mass_tolerance  |     Parsed from **msfragger.fragment_mass_tolerance** (symmetric); unit (ppm/Da) from **msfragger.fragment_mass_units**      |
| enzyme                   |     Parsed from **msfragger.search_enzyme_name_1** and **msfragger.search_enzyme_name_2**; `stricttrypsin`→`Trypsin/P`, `trypsin`→`Trypsin`        |
| semi_enzymatic           |     Parsed from **msfragger.num_enzyme_termini** (True unless the value is `"2"`)        |
| allowed_miscleavages     |     Parsed from **msfragger.allowed_missed_cleavage_1**        |
| min_peptide_length       |     Parsed from **msfragger.digest_min_length**        |
| max_peptide_length       |     Parsed from **msfragger.digest_max_length**        |
| fixed_mods               |     Parsed from **msfragger.table.fix-mods**, converted to ProForma-like notation via a mass→name lookup table (falls back to the raw mass if unrecognized)        |
| variable_mods            |     Parsed from **msfragger.table.var-mods**, same ProForma conversion as fixed_mods (also handles peptide/protein N-term notations)        |
| max_mods                 |     Parsed from **msfragger.max_variable_mods_per_peptide**        |
| min_precursor_charge     |     FragPipe uses charge state information from data, if present. <br>So this value is set to 1 by default, but overwritten using **msfragger.misc.fragger.precursor-charge-lo** if **msfragger.override_charge** is set to True        |
| max_precursor_charge     |     FragPipe uses charge state information from data, if present. <br>So this value is set to None by default, but overwritten using **msfragger.misc.fragger.precursor-charge-hi** if **msfragger.override_charge** is set to True        |
| min_precursor_mz          |  Calculated by dividing the minimum peptide mass set for digestion (**msfragger.misc.fragger.digest-mass-lo**) by the maximum precursor charge |
| max_precursor_mz          |  Calculated by dividing the maximum peptide mass set for digestion (**msfragger.misc.fragger.digest-mass-hi**) by the minimum precursor charge     |
| min_fragment_mz          |   Not parsed    |
| max_fragment_mz          |   Not parsed    |
| quantification_method    |     If not DIA-NN quant, not parsed (TODO)<br>if DIA-NN quant, parsed from **diann.quantification-strategy**        |
| abundance_normalization_ions | If not DIA-NN quant, parsed from **ionquant.normalization**<br>if DIA-NN quant, not parsed        |
| protein_inference        |     If **protein-prophet.run-protein-prophet** is true, parsed from **protein-prophet.cmd-opts** (prefixed `"ProteinProphet: "`)        |
| predictors_library       |     If DIA-NN quant and **diann.library** is set, `"User defined speclib"`; if DIA-NN quant and unset, `"DIANN"`; otherwise not parsed        |
| scan_window              |     Not parsed        |

### i2MassChroQ
*Parsed parameter file: Project parameters.tsv
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/i2mq_result_parameters.tsv).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      i2MassChroQ (fixed)       |
| software_version         |      Parsed from **i2MassChroQ_VERSION**       |
| search_engine            |      Parsed from **AnalysisSoftware_name** (X!Tandem path normalizes `"X! "` → `"X!"`)       |
| search_engine_version    |      Parsed from **AnalysisSoftware_version**       |
| ident_fdr_psm            |      Parsed from **psm_fdr**       |
| ident_fdr_peptide        |      Parsed from **peptide_fdr**       |
| ident_fdr_protein        |      Parsed from **protein_fdr**       |
| enable_match_between_runs|      Parsed from **mcq_mbr**       |
| precursor_mass_tolerance |      Parsed from either **sage_precursor_tol** or **spectrum, parent monoisotopic mass error minus/plus**,<br> depending on search engine used       |
| fragment_mass_tolerance  |      Parsed from either **sage_fragment_tol** or **spectrum, fragment monoisotopic mass error**<br> (single symmetric value, not separate minus/plus), depending on search engine used       |
| enzyme                   |      If Sage is used: parsed from **sage_database_enzyme_cleave_at**, **sage_database_enzyme_restrict**, **sage_database_enzyme_c_terminal**<br>if X!Tandem is used: parsed from **protein, cleavage site**       |
| semi_enzymatic           |      If X!Tandem: parsed from **protein, cleavage semi**<br>if Sage: hardcoded `False` (the config's semi-enzymatic setting is not propagated)       |
| allowed_miscleavages     |      If X!Tandem: parsed from **scoring, maximum missed cleavage sites**, overridden by **refine, maximum missed cleavage sites** if **refine** = `"yes"`<br>if Sage: parsed from **sage_database_enzyme_missed_cleavages**       |
| min_peptide_length       |       Not parsed if X!Tandem is used <br> parsed from **sage_database_enzyme_min_len** if Sage is used      |
| max_peptide_length       |       Not parsed if X!Tandem is used <br> parsed from **sage_database_enzyme_max_len** if Sage is used      |
| fixed_mods               |       Parsed from either **sage_database_static_mods** or **residue, modification mass**, depending on search engine used; both converted to ProForma-like notation via a mapping table (falls back to raw token)      |
| variable_mods            |       Parsed from either **sage_database_variable_mods** or **residue, potential modification mass**, depending on search engine used, with same ProForma conversion.<br>For X!Tandem, also appends `Acetyl(N-term)` if **protein, quick acetyl** = `"yes"` and `Pyrolidone(N-term)` if **protein, quick pyrolidone** = `"yes"`      |
| max_mods                 |       Not parsed if X!Tandem is used <br> parsed from **sage_database_max_variable_mods** if Sage is used      |
| min_precursor_charge     |       Not parsed if X!Tandem is used <br> parsed from **sage_precursor_charge** if Sage is used       |
| max_precursor_charge     |       Parsed from either **sage_precursor_charge** or **spectrum, maximum parent charge**, depending on search engine used      |
| quantification_method    |       Not parsed      |
| abundance_normalization_ions | Parsed from **mcqr_normalization_method** (both X!Tandem and Sage paths)      |
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
| precursor_mass_tolerance |      Parsed from **mainSearchTol** (unit always ppm)       |
| fragment_mass_tolerance  |      Parsed from **MatchTolerance**; unit is ppm if **MatchToleranceInPpm** is true, otherwise Da       |
| enzyme                   |      Parsed from **\<enzymes>\<string\>**       |
| semi_enzymatic           |      Parsed from **enzymeMode** (False only if mode = 0, i.e. "Fully specific")       |
| allowed_miscleavages     |      Parsed from **maxMissedCleavages**       |
| min_peptide_length       |      Parsed from **minPepLen** (version < 2.6) or **minPeptideLength** (version >= 2.6)       |
| max_peptide_length       |      Not parsed (always `None`)†      |
| fixed_mods               |      Parsed from **fixedModifications**, converted to ProForma-like notation (expands multi-residue mods, e.g. `Phospho (STY)` → `S[Phospho], T[Phospho], Y[Phospho]`; terminal qualifiers kept as-is; falls back to a small mapping table for names like `Cys-Cys`/`Cysteinyl`)       |
| variable_mods            |      Parsed from **variableModifications**, same ProForma conversion as fixed_mods       |
| max_mods                 |      Parsed from **maxNmods**       |
| min_precursor_charge     |      Not parsed       |
| max_precursor_charge     |      Parsed from **maxCharge**       |
| min_precursor_mz          |  Not parsed |
| max_precursor_mz          |  Not parsed†     |
| min_fragment_mz          |   Not parsed    |
| max_fragment_mz          |   Not parsed    |
| quantification_method    |      Not parsed       |
| abundance_normalization_ions | Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

\*This may seem incorrect. However, when the setting **PSM FDR** is changed in the GUI, this affects the peptideFdr setting in the mqpar.xml.<br>There does not seem to be a peptide FDR setting in the GUI.

†Earlier versions of this parser derived `max_peptide_length` from **maxPeptideLengthForUnspecificSearch** for DIA runs, and calculated `max_precursor_mz` from **maxPeptideMass** divided by the minimum precursor charge. Both branches are absent from the current `maxquant.py`, so these two fields are unconditionally not parsed.

A separate `maxdia.py` parser exists that delegates to MaxQuant's parser (`extract_params_mq`) and adds MaxDIA-specific fields (DIA min/max peptide length, DIA min/max precursor charge, precursor/fragment tolerances, library type, quantification method). It is **not** currently registered in `QuantModule.EXTRACT_PARAMS_DICT`, so it is not selectable from the web interface or `make_submission()`; its module-level imports also reference `maxquant` directly rather than the fully qualified `proteobench.io.params.maxquant` path.

### MetaMorpheus
*MetaMorpheus requires two files: the search task settings TOML file and a plain-text version file (e.g. `allResults.txt`), uploaded in either order — `identify_file_type()` detects which is which.
Example TOML [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/metamorpheus_search_task_config.toml).
Example version file [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/metamorpheus_version_result.txt).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      MetaMorpheus (fixed)       |
| software_version         |      Parsed from the third whitespace-separated token of the version file's first line       |
| search_engine            |      MetaMorpheus (fixed)       |
| search_engine_version    |      Not parsed (explicitly set to `None`)       |
| ident_fdr_psm            |      Parsed from **CommonParameters.QValueThreshold**       |
| ident_fdr_peptide        |      Not parsed (explicitly set to `None`)       |
| ident_fdr_protein        |      Not parsed (explicitly set to `None`)       |
| enable_match_between_runs|      Parsed from **SearchParameters.MatchBetweenRuns**       |
| precursor_mass_tolerance |      Parsed from **CommonParameters.PrecursorMassTolerance** (e.g. `"±20.0000 PPM"`), formatted as `[-X ppm, X ppm]` or `[-X Da, X Da]`       |
| fragment_mass_tolerance  |      Parsed from **CommonParameters.ProductMassTolerance**, same formatting       |
| enzyme                   |      Parsed from **CommonParameters.DigestionParams.Protease**       |
| semi_enzymatic           |      Parsed from **CommonParameters.DigestionParams.FragmentationTerminus** (True unless the value is `"Both"`)       |
| allowed_miscleavages     |      Parsed from **CommonParameters.DigestionParams.MaxMissedCleavages**       |
| min_peptide_length       |      Parsed from **CommonParameters.DigestionParams.MinPeptideLength**       |
| max_peptide_length       |      Parsed from **CommonParameters.DigestionParams.MaxPeptideLength**       |
| fixed_mods               |      Parsed from **CommonParameters.ListOfModsFixed**, converted from MetaMorpheus's `"{mod} on {residue}"` format to ProForma-like notation (handles Pep/Prot N-/C-term qualifiers)       |
| variable_mods            |      Parsed from **CommonParameters.ListOfModsVariable**, same conversion as fixed_mods       |
| max_mods                 |      Parsed from **CommonParameters.DigestionParams.MaxModsForPeptide**       |
| min_precursor_charge     |      Parsed from **CommonParameters.PrecursorDeconvolutionParameters.MinAssumedChargeState**       |
| max_precursor_charge     |      Parsed from **CommonParameters.PrecursorDeconvolutionParameters.MaxAssumedChargeState**       |
| min_precursor_mz          |  Not parsed |
| max_precursor_mz          |  Not parsed     |
| min_fragment_mz          |   Not parsed    |
| max_fragment_mz          |   Not parsed    |
| quantification_method    |      FlashLFQ (fixed)       |
| abundance_normalization_ions | Parsed from **SearchParameters.Normalize** (bool)       |
| protein_inference        |      `Parsimony` if **SearchParameters.DoParsimony** is True, otherwise not parsed (`None`)       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

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
| semi_enzymatic           |      Parsed from **Enzyme Specificity** (True unless the value is `"full"`)       |
| allowed_miscleavages     |      Parsed from **Max. Missed Cleavage Sites**       |
| min_peptide_length       |      Parsed from **Min. Peptide Length**       |
| max_peptide_length       |      Parsed from **Max. Peptide Length**       |
| fixed_mods               |      Parsed from **Static Modifications**       |
| variable_mods            |      Parsed from **Variable Modifications**       |
| max_mods                 |      Parsed from **Maximum Number of Modifications**       |
| min_precursor_charge     |      Parsed from **Min. Peptide Charge**       |
| max_precursor_charge     |      Parsed from **Max. Peptide Charge**       |
| min_precursor_mz          |  Not parsed |
| max_precursor_mz          |  Not parsed     |
| min_fragment_mz          |   Not parsed    |
| max_fragment_mz          |   Not parsed    |
| quantification_method    |      Parsed from **Quantification Type**       |
| abundance_normalization_ions | Not parsed       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Parsed from **Prediction Model**       |
| scan_window              |      Not parsed       |

*ProteoBench's compatibility with MSAID output is still a work in progress.

### MSAngel
*Parsed parameter file: .json
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/MSAngel_Xtandem-export-param.json).*
(A Mascot-flavored example also exists at `test/params/MSAngel_fromRAWtoQUANT-Mascot-export-param.json` but is not currently linked from the docs.)

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      MSAngel (fixed)       |
| software_version         |      Parsed from **msAngelVersion**       |
| search_engine            |      Parsed from **searchEnginesWithForms**       |
| search_engine_version    |      Not parsed       |
| ident_fdr_psm            |      Parsed from **psmExpectedFdr** in **validationConfig** (divided by 100)       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Not parsed       |
| enable_match_between_runs|      True (fixed)      |
| precursor_mass_tolerance |      Parsed from **TOL** and **TOLU** in the **paramMap** section if Mascot is used<br> Parsed from **precursorTolerance** and **precursorAccuracyType** in the **paramMap** section if X!Tandem is used       |
| fragment_mass_tolerance  |      Not parsed if Mascot is used<br>Parsed from **fragmentIonMZTolerance** and **fragmentAccuracyType** in the **paramMap** section if X!Tandem is used       |
| enzyme                   |      Parsed from **CLE** in the **paramMap** section if Mascot is used (normalized to a canonical enzyme name)<br>Parsed from **enzymes** in **digestionParameters** in the **paramMap** section if X!Tandem is used (normalized to a canonical enzyme name)       |
| semi_enzymatic           |      Not parsed       |
| allowed_miscleavages     |      Parsed from **ERRORTOLERANT** in the **paramMap** section if Mascot is used\*<br>Parsed from **nMissedCleavages** in **digestionParameters** in the **paramMap** section if X!Tandem is used       |
| min_peptide_length       |      Not parsed       |
| max_peptide_length       |      Not parsed      |
| fixed_mods               |      Parsed from **MODS** in the **paramMap** section if Mascot is used<br>Parsed from **fixedModifications** in **modificationParameters** in the **paramMap** section if X!Tandem is used      |
| variable_mods            |      Parsed from **IT_MODS** in the **paramMap** section if Mascot is used<br>Parsed from **variableModifications** in **modificationParameters** in the **paramMap** section if X!Tandem is used.<br> Special parsing of the **data** section if proteinQuickAcetyl and/or quickPyrolidone are toggled       |
| max_mods                 |      Not parsed       |
| min_precursor_charge     |      Parsed from **CHARGE** in the **paramMap** section if Mascot is used<br>Parsed from **minChargeSearched** in the **paramMap** section if X!Tandem is used       |
| max_precursor_charge     |      Parsed from **CHARGE** in the **paramMap** section if Mascot is used<br>Parsed from **maxChargeSearched** in the **paramMap** section if X!Tandem is used       |
| quantification_method    |      Parsed from **quantMethod** type in the **quantitationConfig** section (both Mascot and X!Tandem)       |
| abundance_normalization_ions | Parsed from **quantitationConfig.lfqConfig.masterMapCreationConfig.normalizationMethod**       |
| protein_inference        |      Not parsed       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

\*For the Mascot path, the code first sets `allowed_miscleavages` from **PFA**, but a subsequent chained assignment immediately overwrites it with the **ERRORTOLERANT** flag value (also stored as a separate, undocumented `second_pass` field). The final stored value is therefore always the ERRORTOLERANT flag, not the PFA-derived value — this looks like an unintentional bug rather than intended behavior.

### PEAKS
*Parsed parameter file: parameters.txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/PEAKS_diaPASEF.txt).*
(Additional example variants also exist: `PEAKS_parameters.txt`, `PEAKS_parameters_DDA.txt`, `PEAKS_parameters_DDA_new.txt`, `PEAKS_parameters_DIA.txt`.)

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      PEAKS (fixed)       |
| software_version         |      Parsed from line **PEAKS Version: X**       |
| search_engine            |       PEAKS (fixed)      |
| search_engine_version    |      Parsed from line **PEAKS Version: X**       |
| ident_fdr_psm            |      Parsed from either **Precursor FDR: X** or **PSM FDR: X**       |
| ident_fdr_peptide        |      Parsed from line **Peptide FDR: X**       |
| ident_fdr_protein        |      Parsed from line **Protein Group FDR: X**       |
| enable_match_between_runs|      Parsed from line **Match Between Run: X**      |
| precursor_mass_tolerance |      Parsed from line **Precursor Mass Error Tolerance: X** (falls back to 40 ppm if the value is "System Default")       |
| fragment_mass_tolerance  |      Parsed from line **Fragment Mass Error Tolerance: X** (falls back to 40 ppm if the value is "System Default")       |
| enzyme                   |      Parsed from line **Enzyme: X**       |
| semi_enzymatic           |      Parsed from line **Digest Mode: X** (True unless the value is `"Specific"`)       |
| allowed_miscleavages     |      Parsed from line **Max Missed Cleavage: X**       |
| min_peptide_length       |      Parsed from line **Peptide Length between: X** or **Peptide Length Range: X**       |
| max_peptide_length       |      Parsed from line **Peptide Length between: X** or **Peptide Length Range: X**     |
| fixed_mods               |      Parsed as the elements between **Fixed Modifications:** and **Variable Modifications**      |
| variable_mods            |      Parsed as the elements between **Variable Modifications:** and **Database:**       |
| max_mods                 |      Parsed from line **Max Variable PTM per Peptide: X**       |
| min_precursor_charge     |      Parsed from line **Precursor Charge between: X** or **Charge between: X**       |
| max_precursor_charge     |      Parsed from line **Precursor Charge between: X** or **Charge between: X**       |
| min_precursor_mz          |  Parsed from line **Precursor M/Z between:** (DIA) |
| max_precursor_mz          |  Parsed from line **Precursor M/Z between:** (DIA)     |
| min_fragment_mz          |   Parsed from line **Fragment M/Z between:** (DIA)    |
| max_fragment_mz          |   Parsed from line **Fragment M/Z between:** (DIA)    |
| quantification_method    |      Parsed from line **LFQ Method: X**       |
| abundance_normalization_ions | Parsed from line **Normalization Method: X**       |
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
| semi_enzymatic           |      Not parsed       |
| allowed_miscleavages     |      Parsed from **max_missed_cleavages** on **Search settings and infos** sheet       |
| min_peptide_length       |      Parsed from **psm_filter_2** on **Import and filters** sheet       |
| max_peptide_length       |      Not parsed      |
| fixed_mods               |      Parsed from **fixed_ptms** on **Search settings and infos** sheet       |
| variable_mods            |      Parsed from **variable_ptms** on **Search settings and infos** sheet      |
| max_mods                 |      Not parsed       |
| min_precursor_charge     |      Parsed as the minimal charge state found in **peptide_charge_states** on **Search settings and infos** sheet       |
| max_precursor_charge     |      Parsed as the maximal charge state found in **peptide_charge_states** on **Search settings and infos** sheet       |
| quantification_method    |      Not parsed       |
| abundance_normalization_ions | Not parsed       |
| protein_inference        |      Parsed from the row containing **"peptides selection method"** on the **Quant config** sheet (lowercased); not parsed if that row is absent      |
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
| search_engine            |      Parsed as a list of all the search engines found under the keys in the yml file that start with **SEARCHENGINE** (only **comet** and **msgf** are currently recognized; any other engine name raises an error)      |
| search_engine_version    |      Parsed as a list of the versions of all the search engines under the keys in the yml file that start with **SEARCHENGINE**       |
| ident_fdr_psm            |      Parsed from **psm_level_fdr_cutoff** from the json file       |
| ident_fdr_peptide        |      Not parsed       |
| ident_fdr_protein        |      Parsed from **protein_level_fdr_cutoff** from the json file      |
| enable_match_between_runs|      Not parsed      |
| precursor_mass_tolerance |      Parsed from **precursor_mass_tolerance** (+ **precursor_mass_tolerance_unit**) from the json file      |
| fragment_mass_tolerance  |      Parsed from **fragment_mass_tolerance** (+ **fragment_mass_tolerance_unit**) from the json file      |
| enzyme                   |      Parsed from **enzyme** from the json file       |
| semi_enzymatic           |      Parsed from **num_enzyme_termini** from the json file (True if not equal to `"fully"`)     |
| allowed_miscleavages     |      Parsed from **allowed_missed_cleavages** from the json file       |
| min_peptide_length       |      Parsed from **min_peptide_length** from the json file       |
| max_peptide_length       |      Parsed from **max_peptide_length** from the json file     |
| fixed_mods               |      Parsed from **fixed_mods** from the json file      |
| variable_mods            |      Parsed from **variable_mods** from the json file       |
| max_mods                 |      Parsed from **max_mods** from the json file       |
| min_precursor_charge     |      Parsed from **min_precursor_charge** from the json file       |
| max_precursor_charge     |      Parsed from **max_precursor_charge** from the json file       |
| quantification_method    |      Parsed from **quantification_method** from the json file       |
| abundance_normalization_ions | Parsed from **normalize** from the json file (coerced to bool)   |
| protein_inference        |      Parsed from **protein_inference_method** from the json file        |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### Sage
*Parsed parameter file: .json
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/sage_results.json) (also `test/params/sage_parameterfile.json`).*

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
| semi_enzymatic           |      Parsed from **semi_enzymatic** in the **database[enzyme]** section in the config (bool; `null` → False)      |
| allowed_miscleavages     |      Parsed from **missed_cleavages** in the **database[enzyme]** section in the config       |
| min_peptide_length       |      Parsed from **min_len** in the **database[enzyme]** section in the config       |
| max_peptide_length       |      Parsed from **max_len** in the **database[enzyme]** section in the config (None if not set)      |
| fixed_mods               |      Parsed from **static_mods** in the **database** section in the config, mapped to ProForma-style mod names via a mass lookup table      |
| variable_mods            |      Parsed from **variable_mods** in the **database** section in the config, mapped to ProForma-style mod names via a mass lookup table       |
| max_mods                 |      Parsed from **max_variable_mods** in the **database** section in the config       |
| min_precursor_charge     |      Parsed as first value from **precursor_charge** list       |
| max_precursor_charge     |      Parsed as last value from **precursor_charge** list       |
| quantification_method    |      Parsed from **lfq_settings** in the **quant** section in the config       |
| abundance_normalization_ions | Not parsed       |
| protein_inference        |      Not parsed        |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

### Spectronaut
*Parsed parameter file: .txt
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/spectronaut_Experiment1_ExperimentSetupOverview_BGS_Factory_Settings.txt) (also `Spectronaut_dynamic.txt`, `Spectronaut_static.txt`, `Spectronaut_relative.txt`, one per calibration-method branch).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Spectronaut (fixed)      |
| software_version         |     Parsed from first line        |
| search_engine            |     Spectronaut (fixed)        |
| search_engine_version    |     Parsed from first line        |
| ident_fdr_psm            |     Parsed from line **Precursor Qvalue Cutoff: X**        |
| ident_fdr_peptide        |     Not parsed        |
| ident_fdr_protein        |     Parsed from line **Protein Qvalue Cutoff (Experiment): X**        |
| enable_match_between_runs|     False (fixed)       |
| precursor_mass_tolerance |     Set to **Dynamic**, if the calibration method is set to **Dynamic**<br>If the calibration method is set to **Static** or **Relative**, tolerances are extracted from line **MS1 Tolerance: X**, with Th or ppm units, respectively (resolved within the tolerance section matching the instrument's **Vendor**)       |
| fragment_mass_tolerance  |     Set to **Dynamic**, if the calibration method is set to **Dynamic**<br>If the calibration method is set to **Static** or **Relative**, tolerances are extracted from line **MS2 Tolerance: X**, with Th or ppm units, respectively        |
| enzyme                   |     Parsed from line **Enzymes / Cleavage Rules: X**        |
| semi_enzymatic           |     Parsed from line **Digest Type: X** (True unless the value is `"Specific"`)        |
| allowed_miscleavages     |     Parsed from line **Missed Cleavages: X**        |
| min_peptide_length       |     Parsed from line **Min Peptide Length: X**        |
| max_peptide_length       |     Parsed from line **Max Peptide Length: X**       |
| fixed_mods               |     Parsed from line **Fixed Modifications: X**       |
| variable_mods            |     Parsed from line **Variable Modifications: X**        |
| max_mods                 |     Parsed from line **Max Variable Modifications: X**        |
| min_precursor_charge     |     If Peptide Charge is set to False, not parsed<br>If not, parsed from line **Peptide Charge: X**        |
| max_precursor_charge     |     If Peptide Charge is set to False, not parsed<br>If not, parsed from line **Peptide Charge: X**        |
| min_precursor_mz          |  Not parsed |
| max_precursor_mz          |  Not parsed     |
| min_fragment_mz          |   Not parsed    |
| max_fragment_mz          |   Not parsed    |
| quantification_method    |     Parsed from line **Quantity MS Level: X**        |
| abundance_normalization_ions | Parsed from line **Cross-Run Normalization: X**       |
| protein_inference        |     Parsed from line **Inference Algorithm: X**        |
| predictors_library       |     Not parsed        |
| scan_window              |     Parsed from line **XIC IM Extraction Window: X**        |

### Wombat
*Parsed parameter file: .yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/wombat_params.yaml).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            |      Wombat (fixed)       |
| software_version         |       Parsed from **version**      |
| search_engine            |      various (fixed)       |
| search_engine_version    |      Not parsed (assignment present in source but commented out)       |
| ident_fdr_psm            |      Parsed from **ident_fdr_psm**       |
| ident_fdr_peptide        |      Parsed from **ident_fdr_peptide**       |
| ident_fdr_protein        |       Parsed from **ident_fdr_protein**      |
| enable_match_between_runs|      Parsed from **enable_match_between_runs**      |
| precursor_mass_tolerance |       Parsed from **precursor_mass_tolerance**      |
| fragment_mass_tolerance  |      Parsed from **fragment_mass_tolerance**       |
| enzyme                   |     Parsed from **enzyme** (title-cased to "Trypsin" if the value is "trypsin")        |
| semi_enzymatic           |     Not parsed        |
| allowed_miscleavages     |      Parsed from **miscleavages**       |
| min_peptide_length       |      Parsed from **min_peptide_length**       |
| max_peptide_length       |      Parsed from **max_peptide_length**      |
| fixed_mods               |     Parsed from **fixed_mods**       |
| variable_mods            |     Parsed from **variable_mods**       |
| max_mods                 |      Parsed from **max_mods**       |
| min_precursor_charge     |      Parsed from **min_precursor_charge**       |
| max_precursor_charge     |      Parsed from **max_precursor_charge**       |
| quantification_method    |      Parsed from **quantification_method**       |
| abundance_normalization_ions | Parsed from **normalization_method**       |
| protein_inference        |      Parsed from **protein_inference**       |
| predictors_library       |      Not parsed       |
| scan_window              |      Not parsed       |

## De novo sequencing tools

The `denovo_DDA_HCD` module uses a different, smaller set of parameter fields (defined in `proteobench/io/params/json/denovo/denovo_DDA_HCD.json`) than the quantification modules above:

| Parameter                | Description                                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------------------------|
| software_name            | Name of the software tool.                                                                                       |
| software_version         | Version of the software tool.                                                                                    |
| checkpoint               | Identifier of the model checkpoint used for prediction.                                                          |
| n_beams                  | Number of beams used in beam-search decoding (1 typically means greedy search).                                  |
| n_peaks                  | Number of peaks considered per spectrum.                                                                         |
| precursor_mass_tolerance | Precursor mass tolerance used for matching (unit as reported by the tool).                                       |
| min_peptide_length       | Minimum peptide length considered.                                                                                |
| max_peptide_length       | Maximum peptide length considered.                                                                                |
| min_mz / max_mz          | Minimum / maximum fragment m/z considered.                                                                        |
| min_intensity / max_intensity | Minimum / maximum peak intensity considered.                                                                 |
| tokens                   | The possible predicted tokens (amino acids and modifications known to the model).                                 |
| min_precursor_charge / max_precursor_charge | Minimum / maximum precursor charge allowed.                                                     |
| remove_precursor_tol     | Tolerance window around the precursor m/z within which peaks are removed before prediction.                       |
| isotope_error_range      | Allowed isotope error range (e.g. `"[0, 2]"`).                                                                     |
| decoding_strategy        | Decoding strategy used (e.g. "greedy search", "beam search").                                                     |

### AdaNovo
*Parsed parameter file: config.yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/denovo/adanovo/config.yaml).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            | AdaNovo (fixed) |
| checkpoint               | Not parsed |
| n_beams                  | Parsed from **n_beams** |
| n_peaks                  | Parsed from **n_peaks** |
| precursor_mass_tolerance | Parsed from **precursor_mass_tol** |
| min_peptide_length       | Parsed from **min_peptide_len** |
| max_peptide_length       | Parsed from **max_length** |
| min_mz / max_mz          | Parsed from **min_mz** / **max_mz** |
| min_intensity            | Parsed from **min_intensity** |
| max_intensity            | Not parsed |
| tokens                   | Joined keys of **residues** |
| min_precursor_charge     | Not parsed |
| max_precursor_charge     | Parsed from **max_charge** |
| remove_precursor_tol     | Parsed from **remove_precursor_tol** |
| isotope_error_range      | Parsed from **isotope_error_range** (stringified) |
| decoding_strategy        | `"greedy search"` if **n_beams** == 1, else `"beam search"` |

### Casanovo
*Parsed parameter file: casanovo.yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/denovo/casanovo/casanovo.yaml).*

Identical parsing logic to AdaNovo (same config keys: `n_beams`, `n_peaks`, `precursor_mass_tol`, `min_peptide_len`, `max_length`, `min_mz`, `max_mz`, `min_intensity`, `residues`, `max_charge`, `remove_precursor_tol`, `isotope_error_range`), with `software_name` fixed to `"Casanovo"`.

### ContraNovo
*Parsed parameter file: config.yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/denovo/contranovo/config.yaml).*

Same parsing logic as Casanovo/AdaNovo, with `software_name` fixed to `"ContraNovo"`, **except `min_peptide_length` is not parsed** (the `min_peptide_len` config key is not read by this parser, unlike AdaNovo/Casanovo).

### DeepNovo
*Not implemented.* `deepnovo.py`'s `extract_params()` is a stub (`pass`, no body) and returns `None`. Selecting DeepNovo as the input format would fail downstream since no `ProteoBenchParameters` object is produced.

### InstaNovo
*Parsed parameter file: config.yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/denovo/instanovo/config.yaml).*

| Parameter                | Parsed value |
|--------------------------|-------------|
| software_name            | InstaNovo (fixed) |
| checkpoint               | Parsed from **instanovo_model** |
| n_beams                  | Parsed from **num_beams** |
| n_peaks                  | Not parsed |
| precursor_mass_tolerance | Not parsed |
| min_peptide_length       | Not parsed |
| max_peptide_length       | Parsed from **max_length** |
| min_mz / max_mz          | Not parsed |
| min_intensity / max_intensity | Not parsed |
| tokens                   | Joined keys of **residue_remapping** |
| min_precursor_charge     | Not parsed |
| max_precursor_charge     | Parsed from **max_charge** |
| remove_precursor_tol     | Explicitly set to `None` (not present in InstaNovo's config) |
| isotope_error_range      | Parsed from **isotope_error_range** (stringified) |
| decoding_strategy        | `"greedy search"` if **num_beams** == 1, else `"beam search"` |

### Pi-HelixNovo
*Parsed parameter file: config.yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/denovo/pihelixnovo/config.yaml).*

Same config keys as AdaNovo (`n_beams`, `n_peaks`, `precursor_mass_tol`, `max_length`, `min_mz`, `max_mz`, `min_intensity`, `residues`, `max_charge`, `remove_precursor_tol`, `isotope_error_range`), with `software_name` fixed to `"Pi-HelixNovo"`. **`min_peptide_length` is not parsed** (the corresponding line is commented out in the parser). `decoding_strategy` is `"greedy search"` if the config's **decoding** field is `"greedy"`, else `"greedy search"` if **n_beams** == 1, else `"beam search"`.

### Pi-PrimeNovo
*Parsed parameter file: config.yaml
Example [here](https://github.com/Proteobench/ProteoBench/blob/main/test/params/denovo/piprimenovo/config.yaml).*

Same config keys as AdaNovo except `checkpoint` is parsed from **load_file_name**, and **`min_peptide_length` is not parsed** (commented out). `decoding_strategy` additionally reports mass-controlled decoding: if **PMC_enable** is true, appends `" + PMC [{mass_control_tol} Da]"` to `"beam search"`/`"greedy search"` depending on **n_beams**.

### PointNovo
*Not implemented.* `pointnovo.py`'s `extract_params()` is a stub (`pass`, no body) and returns `None`. Selecting PointNovo as the input format would fail downstream since no `ProteoBenchParameters` object is produced.
