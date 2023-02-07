import pandas as pd
import numpy as np
import itertools
import toml
import os
from proteobench.modules.dda_quant.io.parse import prepare_df

def get_quant(
        filtered_df,
        replicate_to_raw,
        species_dict
    ):

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
        cv_replicate_quant_df,
        species_quant_df,
        species_dict,
        replicate_mapper,
        species_expected_ratio
    ):

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

def get_cv(
        peptidoforms_replicate,
        alpha=1e-20
    ):

    return (np.std(peptidoforms_replicate)/(np.mean(peptidoforms_replicate)+alpha))*100


def get_vertical(
        filtered_df,
        replicate_mapper
    ):

    return len(set(filtered_df[filtered_df[list(replicate_mapper.keys())[0]] != 0]["peptidoform"]))

def main(
        input_csv: str,
        input_format: str,
        mbr: str,    
    ):

    dir_f = os.path.join(os.path.dirname(os.path.realpath(__file__)))
    # Parse user config        
    if input_format == "MaxQuant":
        df = pd.read_csv(input_csv,sep="\t",low_memory=False)
        parse_settings = toml.load(os.path.join(dir_f,"io/parse_settings_maxquant.toml"))
    elif input_format == "AlphaPept":
        df = pd.read_csv(input_csv,low_memory=False,sep="\t")
        parse_settings = toml.load(os.path.join(dir_f,"io/parse_settings_alphapept.toml"))
    elif input_format == "WOMBAT":
        df = pd.read_csv(input_csv,low_memory=False,sep=",")
        parse_settings = toml.load(os.path.join(dir_f,"io/parse_settings_wombat.toml"))

    print(parse_settings)
    mapper = parse_settings["mapper"]
    replicate_mapper = parse_settings["replicate_mapper"]
    decoy_flag = parse_settings["general"]["decoy_flag"]
    species_dict = parse_settings["species_dict"]
    contaminant_flag = parse_settings["general"]["contaminant_flag"]
    min_count_multispec = parse_settings["general"]["min_count_multispec"]
    species_expected_ratio = parse_settings["species_expected_ratio"]

    prepared_df, replicate_to_raw = prepare_df(
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

    return result_performance
    
