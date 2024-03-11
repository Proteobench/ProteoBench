from __future__ import annotations

import datetime
import hashlib
import logging
import os
import re
from collections import ChainMap
from dataclasses import asdict
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import streamlit as st

from proteobench.github.gh import clone_repo, pr_github, read_results_json_repo
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.params.alphapept import extract_params as extract_params_alphapept
from proteobench.io.params.fragger import extract_params as extract_params_fragger
from proteobench.io.params.maxquant import extract_params as extract_params_maxquant
from proteobench.io.params.proline import extract_params as extract_params_proline
from proteobench.io.params.sage import extract_params as extract_params_sage
from proteobench.modules.dda_quant_base.datapoint import Datapoint
from proteobench.modules.dda_quant_base.parse import (
    ParseInputs,
    aggregate_modification_column,
)
from proteobench.modules.dda_quant_base.parse_settings import (
    DDA_QUANT_RESULTS_REPO,
    PRECURSOR_NAME,
    ParseSettings,
)
from proteobench.modules.interfaces import ModuleInterface


class Module(ModuleInterface):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(self):
        self.dda_quant_results_repo = DDA_QUANT_RESULTS_REPO
        self.precursor_name = PRECURSOR_NAME

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    EXTRACT_PARAMS_DICT = {
        "MaxQuant": extract_params_maxquant,
        "Proline": extract_params_proline,
        "AlphaPept": extract_params_alphapept,
        "Sage": extract_params_sage,
        "FragPipe": extract_params_fragger,
    }

    @staticmethod
    def convert_replicate_to_raw(replicate_to_raw: dict) -> pd.DataFrame:
        """Converts replicate_to_raw dictionary into a dataframe."""
        replicate_to_raw_df = pd.DataFrame(replicate_to_raw.items(), columns=["Group", "Raw file"])
        replicate_to_raw_df = replicate_to_raw_df.explode("Raw file")
        return replicate_to_raw_df

    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
        replicate_to_raw: dict,
        parse_settings: ParseSettings,
    ) -> pd.DataFrame:
        # select columns which are relavant for the statistics
        # TODO, this should be handled different, probably in the parse settings
        relevant_columns_df = filtered_df[["Raw file", self.precursor_name, "Intensity"]].copy()
        replicate_to_raw_df = Module.convert_replicate_to_raw(replicate_to_raw)

        # add column "Group" to filtered_df_p1 using inner join on "Raw file"
        relevant_columns_df = pd.merge(relevant_columns_df, replicate_to_raw_df, on="Raw file", how="inner")

        quant_df = Module.compute_group_stats(
            relevant_columns_df,
            min_intensity=0,
            precursor=self.precursor_name,
        )

        species_prec_ion = list(parse_settings.species_dict.values())
        species_prec_ion.append(self.precursor_name)
        prec_ion_to_species = filtered_df[species_prec_ion].drop_duplicates()
        # merge dataframes quant_df and species_quant_df and prec_ion_to_species using pepdidoform as index
        quant_df_withspecies = pd.merge(quant_df, prec_ion_to_species, on=self.precursor_name, how="inner")
        species_expected_ratio = parse_settings.species_expected_ratio
        res = Module.compute_epsilon(quant_df_withspecies, species_expected_ratio)
        return res

    @staticmethod
    def compute_group_stats(
        relevant_columns_df: pd.DataFrame,
        min_intensity=0,
        precursor="precursor ion",
    ) -> pd.DataFrame:
        """Method used to precursor statistics, such as number of observations, CV, mean per group etc."""

        # fiter for min_intensity
        relevant_columns_df = relevant_columns_df[relevant_columns_df["Intensity"] > min_intensity]

        # TODO: check if this is still needed
        # sum intensity values of the same precursor and "Raw file" using the sum
        quant_raw_df_int = (
            relevant_columns_df.groupby([precursor, "Raw file", "Group"])["Intensity"]
            .agg(Intensity="sum", Count="size")
            .reset_index()
        )

        # add column "log_Intensity" to quant_raw_df
        quant_raw_df_int["log_Intensity"] = np.log2(quant_raw_df_int["Intensity"])

        # compute the mean of the log_Intensity per precursor and "Group"
        quant_raw_df_count = (quant_raw_df_int.groupby([precursor])).agg(nr_observed=("Raw file", "size"))

        # pivot filtered_df_p1 to wide where index peptide ion, columns Raw file and values Intensity

        intensities_wide = quant_raw_df_int.pivot(index=precursor, columns="Raw file", values="Intensity").reset_index()

        quant_raw_df = (
            quant_raw_df_int.groupby([precursor, "Group"])
            .agg(
                log_Intensity_mean=("log_Intensity", "mean"),
                log_Intensity_std=("log_Intensity", "std"),
                Intensity_mean=("Intensity", "mean"),
                Intensity_std=("Intensity", "std"),
                Sum=("Intensity", "sum"),
                nr_obs_group=("Intensity", "size"),
            )
            .reset_index()
        )

        # compute coefficient of variation (CV) of the log_Intensity_mean and log_Intensity_std
        quant_raw_df["CV"] = quant_raw_df["Intensity_std"] / quant_raw_df["Intensity_mean"]
        # pivot dataframe wider so for each Group variable there is a column with log_Intensity_mean, log_Intensity_std, Intensity_mean, Intensity_std and CV
        quant_raw_df = quant_raw_df.pivot(
            index=precursor,
            columns="Group",
            values=[
                "log_Intensity_mean",
                "log_Intensity_std",
                "Intensity_mean",
                "Intensity_std",
                "CV",
            ],
        ).reset_index()

        quant_raw_df.columns = [f"{x[0]}_{x[1]}" if len(str(x[1])) > 0 else x[0] for x in quant_raw_df.columns]

        quant_raw_df["log2_A_vs_B"] = quant_raw_df["log_Intensity_mean_A"] - quant_raw_df["log_Intensity_mean_B"]

        quant_raw_df = pd.merge(quant_raw_df, intensities_wide, on=precursor, how="inner")
        quant_raw_df = pd.merge(quant_raw_df, quant_raw_df_count, on=precursor, how="inner")
        return quant_raw_df

    @staticmethod
    def compute_epsilon(withspecies, species_expected_ratio):
        # for all columns named parse_settings.species_dict.values() compute the sum over the rows and add it to a new column "unique"
        withspecies["unique"] = withspecies[species_expected_ratio.keys()].sum(axis=1)

        # now remove all rows with withspecies["unique"] > 1
        withspecies = withspecies[withspecies["unique"] == 1]

        # for species in parse_settings.species_dict.values(), set all values in new column "species" to species if withe species is True
        for species in species_expected_ratio.keys():
            withspecies.loc[withspecies[species] == True, "species"] = species
            withspecies.loc[withspecies[species] == True, "log2_expectedRatio"] = np.log2(
                species_expected_ratio[species]["A_vs_B"]
            )

        withspecies["epsilon"] = withspecies["log2_A_vs_B"] - withspecies["log2_expectedRatio"]
        return withspecies

    @staticmethod
    def get_metrics(df, min_nr_observed=1):
        # compute mean of epsilon column in df
        # take abs value of df["epsilon"]
        # TODO use nr_missing to filter df before computing stats.
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        nr_prec = len(df_slice)
        # median abs unafected by outliers
        median_abs_epsilon = df_slice["epsilon"].abs().mean()
        # variance affected by outliers
        variance_epsilon = df_slice["epsilon"].var()
        # TODO more concise way to describe distribution of CV's
        cv_median = (df_slice["CV_A"].median() + df_slice["CV_B"].median()) / 2
        cv_q75 = (df_slice["CV_A"].quantile(0.75) + df_slice["CV_B"].quantile(0.75)) / 2
        cv_q90 = (df_slice["CV_A"].quantile(0.9) + df_slice["CV_B"].quantile(0.9)) / 2
        cv_q95 = (df_slice["CV_A"].quantile(0.95) + df_slice["CV_B"].quantile(0.95)) / 2

        return {
            min_nr_observed: {
                "median_abs_epsilon": median_abs_epsilon,
                "variance_epsilon": variance_epsilon,
                "nr_prec": nr_prec,
                "CV_median": cv_median,
                "CV_q90": cv_q90,
                "CV_q75": cv_q75,
                "CV_q95": cv_q95,
            }
        }

    def generate_datapoint(
        self, intermediate: pd.DataFrame, input_format: str, user_input: dict, default_cutoff_min_prec: int = 3
    ) -> Datapoint:
        """Method used to compute metadata for the provided result."""
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        if "comments_for_submission" not in user_input.keys():
            user_input["comments_for_submission"] = ""

        result_datapoint = Datapoint(
            id=input_format + "_" + user_input["software_version"] + "_" + formatted_datetime,
            software_name=input_format,
            software_version=user_input["software_version"],
            search_engine=user_input["search_engine"],
            search_engine_version=user_input["search_engine_version"],
            ident_fdr_psm=user_input["ident_fdr_psm"],
            ident_fdr_peptide=user_input["ident_fdr_peptide"],
            ident_fdr_protein=user_input["ident_fdr_protein"],
            enable_match_between_runs=user_input["enable_match_between_runs"],
            precursor_mass_tolerance=user_input["precursor_mass_tolerance"],
            fragment_mass_tolerance=user_input["fragment_mass_tolerance"],
            enzyme=user_input["enzyme"],
            allowed_miscleavages=user_input["allowed_miscleavages"],
            min_peptide_length=user_input["min_peptide_length"],
            max_peptide_length=user_input["max_peptide_length"],
            intermediate_hash=str(hashlib.sha1(intermediate.to_string().encode("utf-8")).hexdigest()),
            comments=user_input["comments_for_submission"],
        )

        result_datapoint.generate_id()
        results = dict(ChainMap(*[Module.get_metrics(intermediate, nr_observed) for nr_observed in range(1, 7)]))
        result_datapoint.results = results
        result_datapoint.median_abs_epsilon = result_datapoint.results[default_cutoff_min_prec]["median_abs_epsilon"]

        results_series = pd.Series(asdict(result_datapoint))

        return results_series

    def load_input_file(self, input_csv: str, input_format: str) -> pd.DataFrame:
        """Method loads dataframe from a csv depending on its format."""
        input_data_frame: pd.DataFrame

        if input_format == "MaxQuant":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "AlphaPept":
            input_data_frame = pd.read_csv(input_csv, low_memory=False)
        elif input_format == "Sage":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "FragPipe":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        elif input_format == "WOMBAT":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
            input_data_frame["proforma"] = input_data_frame["modified_peptide"]
        elif input_format == "Proline":
            input_data_frame = pd.read_excel(
                input_csv,
                sheet_name="Quantified peptide ions",
                header=0,
                index_col=None,
            )
            # TODO this should be generalized further, maybe even moved to parsing param in toml
            input_data_frame["modifications"].fillna("", inplace=True)
            input_data_frame["proforma"] = input_data_frame.apply(
                lambda x: aggregate_modification_column(x.sequence, x.modifications),
                axis=1,
            )
        elif input_format == "i2MassChroQ":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["ProForma"]
        elif input_format == "Custom":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["Modified sequence"]

        return input_data_frame

    def add_current_data_point(self, all_datapoints, current_datapoint):
        """Add current data point to all data points and load them from file if empty. TODO: Not clear why is the df transposed here."""
        if not isinstance(all_datapoints, pd.DataFrame):
            # all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
            all_datapoints = read_results_json_repo(self.dda_quant_results_repo)

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
            all_datapoints = read_results_json_repo(self.dda_quant_results_repo)

        all_datapoints["old_new"] = "old"

        return all_datapoints

    def benchmarking(
        self, input_file: str, input_format: str, user_input: dict, all_datapoints, default_cutoff_min_prec: int = 3
    ) -> pd.DataFrame:
        """Main workflow of the module. Used to benchmark workflow results."""

        # Parse user config
        input_df = self.load_input_file(input_file, input_format)
        parse_settings = ParseSettings(input_format)

        standard_format, replicate_to_raw = ParseInputs().convert_to_standard_format(input_df, parse_settings)

        # Get quantification data
        intermediate_data_structure = self.generate_intermediate(standard_format, replicate_to_raw, parse_settings)

        current_datapoint = self.generate_datapoint(
            intermediate_data_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
        )

        all_datapoints = self.add_current_data_point(all_datapoints, current_datapoint)

        # TODO check why there are NA and inf/-inf values
        return (
            intermediate_data_structure,
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
            overlap_name = all_datapoints_old.loc[all_datapoints_old["intermediate_hash"] == list(overlap)[0], "id"]

            st.error(
                f"The run you want to submit has been previously submitted \
                 under the identifier: {str(overlap_name)}"
            )
            return False
        return True

    def clone_pr(
        self,
        temporary_datapoints,
        datapoint_params,
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
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v
        current_datapoint["submission_comments"] = submission_comments

        all_datapoints = self.add_current_data_point(None, current_datapoint)

        if not self.check_new_unique_hash(all_datapoints):
            return False

        branch_name = current_datapoint["id"]

        path_write = os.path.join(t_dir, "results.json")
        logging.info(f"Writing the json to: {path_write}")
        f = open(path_write, "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        f.close()
        commit_message = f"Added new run with id {branch_name} \n user comments: {submission_comments}"

        pr_id = pr_github(
            clone_dir=t_dir,
            token=token,
            remote_git=remote_git,
            username=username,
            branch_name=branch_name,
            commit_message=commit_message,
        )

        return "https://" + remote_git.replace(".git", "") + "/pull/" + str(pr_id)

    def write_json_local_development(self, temporary_datapoints, datapoint_params):
        t_dir = TemporaryDirectory().name
        os.mkdir(t_dir)

        current_datapoint = temporary_datapoints.iloc[-1]

        # Update parameters based on parsed params
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v

        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(None, current_datapoint)

        # TODO write below to logger instead of std.out
        fname = os.path.join(t_dir, "results.json")
        logging.info(f"Writing the json to: {fname}")

        f = open(os.path.join(t_dir, "results.json"), "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        return os.path.join(t_dir, "results.json")

    def write_intermediate_raw(self, dir, ident, input_df, result_performance, param_loc):
        path_write = os.path.join(dir, ident)
        try:
            os.mkdir(path_write)
        except:
            logging.warning(f"Could not make directory: {path_write}")

        # TODO: save parameters file "locally" together with the raw and intermediate?
        outfile_param = open(os.path.join(path_write, "params.csv"), "w")
        outfile_param.write(str(param_loc.getvalue()))
        outfile_param.close()

        input_df.to_csv(os.path.join(path_write, "input_df.csv"))
        result_performance.to_csv(os.path.join(path_write, "result_performance.csv"))

    def load_params_file(self, input_file: list[str], input_format: str) -> ProteoBenchParameters:
        """Method loads parameters from a metadata file depending on its format."""
        # ! adapted to be able to parse more than one file.
        # ! how to ensure orrect order?
        params = self.EXTRACT_PARAMS_DICT[input_format](*input_file)
        params.software_name = input_format
        return params
