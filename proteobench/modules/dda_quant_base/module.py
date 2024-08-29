from __future__ import annotations

import logging
import os
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import (
    Datapoint,
    filter_df_numquant_median_abs_epsilon,
    filter_df_numquant_nr_prec,
)
from proteobench.github.gh import GithubProteobotRepo
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.params.alphapept import extract_params as extract_params_alphapept
from proteobench.io.params.fragger import extract_params as extract_params_fragger
from proteobench.io.params.i2masschroq import (
    extract_params as extract_params_i2masschroq,
)
from proteobench.io.params.maxquant import extract_params as extract_params_maxquant
from proteobench.io.params.proline import extract_params as extract_params_proline
from proteobench.io.params.sage import extract_params as extract_params_sage
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.score.quant.quantscores import QuantScores


class Module:
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(
        self,
        token=None,
        proteobench_repo_name="Proteobench/Results_Module2_quant_DDA",
        proteobot_repo_name="Proteobot/Results_Module2_quant_DDA",
    ):
        self.t_dir = TemporaryDirectory().name
        self.t_dir_pr = TemporaryDirectory().name
        self.github_repo = GithubProteobotRepo(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            clone_dir=self.t_dir,
            clone_dir_pr=self.t_dir_pr,
        )
        self.github_repo.clone_repo()

        self.precursor_name = "precursor ion"

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    EXTRACT_PARAMS_DICT = {
        "MaxQuant": extract_params_maxquant,
        "Proline": extract_params_proline,
        "AlphaPept": extract_params_alphapept,
        "Sage": extract_params_sage,
        "FragPipe": extract_params_fragger,
        "i2MassChroQ": extract_params_i2masschroq,
    }

    def add_current_data_point(self, all_datapoints, current_datapoint):
        """Add current data point to all data points and load them from file if empty."""
        if not isinstance(all_datapoints, pd.DataFrame):
            # all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
            all_datapoints = self.github_repo.read_results_json_repo()

        all_datapoints["old_new"] = "old"
        all_datapoints = all_datapoints.T

        current_datapoint["old_new"] = "new"
        all_datapoints = pd.concat([all_datapoints, current_datapoint], axis=1)
        all_datapoints = all_datapoints.T.reset_index(drop=True)
        return all_datapoints

    def obtain_all_data_point(self, all_datapoints):
        """Add current data point to all data points and load them from file if empty."""
        if not isinstance(all_datapoints, pd.DataFrame):
            all_datapoints = self.github_repo.read_results_json_repo()

        all_datapoints["old_new"] = "old"

        return all_datapoints

    @staticmethod
    def filter_data_point(all_datapoints, default_val_slider: int = 3):
        """Add current data point to all data points and load them from file if empty."""
        all_datapoints["median_abs_epsilon"] = [
            filter_df_numquant_median_abs_epsilon(v, min_quant=default_val_slider) for v in all_datapoints["results"]
        ]

        all_datapoints["nr_prec"] = [
            filter_df_numquant_nr_prec(v, min_quant=default_val_slider) for v in all_datapoints["results"]
        ]

        return all_datapoints

    def benchmarking(
        self, input_file: str, input_format: str, user_input: dict, all_datapoints, default_cutoff_min_prec: int = 3
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """Main workflow of the module. Used to benchmark workflow results."""

        # Parse user config
        input_df = load_input_file(input_file, input_format)
        parse_settings = ParseSettingsBuilder().build_parser(input_format)
        standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

        # Get quantification data
        quant_score = QuantScores(
            self.precursor_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
        )
        intermediate_data_structure = quant_score.generate_intermediate(standard_format, replicate_to_raw)

        current_datapoint = Datapoint.generate_datapoint(
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
        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
        submission_comments="no comments",
    ):
        self.github_repo.clone_repo_pr()
        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v
        current_datapoint["submission_comments"] = submission_comments

        all_datapoints = self.add_current_data_point(None, current_datapoint)

        if not self.check_new_unique_hash(all_datapoints):
            logging.error("The run was previously submitted. Will not submit.")
            return False

        branch_name = current_datapoint["id"]

        path_write = os.path.join(self.t_dir, "results.json")
        logging.info(f"Writing the json to: {path_write}")
        f = open(path_write, "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        f.close()
        commit_message = f"Added new run with id {branch_name} \n user comments: {submission_comments}"

        try:
            self.github_repo.create_branch(branch_name)
            self.github_repo.commit(commit_message)
            pr_id = self.github_repo.create_pull_request(commit_message)
        except Exception as e:
            logging.error(f"Error in PR: {e}")
            return "Unable to create PR. Please check the logs."

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
        with open(os.path.join(path_write, "params.csv"), "w") as f:
            f.write(",\n".join(_file.getvalue().decode("utf-8") for _file in param_loc))

        input_df.to_csv(os.path.join(path_write, "input_df.csv"))
        result_performance.to_csv(os.path.join(path_write, "result_performance.csv"))

    def load_params_file(self, input_file: list[str], input_format: str) -> ProteoBenchParameters:
        """Method loads parameters from a metadata file depending on its format."""
        # ! adapted to be able to parse more than one file.
        # ! how to ensure orrect order?
        params = self.EXTRACT_PARAMS_DICT[input_format](*input_file)
        params.software_name = input_format
        return params
