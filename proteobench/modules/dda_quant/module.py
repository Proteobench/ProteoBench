from __future__ import annotations

import datetime
import itertools
import os
import re
from dataclasses import asdict
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import streamlit as st
from proteobench.github.gh import clone_repo, pr_github, read_results_json_repo
from proteobench.modules.dda_quant.datapoint import Datapoint
from proteobench.modules.dda_quant.parse import ParseInputs
from proteobench.modules.dda_quant.parse_settings import (
    DDA_QUANT_RESULTS_REPO, ParseSettings)
from proteobench.modules.interfaces import ModuleInterface


class Module(ModuleInterface):
    """Object is used as a main interface with the Proteobench library within the module."""

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    def generate_intermediate(
        self, filtered_df, replicate_to_raw: dict, parse_settings: ParseSettings
    ) -> pd.DataFrame:
        """Take the generic format of data search output and convert it to get the quantification data (a tuple, the quantification measure and the reliability of it)."""

        # Summarize values of the same peptide using mean
        # TODO should we take the mean or sum of the same peptidoform/peptideions same raw file multiple intensities
        quant_raw_df = filtered_df.groupby(["peptidoform", "Raw file"]).Intensity.mean()
        quant_df = quant_raw_df.unstack(level=1)

        # Count number of values per peptidoform and Raw file
        # TODO calculate this on the log2 transformed values
        for replicate, replicate_runs in replicate_to_raw.items():
            selected_replicate_df = quant_raw_df.index.get_level_values(
                "Raw file"
            ).isin(replicate_runs)
            replicate_quant_df = quant_raw_df[selected_replicate_df]
            ## Add means of replicates
            mean_series = replicate_quant_df.groupby(["peptidoform"]).mean()
            # change indices of mean_series from peptidoform to multiindices containing peptidoform,replicate
            quant_df["mean_of_" + str(replicate)] = mean_series

            ## Add number of missing values per row of replicate
            # TODO keep missing values, filter later for calculation of ratios
            missing_series = replicate_quant_df.isna().groupby(["peptidoform"]).sum()
            quant_df["missing_values_" + str(replicate)] = missing_series

        species_peptidoform = list(parse_settings.species_dict.values())
        species_peptidoform.append("peptidoform")
        # TODO check, do we need to drop_duplicates? When?
        peptidoform_to_species = filtered_df[species_peptidoform].drop_duplicates()
        peptidoform_to_species.index = peptidoform_to_species["peptidoform"]
        peptidoform_to_species_dict = peptidoform_to_species.T.to_dict()

        species_quant_df = pd.DataFrame(
            [peptidoform_to_species_dict[idx] for idx in quant_df.index]
        )
        species_quant_df.set_index("peptidoform", drop=True, inplace=True)

        """Calculate the quantification ratios and compare them to the expected ratios."""

        cv_replicate_quant_species_df = pd.concat([quant_df, species_quant_df], axis=1)

        ratio_dict = {}
        for species in parse_settings.species_dict.values():
            species_df_slice = cv_replicate_quant_species_df[
                cv_replicate_quant_species_df[species] == True
            ]
            # TODO add cutoffs for different thresholds presence of peptide ion
            # TODO do substraction for log2 transformed
            for conditions in itertools.combinations(
                set(parse_settings.replicate_mapper.values()), 2
            ):
                condition_comp_id = "|".join(map(str, conditions))

                ratio = (
                    species_df_slice["mean_of_" + str(conditions[0])]
                    / species_df_slice["mean_of_" + str(conditions[1])]
                )
                ratio_diff = (
                    abs(
                        ratio
                        - parse_settings.species_expected_ratio[species][
                            condition_comp_id
                        ]
                    )
                    * 100
                )

                # There is a loop that adds resulting ratios, if already
                # exists than concat to the existing DF, otherwise
                # keyexception and make df
                try:
                    ratio_dict[condition_comp_id + "_ratio"] = pd.concat(
                        [ratio, ratio_dict[condition_comp_id + "_ratio"]]
                    )
                    ratio_dict[condition_comp_id + "_expected_ratio_diff"] = pd.concat(
                        [
                            ratio_dict[condition_comp_id + "_expected_ratio_diff"],
                            ratio_diff,
                        ]
                    )
                except KeyError:
                    ratio_dict[condition_comp_id + "_ratio"] = ratio
                    ratio_dict[condition_comp_id + "_expected_ratio_diff"] = ratio_diff
        ratio_df = pd.DataFrame(ratio_dict)

        intermediate = pd.concat([cv_replicate_quant_species_df, ratio_df], axis=1)

        intermediate.rename(columns=parse_settings.run_mapper, inplace=True)

        return intermediate

    def strip_sequence_wombat(self, seq: str) -> str:
        """Remove parts of the peptide sequence that contain modifications."""
        return re.sub("([\(\[]).*?([\)\]])", "", seq)

    def generate_datapoint(
        self, intermediate: pd.DataFrame, input_format: str, user_input: dict
    ) -> Datapoint:
        """Method used to compute metadata for the provided result."""
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

    
        result_datapoint = Datapoint(
            id=input_format
            + "_"
            + user_input["version"]
            + "_"
            + formatted_datetime,
            search_engine=input_format,
            software_version=user_input["version"],
            fdr_psm=user_input["fdr_psm"],
            fdr_peptide=user_input["fdr_peptide"],
            fdr_protein=user_input["fdr_protein"],
            MBR=user_input["mbr"],
            precursor_tol=user_input["precursor_mass_tolerance"],
            precursor_tol_unit=user_input["precursor_mass_tolerance_unit"],
            fragmnent_tol=user_input["fragment_mass_tolerance"],
            fragment_tol_unit=user_input["fragment_mass_tolerance_unit"],
            enzyme_name=user_input["search_enzyme_name"],
            missed_cleavages=user_input["allowed_missed_cleavage"],
            min_pep_length=user_input["min_peptide_length"],
            max_pep_length=user_input["max_peptide_length"],
        )
        result_datapoint.generate_id()
        result_datapoint.calculate_plot_data(intermediate)
        # result_metadata.dump_json_object(json_dump_path)
        df = pd.Series(asdict(result_datapoint))

        return df

    def load_input_file(self, input_csv: str, input_format: str) -> pd.DataFrame:
        """Method loads dataframe from a csv depending on its format."""
        input_data_frame: pd.DataFrame

        if input_format == "MaxQuant":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "AlphaPept":
            input_data_frame = pd.read_csv(input_csv, low_memory=False)
        elif input_format == "Sage":
            input_data_frame = pd.read_csv(input_csv, sep='\t', low_memory=False)
        elif input_format == "MSFragger":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        elif input_format == "WOMBAT":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
            input_data_frame["Sequence"] = input_data_frame["modified_peptide"].apply(
                self.strip_sequence_wombat
            )
        elif input_format == "Proline":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        elif input_format == "Custom":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")


        return input_data_frame

    def add_current_data_point(self, all_datapoints, current_datapoint):
        """Add current data point to all data points and load them from file if empty. TODO: Not clear why is the df transposed here."""
        if not isinstance(all_datapoints, pd.DataFrame):
            #all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
            all_datapoints = read_results_json_repo(DDA_QUANT_RESULTS_REPO)
        
        all_datapoints["old_new"] = "old"
        all_datapoints = all_datapoints.T
        
        current_datapoint["old_new"] = "new"
        all_datapoints = pd.concat([all_datapoints, current_datapoint], axis=1)
        all_datapoints = all_datapoints.T.reset_index(drop=True)
        return all_datapoints

    def benchmarking(
        self, input_file: str, input_format: str, user_input: dict, all_datapoints
    ) -> pd.DataFrame:
        """Main workflow of the module. Used to benchmark workflow results."""

        # Parse user config
        input_df = self.load_input_file(input_file, input_format)
        parse_settings = ParseSettings(input_format)

        standard_format, replicate_to_raw = ParseInputs().convert_to_standard_format(
            input_df, parse_settings
        )

        # Get quantification data
        intermediate_data_structure = self.generate_intermediate(
            standard_format, replicate_to_raw, parse_settings
        )

        current_datapoint = self.generate_datapoint(
            intermediate_data_structure, input_format, user_input
        )

        all_datapoints = self.add_current_data_point(all_datapoints, current_datapoint)

        # TODO check why there are NA and inf/-inf values
        return intermediate_data_structure.fillna(0.0).replace([np.inf, -np.inf], 0), all_datapoints


    def clone_pr(
        self,
        temporary_datapoints,
        token,
        username="Proteobot",
        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
        branch_name="new_branch",
        submission_comments="no comments",
    ):
        t_dir = TemporaryDirectory().name

        clone_repo(clone_dir=t_dir, token=token, remote_git=remote_git, username=username)
        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(None, current_datapoint)
        branch_name = current_datapoint["id"]

        # do the pd.write_json() here!!!
        print(os.path.join(t_dir, "results.json"))
        f = open(os.path.join(t_dir, "results.json"), "w")
        
        all_datapoints.to_json(
            f,
            orient="records",
            indent=2
        )

        f.close()
        commit_message = f"Added new run with id {branch_name} \n user comments: {submission_comments}"

        pr_github(
            clone_dir=t_dir,
            token=token,
            remote_git=remote_git,
            username=username,
            branch_name=branch_name,
            commit_message=commit_message
        )


    def write_json_local_development(
        self, 
        temporary_datapoints
    ):  
        t_dir = TemporaryDirectory().name
        os.mkdir(t_dir)

        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(None, current_datapoint)

        # TODO write below to logger instead of std.out
        fname = os.path.join(t_dir, "results.json")
        print(f"Writing the json to: {fname}")

        f = open(os.path.join(t_dir, "results.json"), "w")
        
        all_datapoints.to_json(
            f,
            orient="records",
            indent=2
        )

        return os.path.join(t_dir, "results.json")
