# Parameters parsed for public submission

We automatically retrieve the parameters used for a specific worklow run in the parameter file submitted next to the result. The parsing depends on the tool and are described below.

## General comments on the parameters that are retreived by ProteoBench

The parameters that are retrieve from the parameter files are the following:

- "software_name": name of the software tool.
- "software_version": version of the software tool used to generate the run.
- "search_engine": name of the search engine used for MS-based identification.
- "search_engine_version": version of the search engine.
- "ident_fdr_psm": target or obtained FDR at PSM level.
- "enable_match_between_runs": TRUE if match between run is enabled.
- "precursor_mass_tolerance": precursor mass tolerance used for identification (in the format "[-20 ppm, 20 ppm]").
- "fragment_mass_tolerance": fragment mass tolerance used for identification (in the format "[-50 ppm, 50 ppm]").
- "enzyme": enzyme used for digesting peptides.
- "allowed_miscleavages": number of maximum missed-cleavages allowed per peptide.
- "min_peptide_length": minimum peptide length considered in the analysis.
- "max_peptide_length": maximum peptide length considered in the analysis.
- "fixed_mods": list of fixed modifications (PTMs) considered in the analysis.
- "variable_mods": list of variable modifications (PTMs) considered in the analysis.
- "max_mods": maximum number of modifications per peptide considered in the analysis.
- "min_precursor_charge": minimum precursor charge considered in the analysis.
- "max_precursor_charge": maximum precursor charge considered in the analysis.
- "quantification_method": quantification method. This applies to software tools that offer different strategies for quantification.
- "protein_inference": 
- "predictors_library": lybrary used for the analysis in DIA. With the current module, we do not support experimentally generated libraries, but some software tools allow to use different in-silico-generated libraries.
- "abundance_normalization_ions":



## Tool-specific considerations

### alphaDIA

We give as "search_engine" the name "AlphaDIA". The "quantification_method" is set by default to "DirectLFQ", the "predictors_library" to "AlphaPeptDeep", and "enable_match_between_runs" to False.