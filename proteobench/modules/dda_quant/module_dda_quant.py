""" Main interface of the module."""

import os
import re
import itertools
import pandas as pd
import toml
from proteobench.modules.dda_quant import parse_dda_id, parse_settings_dda_quant
from proteobench.modules.dda_quant.__metadata__ import Metadata

def is_implemented() -> bool:
    """ Returns whether the module is fully implemented. """
    return True

def get_quant(
        filtered_df,
        replicate_to_raw:dict,
        species_dict
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ Take the generic format of data search output and convert it to get the quantification data (a tuple, the quantification measure and the reliability of it). """

    quant_df = filtered_df.groupby(["peptidoform","Raw file"]).mean()["Intensity"]
        
    replicate_quant_list = {}

    for replicate,replicate_runs in replicate_to_raw.items():
        selected_replicate_df = quant_df.index.get_level_values("Raw file").isin(replicate_runs)
        replicate_quant_df = quant_df[selected_replicate_df]
        
        cv_series = replicate_quant_df.groupby(["peptidoform"]).mean()
        replicate_quant_list[replicate] = cv_series
    
    cv_replicate_quant_df = pd.DataFrame(replicate_quant_list)

    species_peptidoform = list(species_dict.keys())
    species_peptidoform.append("peptidoform")
    peptidoform_to_species = filtered_df[species_peptidoform].drop_duplicates()
    peptidoform_to_species.index = peptidoform_to_species["peptidoform"]
    peptidoform_to_species_dict = peptidoform_to_species.T.to_dict()

    species_quant_df = pd.DataFrame([peptidoform_to_species_dict[idx] for idx in cv_replicate_quant_df.index])
    species_quant_df.set_index("peptidoform", drop = True, inplace = True)

    return species_quant_df,cv_replicate_quant_df

def get_quant_ratios(
        cv_replicate_quant_df:pd.DataFrame,
        species_quant_df:pd.DataFrame,
        species_dict:dict,
        replicate_mapper,
        species_expected_ratio
    ) -> pd.DataFrame:
    """ Calculate the quantification ratios and compare them to the expected ratios. """

    cv_replicate_quant_species_df = pd.concat([cv_replicate_quant_df,species_quant_df],axis=1)

    ratio_dict = {}
    for species in species_dict.keys():
        species_df_slice = cv_replicate_quant_species_df[cv_replicate_quant_species_df[species] == True]
        for conditions in itertools.combinations(set(replicate_mapper.values()),2):
            condition_comp_id = "|".join(map(str,conditions))

            ratio = species_df_slice[conditions[0]]/species_df_slice[conditions[1]]
            ratio_diff = abs(ratio-species_expected_ratio[species][condition_comp_id])*100
            
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


def main(
        input_csv: str,
        input_format: str
    ) -> pd.DataFrame:
    """ Main workflow of the module. Used to benchmark workflow results. """

    # Parse user config   
    parse_settings = toml.load(parse_settings_dda_quant.PARSE_SETTINGS_FILES[input_format])   
    if input_format == "MaxQuant":
        df = pd.read_csv(input_csv,sep="\t",low_memory=False)
        
    elif input_format == "AlphaPept":
        df = pd.read_csv(input_csv,low_memory=False,sep="\t")
    elif input_format == "MSFragger":
        df = pd.read_csv(input_csv,low_memory=False,sep="\t")
    elif input_format == "WOMBAT":
        df = pd.read_csv(input_csv,low_memory=False,sep=",")
        df["Sequence"] = df["modified_peptide"].apply(strip_sequence_wombat)

    print(parse_settings)
    mapper = parse_settings["mapper"]
    replicate_mapper = parse_settings["replicate_mapper"]
    decoy_flag = parse_settings["general"]["decoy_flag"]
    species_dict = parse_settings["species_dict"]
    contaminant_flag = parse_settings["general"]["contaminant_flag"]
    min_count_multispec = parse_settings["general"]["min_count_multispec"]
    species_expected_ratio = parse_settings["species_expected_ratio"]

    prepared_df, replicate_to_raw = parse_dda_id.prepare_df(
        df,
        mapper,
        replicate_mapper,
        decoy_flag,
        species_dict,
        contaminant_flag,
        min_count_multispec
    )

    print(prepared_df.columns)

    species_quant_df, cv_replicate_quant_df = get_quant(
            prepared_df,
            replicate_to_raw,
            species_dict
    )

    result_performance = get_quant_ratios(
                cv_replicate_quant_df,
                species_quant_df,
                species_dict,
                replicate_mapper,
                species_expected_ratio
    )

    _metadata = Metadata(
        id = 0,
        search_engine = input_format,
        software_version = 0,
        fdr_psm = 0,
        fdr_peptide = 0,
        fdr_protein = 0,
        MBR = False,
        precursor_tol = 0,
        precursor_tol_unit = "Da",
        fragmnent_tol = 0,
        fragment_tol_unit = "Da",
        enzyme_name = None,
        missed_cleavages = 0,
        min_pep_length = 0,
        max_pep_length = 0
    )
    _metadata.generate_id()
    _metadata.calculate_plot_data(result_performance)
    _metadata.dump_json_object("results.json")


    return result_performance
