from __future__ import annotations
import datetime
import re
import itertools
import pandas as pd
import toml
from proteobench.modules.dda_quant import parse_dda_id, parse_settings_dda_quant
from proteobench.modules.dda_quant.__metadata__ import Metadata
from proteobench.modules.dda_quant.parse_settings_dda_quant import ParseSettings
from proteobench.modules.dda_quant.parse_settings_dda_quant import DDA_QUANT_RESULTS_PATH
from dataclasses import asdict

def is_implemented() -> bool:
    """ Returns whether the module is fully implemented. """
    return True

def get_quant(
        filtered_df,
        replicate_to_raw:dict,
        parse_settings:ParseSettings
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ Take the generic format of data search output and convert it to get the quantification data (a tuple, the quantification measure and the reliability of it). """

    # Summarize values of the same peptide using mean
    quant_raw_df = filtered_df.groupby(["peptidoform","Raw file"]).mean()["Intensity"]
    quant_df = quant_raw_df.unstack(level=1)

    # Count number of values per peptidoform and Raw file

    for replicate, replicate_runs in replicate_to_raw.items():
        selected_replicate_df = quant_raw_df.index.get_level_values("Raw file").isin(replicate_runs)
        replicate_quant_df = quant_raw_df[selected_replicate_df]
        ## Add means of replicates
        mean_series = replicate_quant_df.groupby(["peptidoform"]).mean()
        # change indices of mean_series from peptidoform to multiindices containing peptidoform,replicate
        quant_df["mean_of_" + str(replicate)] = mean_series

        ## Add number of missing values per row of replicate
        missing_series = replicate_quant_df.isna().groupby(["peptidoform"]).sum()
        quant_df["missing_values_" + str(replicate)] = missing_series

    species_peptidoform = list(parse_settings.species_dict.keys())
    species_peptidoform.append("peptidoform")
    peptidoform_to_species = filtered_df[species_peptidoform].drop_duplicates()
    peptidoform_to_species.index = peptidoform_to_species["peptidoform"]
    peptidoform_to_species_dict = peptidoform_to_species.T.to_dict()

    species_quant_df = pd.DataFrame([peptidoform_to_species_dict[idx] for idx in quant_df.index])
    species_quant_df.set_index("peptidoform", drop = True, inplace = True)

    return species_quant_df,quant_df

def get_quant_ratios(
        quant_df:pd.DataFrame,
        species_quant_df:pd.DataFrame,
        parse_settings:ParseSettings
    ) -> pd.DataFrame:
    """ Calculate the quantification ratios and compare them to the expected ratios. """

    cv_replicate_quant_species_df = pd.concat([quant_df,species_quant_df],axis=1)

    ratio_dict = {}
    for species in parse_settings.species_dict.keys():
        species_df_slice = cv_replicate_quant_species_df[cv_replicate_quant_species_df[species] == True]
        for conditions in itertools.combinations(set(parse_settings.replicate_mapper.values()),2):
            condition_comp_id = "|".join(map(str,conditions))

            ratio = species_df_slice["mean_of_" + str(conditions[0])]/species_df_slice["mean_of_" + str(conditions[1])]
            ratio_diff = abs(ratio-parse_settings.species_expected_ratio[species][condition_comp_id])*100
            
            try:
                ratio_dict[condition_comp_id+"_ratio"] = pd.concat([ratio,ratio_dict[condition_comp_id+"_ratio"]])
                ratio_dict[condition_comp_id+"_expected_ratio_diff"] = pd.concat([ratio_dict[condition_comp_id+"_expected_ratio_diff"],ratio_diff])
            except KeyError:
                ratio_dict[condition_comp_id+"_ratio"] = ratio
                ratio_dict[condition_comp_id+"_expected_ratio_diff"] = ratio_diff
    ratio_df = pd.DataFrame(ratio_dict)

    result_performance = pd.concat([cv_replicate_quant_species_df,ratio_df],axis=1)

    return result_performance


def strip_sequence_wombat(seq:str) -> str:
    """ Remove parts of the peptide sequence that contain modifications. """
    return re.sub("([\(\[]).*?([\)\]])", "", seq)

def compute_metadata(
        result_performance:pd.DataFrame,
        input_format:str,
        user_input:dict
        ) -> Metadata:
    """ Method used to compute metadata for the provided result. """
    result_metadata = Metadata(
        id = input_format + "_" + user_input["version"] + "_" + str(datetime.datetime.now()),
        search_engine = input_format,
        software_version = user_input["version"],
        fdr_psm = user_input["fdr_psm"],
        fdr_peptide = user_input["fdr_peptide"],
        fdr_protein = user_input["fdr_protein"],
        MBR = user_input["mbr"],
        precursor_tol = user_input["precursor_mass_tolerance"],
        precursor_tol_unit = user_input["precursor_mass_tolerance_unit"],
        fragmnent_tol = user_input["fragment_mass_tolerance"],
        fragment_tol_unit = user_input["fragment_mass_tolerance_unit"],
        enzyme_name = user_input["search_enzyme_name"],
        missed_cleavages = user_input["allowed_missed_cleavage"], 
        min_pep_length = user_input["min_peptide_length"],
        max_pep_length = user_input["max_peptide_length"]
    )
    result_metadata.generate_id()
    result_metadata.calculate_plot_data(result_performance)
    #result_metadata.dump_json_object(json_dump_path)
    df = pd.Series(asdict(result_metadata))

    return df

def load_input_file(input_csv:str, input_format:str) -> pd.DataFrame:
    """ Method loads dataframe from a csv depending on its format."""
    input_data_frame:pd.DataFrame

    if input_format == "MaxQuant":
        input_data_frame = pd.read_csv(input_csv,sep="\t",low_memory=False)
    elif input_format == "AlphaPept":
        input_data_frame = pd.read_csv(input_csv,low_memory=False)
    elif input_format == "MSFragger":
        input_data_frame = pd.read_csv(input_csv,low_memory=False,sep="\t")
    elif input_format == "WOMBAT":
        input_data_frame = pd.read_csv(input_csv,low_memory=False,sep=",")
        input_data_frame["Sequence"] = input_data_frame["modified_peptide"].apply(strip_sequence_wombat)

    return input_data_frame

def load_data_points_from_repo():
    df = pd.read_json(DDA_QUANT_RESULTS_PATH)
    return df

def add_current_data_point(all_datapoints, current_datapoint):
    if (not isinstance(all_datapoints,pd.DataFrame)):
        all_datapoints = load_data_points_from_repo()
    else:
        all_datapoints = all_datapoints.T
    all_datapoints = pd.concat([all_datapoints, current_datapoint],axis=1)
    all_datapoints = all_datapoints.T.reset_index(drop=True)
    return all_datapoints

def benchmarking(
        input_file: str,
        input_format: str,
        user_input:dict,
        all_datapoints
    ) -> pd.DataFrame:
    """ Main workflow of the module. Used to benchmark workflow results. """

    # Parse user config
    input_df = load_input_file(input_file,input_format)
    parse_settings = parse_settings_dda_quant.ParseSettings(input_format)

    prepared_df, replicate_to_raw = parse_dda_id.prepare_df(
        input_df,
        parse_settings
    )

    #print(prepared_df.columns)

    # Get quantification data
    species_quant_df, quant_df = get_quant(
            prepared_df,
            replicate_to_raw,
            parse_settings
    )

    # Compute quantification ratios
    result_performance = get_quant_ratios(
                quant_df,
                species_quant_df,
                parse_settings
    )

    current_datapoint = compute_metadata(result_performance, input_format, user_input)
    all_datapoints = add_current_data_point(all_datapoints, current_datapoint)
    
    return result_performance, all_datapoints
