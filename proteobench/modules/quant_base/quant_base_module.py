from __future__ import annotations

import logging
import os
from tempfile import TemporaryDirectory
from typing import Any, Optional

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
from proteobench.io.params.alphadia import extract_params as extract_params_alphadia
from proteobench.io.params.alphapept import extract_params as extract_params_alphapept
from proteobench.io.params.diann import extract_params as extract_params_diann
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


class QuantModule:
    """
    Base Module for Quantification.

    Attributes
    ----------
    t_dir
        Temporary directory for the module.
    t_dir_pr
        Temporary directory for the pull request.
    github_repo
        Github repository for the module.
    precursor_name
        Level of quantification.

    """

    def __init__(self, token: str = None, proteobench_repo_name: str = "", proteobot_repo_name: str = ""):
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

        self.precursor_name = ""

    EXTRACT_PARAMS_DICT = {
        "MaxQuant": extract_params_maxquant,
        "ProlineStudio": extract_params_proline,
        "AlphaPept": extract_params_alphapept,
        "Sage": extract_params_sage,
        "FragPipe": extract_params_fragger,
        "i2MassChroQ": extract_params_i2masschroq,
        "DIA-NN": extract_params_diann,
        "AlphaDIA": extract_params_alphadia,
        "FragPipe (DIA-NN quant)": extract_params_fragger,
        # "Spectronaut": extract_params_spectronaut
    }

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    def add_current_data_point(
        self, current_datapoint: pd.Series, all_datapoints: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Add current data point to the data points from previous runs, load them from file if empty.

        Parameters
        ----------
        all_datapoints
            The data points from previous runs. If none, it will be loaded from the github repo.
        current_datapoint
            The current data point to be added.

        Returns
        -------
        pd.DataFrame
            All data points with the current data point added.
        """

        if not isinstance(all_datapoints, pd.DataFrame):
            all_datapoints = self.github_repo.read_results_json_repo()

        all_datapoints = all_datapoints.T

        current_datapoint["old_new"] = "new"

        # TODO: this doesn't work outside of the web interface, because the intermediate_hash is not present without the old datapoints. Temp fix with try except
        try:
            if current_datapoint["intermediate_hash"] not in all_datapoints.loc["intermediate_hash", :].values:
                all_datapoints.loc["old_new", :] = "old"
                all_datapoints_new = pd.concat([all_datapoints, current_datapoint], axis=1)
                all_datapoints_new = all_datapoints_new.T.reset_index(drop=True)
            else:
                all_datapoints_new = all_datapoints.T.reset_index(drop=True)
        except KeyError:  # if there is no intermediate_hash, because of local use
            all_datapoints_new = pd.concat([all_datapoints, current_datapoint], axis=1)
            all_datapoints_new = all_datapoints_new.T.reset_index(drop=True)

        return all_datapoints_new

    def obtain_all_data_points(self, all_datapoints: Optional[pd.DataFrame] = None):
        """
        Load all data points and load them from file if empty.

        Parameters
        ----------
        all_datapoints
            All data points. If none, it will be loaded from the github repo.

        Returns
        -------
        pd.DataFrame
            All data points.
        """

        if not isinstance(all_datapoints, pd.DataFrame):
            all_datapoints = self.github_repo.read_results_json_repo()

        all_datapoints["old_new"] = "old"

        return all_datapoints

    @staticmethod
    def filter_data_point(all_datapoints: pd.DataFrame, default_val_slider: int = 3):
        """
        Add current data point to all data points and load them from file if empty.

        Parameters
        ----------
        all_datapoints
            All data points.
        default_val_slider
            Default value for the slider.

        Returns
        -------
        pd.DataFrame
            All data points with the filtered data points.
        """
        print(all_datapoints)

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
        """
        Main workflow of the module. Used to benchmark workflow results.

        Parameters
        ----------
        input_file
            Path to the workflow output file.
        input_format
            Format of the workflow output file.
        user_input
            User provided parameters for plotting.
        all_datapoints
            DataFrame containing all datapoints from the proteobench repo.
        default_cutoff_min_prec
            Minimum number of runs an ion has to be identified in.

        Returns
        -------
        tuple[DataFrame, DataFrame, DataFrame]
            Tuple containing the intermediate data structure, all datapoints, and the input DataFrame.
        """

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

        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=all_datapoints)

        # TODO check why there are NA and inf/-inf values
        return (
            intermediate_data_structure,
            all_datapoints,
            input_df,
        )

    def check_new_unique_hash(self, datapoints: pd.DataFrame) -> bool:
        """
        Check if the new data point has a unique hash.

        Parameters
        ----------
        datapoints
            Data points.

        Returns
        -------
        bool
            Whether the new data point has a unique hash.
        """

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
        temporary_datapoints: pd.DataFrame,
        datapoint_params: Any,
        remote_git: str,
        submission_comments: str = "no comments",
    ):
        """
        Clone repo and open pull request.

        Parameters
        ----------
        temporary_datapoints
            Temporary data points.
        datapoint_params
            Data point parameters.
        remote_git
            Remote git.
        submission_comments
            Submission comments.

        Returns
        -------
        str
            URL of the pull request.
        """

        self.github_repo.clone_repo_pr()
        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v
        current_datapoint["submission_comments"] = submission_comments

        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=None)

        if not self.check_new_unique_hash(all_datapoints):
            logging.error("The run was previously submitted. Will not submit.")
            return False

        branch_name = current_datapoint["id"].replace(" ", "_").replace("(", "").replace(")", "")

        path_write = os.path.join(self.t_dir_pr, "results.json")
        logging.info(f"Writing the json to: {path_write}")
        f = open(path_write, "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        f.close()
        commit_name = f"Added new run with id {branch_name}"
        commit_message = f"User comments: {submission_comments}"

        try:
            self.github_repo.create_branch(branch_name)
            self.github_repo.commit(commit_name, commit_message)
            pr_id = self.github_repo.create_pull_request(commit_name, commit_message)
        except Exception as e:
            logging.error(f"Error in PR: {e}")
            return "Unable to create PR. Please check the logs."

        return "https://" + remote_git.replace(".git", "") + "/pull/" + str(pr_id)

    def write_json_local_development(self, temporary_datapoints: pd.DataFrame, datapoint_params: dict) -> str:
        """
        Write datapoints to json for local development.

        Parameters
        ----------
        temporary_datapoints
            Temporary data points.
        datapoint_params
            Data point parameters.

        Returns
        -------
        str
            Path to the json file.
        """

        os.mkdir(self.t_dir_pr)

        current_datapoint = temporary_datapoints.iloc[-1]

        # Update parameters based on parsed params
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v

        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=None)

        # TODO write below to logger instead of std.out
        fname = os.path.join(self.t_dir_pr, "results.json")
        logging.info(f"Writing the json to: {fname}")

        f = open(os.path.join(self.t_dir_pr, "results.json"), "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        return os.path.join(self.t_dir_pr, "results.json")

    def write_intermediate_raw(self, dir: str, ident: str, input_df: pd.DataFrame, result_performance, param_loc):
        """
        Write intermediate and raw data to a directory.

        Parameters
        ----------
        dir
            Directory to write to.
        ident
            Intermediate hash of the submission.
        input_df
            Input DataFrame.
        result_performance
            Result performance DataFrame.
        """

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
        """
        Method loads parameters from a metadata file depending on its format.

        Parameters
        ----------
        input_file
            Path to the metadata file.
        input_format
            Format of the metadata file.

        Returns
        -------
        ProteoBenchParameters
            Parameters for the module.
        """

        # ! adapted to be able to parse more than one file.
        # ! how to ensure orrect order?
        params = self.EXTRACT_PARAMS_DICT[input_format](*input_file)
        params.software_name = input_format
        return params
