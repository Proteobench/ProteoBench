from __future__ import annotations

import datetime
import hashlib
import logging
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
    DDA_QUANT_RESULTS_REPO,
    ParseSettings,
)
from proteobench.modules.interfaces import ModuleInterface


class Module(ModuleInterface):
    """Object is used as a main interface with the Proteobench library within the module."""

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    @staticmethod
    def generate_intermediate_V2(
        filtered_df,
        replicate_to_raw: dict,
        parse_settings: ParseSettings,
        min_intensity=0,
        precursor="peptidoform",
    ) -> pd.DataFrame:
        # convert replicate_to_raw into dataframe where key values are in a column "Group" and values are in another column "Raw file"
        replicate_to_raw_df = pd.DataFrame(
            replicate_to_raw.items(), columns=["Group", "Raw file"]
        )
        # since there are several Raw files per Group we need to split them into different rows
        replicate_to_raw_df = replicate_to_raw_df.explode("Raw file")

        filtered_df_p1 = filtered_df[["Raw file", precursor, "Intensity"]].copy()
        # remove all rows where Intensity below min_intensity
        filtered_df_p1 = filtered_df_p1[filtered_df_p1["Intensity"] >= min_intensity]

        # add column "Group" to filtered_df_p1 using inner join on "Raw file"
        filtered_df_p1 = pd.merge(
            filtered_df_p1, replicate_to_raw_df, on="Raw file", how="inner"
        )

        # how many disinct combinations by row of distinct precursor, "Raw file" and "Group" in filtered_df_p1
        filtered_df_p1_check = filtered_df_p1[["Raw file", precursor, "Group"]].copy()
        filtered_df_p1_check = filtered_df_p1_check.drop_duplicates()
        filtered_df_p1_check = filtered_df_p1_check.shape[0]
        # sum intensity values of the same peptide and "Raw file" using the sum
        quant_raw_df_int = (
            filtered_df_p1.groupby([precursor, "Raw file", "Group"])["Intensity"]
            .agg(Intensity="sum", Count="size")
            .reset_index()
        )

        # pivot filtered_df_p1 to wide where index peptideform, columns Raw file and values Intensity

        intensities_wide = quant_raw_df_int.pivot(
            index=precursor, columns="Raw file", values="Intensity"
        ).reset_index()

        # add column "log_Intensity" to quant_raw_df
        quant_raw_df_int["log_Intensity"] = np.log2(quant_raw_df_int["Intensity"])
        # comopute the mean of the log_Intensity per precursor and "Group"
        quant_raw_df = (
            quant_raw_df_int.groupby([precursor, "Group"])
            .agg(
                log_Intensity_mean=("log_Intensity", "mean"),
                log_Intensity_std=("log_Intensity", "std"),
                Intensity_mean=("Intensity", "mean"),
                Intensity_std=("Intensity", "std"),
            )
            .reset_index()
        )

        # compute coefficient of variation (CV) of the log_Intensity_mean and log_Intensity_std
        quant_raw_df["CV"] = (
            quant_raw_df["Intensity_std"] / quant_raw_df["Intensity_mean"]
        )
        # pivot dataframe wider so for each Group variable there is a column with log_Intensity_mean, log_Intensity_std, Intensity_mean, Intensity_std and CV
        quant_raw_df = quant_raw_df.pivot(
            index="peptidoform",
            columns="Group",
            values=[
                "log_Intensity_mean",
                "log_Intensity_std",
                "Intensity_mean",
                "Intensity_std",
                "CV",
            ],
        ).reset_index()

        quant_raw_df.columns = [
            f"{x[0]}_{x[1]}" if len(str(x[1])) > 0 else x[0]
            for x in quant_raw_df.columns
        ]

        quant_raw_df["log2_A_vs_B"] = (
            quant_raw_df["log_Intensity_mean_A"] - quant_raw_df["log_Intensity_mean_B"]
        )
        quant_raw_df = pd.merge(
            quant_raw_df, intensities_wide, on="peptidoform", how="inner"
        )
        return quant_raw_df

    @staticmethod
    def generate_intermediate_V3(filtered_df, quant_df, parse_settings):
        species_peptidoform = list(parse_settings.species_dict.values())
        species_peptidoform.append("peptidoform")
        peptidoform_to_species = filtered_df[species_peptidoform].drop_duplicates()

        # merge dataframes quant_df and species_quant_df and peptidoform_to_species using pepdidoform as index
        withspecies = pd.merge(
            quant_df, peptidoform_to_species, on="peptidoform", how="inner"
        )
        species_expected_ratio = parse_settings.species_expected_ratio
        # for all columns named parse_settings.species_dict.values() compute the sum over the rows and add it to a new column "unique"
        withspecies["unique"] = withspecies[parse_settings.species_dict.values()].sum(
            axis=1
        )
        # create a list tabulating how many entries in withspecies["unique"] are 1,2,3,4,5,6
        unique_counts = withspecies["unique"].value_counts()

        # now remove all rows with withspecies["unique"] > 1
        withspecies = withspecies[withspecies["unique"] == 1]

        # for species in parse_settings.species_dict.values(), set all values in new column "species" to species if withe species is True
        for species in parse_settings.species_dict.values():
            withspecies.loc[withspecies[species] == True, "species"] = species
            withspecies.loc[
                withspecies[species] == True, "expectedRatio"
            ] = species_expected_ratio[species]["A_vs_B"]

        withspecies["epsilon"] = (
            withspecies["log2_A_vs_B"] - withspecies["expectedRatio"]
        )
        return withspecies

    def generate_intermediate(
        self, filtered_df, replicate_to_raw: dict, parse_settings: ParseSettings
    ) -> pd.DataFrame:
        res = Module.generate_intermediate_V2(
            filtered_df, replicate_to_raw, parse_settings
        )
        res = Module.generate_intermediate_V3(filtered_df, res, parse_settings)
        return res

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
            id=input_format + "_" + user_input["version"] + "_" + formatted_datetime,
            search_engine=input_format,
            software_version=user_input["version"],
            fdr_psm=user_input["fdr_psm"],
            fdr_peptide=user_input["fdr_peptide"],
            fdr_protein=user_input["fdr_protein"],
            MBR=user_input["mbr"],
            precursor_tol=user_input["precursor_mass_tolerance"],
            precursor_tol_unit=user_input["precursor_mass_tolerance_unit"],
            fragment_tol=user_input["fragment_mass_tolerance"],
            fragment_tol_unit=user_input["fragment_mass_tolerance_unit"],
            enzyme_name=user_input["search_enzyme_name"],
            missed_cleavages=user_input["allowed_missed_cleavage"],
            min_pep_length=user_input["min_peptide_length"],
            max_pep_length=user_input["max_peptide_length"],
            intermediate_hash=int(
                hashlib.sha1(intermediate.to_string().encode("utf-8")).hexdigest(), 16
            ),
        )
        result_datapoint.generate_id()
        result_datapoint.calculate_plot_data(intermediate)
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
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "MSFragger":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        elif input_format == "WOMBAT":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
            input_data_frame["proforma"] = input_data_frame["modified_peptide"]
        elif input_format == "Proline":
            input_data_frame = pd.read_excel(input_csv, sheet_name="Quantified peptide ions", header = 0, index_col = None)
        elif input_format == "Custom":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")

        return input_data_frame

    def add_current_data_point(self, all_datapoints, current_datapoint):
        """Add current data point to all data points and load them from file if empty. TODO: Not clear why is the df transposed here."""
        if not isinstance(all_datapoints, pd.DataFrame):
            # all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
            all_datapoints = read_results_json_repo(DDA_QUANT_RESULTS_REPO)

        all_datapoints["old_new"] = "old"
        all_datapoints = all_datapoints.T

        current_datapoint["old_new"] = "new"
        all_datapoints = pd.concat([all_datapoints, current_datapoint], axis=1)
        all_datapoints = all_datapoints.T.reset_index(drop=True)
        return all_datapoints

    def obtain_all_data_point(self, all_datapoints):
        """Add current data point to all data points and load them from file if empty. TODO: Not clear why is the df transposed here."""
        if not isinstance(all_datapoints, pd.DataFrame):
            # all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
            all_datapoints = read_results_json_repo(DDA_QUANT_RESULTS_REPO)

        all_datapoints["old_new"] = "old"

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
        return (
            intermediate_data_structure.fillna(0.0).replace([np.inf, -np.inf], 0),
            all_datapoints,
            input_df,
        )

    def check_new_unique_hash(self, datapoints):
        current_datapoint = datapoints[datapoints["old_new"] == "new"]
        all_datapoints_old = datapoints[datapoints["old_new"] == "old"]

        set_current_datapoint = set(list(current_datapoint["intermediate_hash"]))
        set_all_datapoints_old = set(list(all_datapoints_old["intermediate_hash"]))

        overlap = set_current_datapoint.intersection(set_all_datapoints_old)

        if len(overlap) > 0:
            st.error(
                f"The run you want to submit has been previously submitted \
                 under the identifier: {overlap}"
            )
            return False
        return True

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

        clone_repo(
            clone_dir=t_dir, token=token, remote_git=remote_git, username=username
        )
        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(None, current_datapoint)

        if not self.check_new_unique_hash(all_datapoints):
            return

        branch_name = current_datapoint["id"]

        path_write = os.path.join(t_dir, "results.json")
        logging.info(f"Writing the json to: {path_write}")
        f = open(path_write, "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        f.close()
        commit_message = f"Added new run with id {branch_name} \n user comments: {submission_comments}"

        pr_github(
            clone_dir=t_dir,
            token=token,
            remote_git=remote_git,
            username=username,
            branch_name=branch_name,
            commit_message=commit_message,
        )

    def write_json_local_development(self, temporary_datapoints):
        t_dir = TemporaryDirectory().name
        os.mkdir(t_dir)

        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(None, current_datapoint)

        # TODO write below to logger instead of std.out
        fname = os.path.join(t_dir, "results.json")
        logging.info(f"Writing the json to: {fname}")

        f = open(os.path.join(t_dir, "results.json"), "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        return os.path.join(t_dir, "results.json")

    def write_intermediate_raw(
        self, dir, ident, input_df, result_performance, param_loc
    ):
        path_write = os.path.join(dir, ident)
        try:
            os.mkdir(path_write)
        except:
            logging.warning(f"Could not make directory: {path_write}")

        outfile_param = open(os.path.join(path_write, "params.csv"), "w")
        outfile_param.write(str(param_loc.getvalue()))
        outfile_param.close()

        input_df.to_csv(os.path.join(path_write, "input_df.csv"))
        result_performance.to_csv(os.path.join(path_write, "result_performance.csv"))
