"""
Quant Base Module.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
import zipfile
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import (
    QuantDatapoint,
    filter_df_numquant_epsilon,
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
from proteobench.io.params.msaid import extract_params as extract_params_msaid
from proteobench.io.params.msangel import extract_params as extract_params_msangel
from proteobench.io.params.peaks import read_peaks_settings as extract_params_peaks
from proteobench.io.params.proline import extract_params as extract_params_proline
from proteobench.io.params.quantms import extract_params as extract_params_quantms
from proteobench.io.params.sage import extract_params as extract_params_sage
from proteobench.io.params.spectronaut import (
    read_spectronaut_settings as extract_params_spectronaut,
)
from proteobench.io.params.wombat import extract_params as extract_params_wombat
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.score.quant.quantscores import QuantScores


class QuantModule:
    """
    Base Module for Quantification.

    Parameters
    ----------
    token : Optional[str]
        The GitHub token.
    proteobench_repo_name : str
        The name of the ProteoBench repository.
    proteobot_repo_name : str
        The name of the ProteoBot repository.
    parse_settings_dir : str
        The directory containing parse settings.
    module_id : str
        The module identifier for configuration.
    """

    EXTRACT_PARAMS_DICT: Dict[str, Any] = {
        "MaxQuant": extract_params_maxquant,
        "ProlineStudio": extract_params_proline,
        "MSAngel": extract_params_msangel,
        "AlphaPept": extract_params_alphapept,
        "Sage": extract_params_sage,
        "FragPipe": extract_params_fragger,
        "i2MassChroQ": extract_params_i2masschroq,
        "DIA-NN": extract_params_diann,
        "AlphaDIA": extract_params_alphadia,
        "FragPipe (DIA-NN quant)": extract_params_fragger,
        "MSAID": extract_params_msaid,
        "Spectronaut": extract_params_spectronaut,
        "PEAKS": extract_params_peaks,
        "WOMBAT": extract_params_wombat,
        # TODO needs to be replace with parameter extraction function
        "Proteome Discoverer": extract_params_spectronaut,
        "quantms": extract_params_quantms,
    }

    def __init__(
        self,
        token: Optional[str],
        proteobench_repo_name: str,
        proteobot_repo_name: str,
        parse_settings_dir: str,
        module_id: str,
    ):
        """
        Initialize the QuantModule with GitHub repo and settings.

        Parameters
        ----------
        token : Optional[str]
            The GitHub token.
        proteobench_repo_name : str
            The name of the ProteoBench repository.
        proteobot_repo_name : str
            The name of the ProteoBot repository.
        parse_settings_dir : str
            The directory containing parse settings.
        module_id : str
            The module identifier for configuration.
        """
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
        self.parse_settings_dir = parse_settings_dir

        self.precursor_column_name = ""
        self.module_id = module_id

    def is_implemented(self) -> bool:
        """
        Return whether the module is fully implemented.

        Returns
        -------
        bool
            Always returns True in this implementation.
        """
        return True

    def add_current_data_point(
        self, current_datapoint: pd.Series, all_datapoints: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Add current data point to previous data points. Load them from file if empty.

        Parameters
        ----------
        current_datapoint : pd.Series
            The current data point to add.
        all_datapoints : Optional[pd.DataFrame]
            Data points from previous runs. Loaded from GitHub repo if None.

        Returns
        -------
        pd.DataFrame
            A DataFrame with the current data point added.
        """
        if not isinstance(all_datapoints, pd.DataFrame):
            all_datapoints = self.github_repo.read_results_json_repo()

        all_datapoints = all_datapoints.T
        current_datapoint["old_new"] = "new"

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

    def obtain_all_data_points(self, all_datapoints: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Load all data points, load from file if empty.

        Parameters
        ----------
        all_datapoints : Optional[pd.DataFrame])
            All data points. Loaded from the GitHub repo if None.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing all data points.
        """
        if not isinstance(all_datapoints, pd.DataFrame):
            all_datapoints = self.github_repo.read_results_json_repo()

        all_datapoints["old_new"] = "old"

        return all_datapoints

    @staticmethod
    def filter_data_point(all_datapoints: pd.DataFrame, default_val_slider: int = 3) -> pd.DataFrame:
        """
        Filter the data points based on predefined criteria.

        Parameters
        ----------
        all_datapoints : pd.DataFrame
            All data points.
        default_val_slider : int, optional
            The minimum number of observations for filtering. Defaults to 3.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the filtered data points.
        """
        if len(all_datapoints) == 0:
            return all_datapoints

        all_datapoints["median_abs_epsilon"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider) for v in all_datapoints["results"]
        ]

        all_datapoints["mean_abs_epsilon"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, metric="mean")
            for v in all_datapoints["results"]
        ]

        all_datapoints["nr_prec"] = [
            filter_df_numquant_nr_prec(v, min_quant=default_val_slider) for v in all_datapoints["results"]
        ]

        return all_datapoints

    def benchmarking(
        self,
        input_file: str,
        input_format: str,
        user_input: dict,
        all_datapoints: Optional[pd.DataFrame],
        default_cutoff_min_prec: int = 3,
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """
        Main workflow of the module. Used to benchmark workflow results.

        Parameters
        ----------
        input_file : str
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        user_input : dict
            User-provided parameters for plotting.
        all_datapoints : Optional[pd.DataFrame]
            DataFrame containing all datapoints from the ProteoBench repo.
        default_cutoff_min_prec : int, optional
            Minimum number of runs a precursor ion has to be identified in. Defaults to 3.

        Returns
        -------
        tuple[DataFrame, DataFrame, DataFrame]
            A tuple containing the intermediate data structure, all data points, and the input DataFrame.
        """
        # Parse user config
        input_df = load_input_file(input_file, input_format)
        parse_settings = ParseSettingsBuilder(
            parse_settings_dir=self.parse_settings_dir, module_id=self.module_id
        ).build_parser(input_format)
        standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

        # Get quantification data
        quant_score = QuantScores(
            self.precursor_column_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
        )
        intermediate_metric_structure = quant_score.generate_intermediate(standard_format, replicate_to_raw)

        current_datapoint = QuantDatapoint.generate_datapoint(
            intermediate_metric_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
        )

        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=all_datapoints)

        return intermediate_metric_structure, all_datapoints, input_df

    def check_new_unique_hash(self, datapoints: pd.DataFrame) -> bool:
        """
        Check if the new data point has a unique hash.

        Parameters
        ----------
        datapoints : pd.DataFrame
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
                f"The run you want to submit has been previously submitted under the identifier: {str(overlap_name)}"
            )
            return False
        return True

    def clone_pr(
        self,
        temporary_datapoints: pd.DataFrame,
        datapoint_params: Any,
        remote_git: str,
        submission_comments: str = "no comments",
    ) -> str:
        """
        Clone the repo and open a pull request with the new data points.

        Parameters
        ----------
        temporary_datapoints : pd.DataFrame
            Temporary data points.
        datapoint_params : Any
            Data point parameters.
        remote_git : str
            Remote Git repository URL.
        submission_comments : str, optional
            Comments to be included in the pull request. Defaults to "no comments".

        Returns
        -------
        str
            The URL of the created pull request.
        """
        repo = self.github_repo.clone_repo_pr()

        current_datapoint = temporary_datapoints.iloc[-1]
        current_datapoint["is_temporary"] = False
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v

        # Generate the URL with the intermediate hash
        intermediate_hash = current_datapoint["intermediate_hash"]
        dataset_url = f"https://proteobench.cubimed.rub.de/datasets/{intermediate_hash}/"

        # Append the URL to the user comments
        submission_comments += f"\n\nDataset URL: {dataset_url}"
        current_datapoint["submission_comments"] = submission_comments

        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=None)

        if not self.check_new_unique_hash(all_datapoints):
            logging.error("The run was previously submitted. Will not submit.")
            return False

        # Create a new branch for the pull request with a unique branch name, this unique
        # branch name is important for batch resubmission to avoid clashes. We do guarentee
        # the same identifier name.
        hash_input = f"{datetime.now().isoformat()}_{uuid.uuid4()}".encode("utf-8")
        short_hash = hashlib.sha256(hash_input).hexdigest()[:10]  # First 10 hex characters

        branch_name = current_datapoint["id"].replace(" ", "_").replace("(", "").replace(")", "") + "_" + short_hash

        path_write_individual_point = os.path.join(self.t_dir_pr, current_datapoint["intermediate_hash"] + ".json")
        logging.info(f"Writing the json (single point) to: {path_write_individual_point}")
        with open(path_write_individual_point, "w") as f:
            json.dump(current_datapoint.to_dict(), f, indent=2)

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
        Write the datapoints to a JSON file for local development.

        Parameters
        ----------
        temporary_datapoints : pd.DataFrame
            Temporary data points.
        datapoint_params : dict
            Data point parameters.

        Returns
        -------
        str
            The path to the written JSON file.
        """

        # TODO: need to test if this still works...

        os.mkdir(self.t_dir_pr)

        current_datapoint = temporary_datapoints.iloc[-1]

        # Update parameters based on parsed params
        for k, v in datapoint_params.__dict__.items():
            current_datapoint[k] = v

        current_datapoint["is_temporary"] = False
        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=None)

        fname = os.path.join(self.t_dir_pr, "results.json")
        logging.info(f"Writing the json to: {fname}")

        f = open(os.path.join(self.t_dir_pr, "results.json"), "w")

        all_datapoints.to_json(f, orient="records", indent=2)

        return os.path.join(self.t_dir_pr, "results.json")

    def write_intermediate_raw(
        self,
        dir: str,
        ident: str,
        input_file_obj: Any,
        result_performance: pd.DataFrame,
        param_loc: List[Any],
        comment: str,
        extension_input_file: str = ".txt",
        extension_input_parameter_file: str = ".txt",
    ) -> None:
        """
        Write intermediate and raw data to a directory in zipped form.

        Parameters
        ----------
        dir : str
            Directory to write to.
        ident : str
            Identifier to create a subdirectory for this submission.
        input_file_obj : Any
            File-like object representing the raw input file.
        result_performance : pd.DataFrame
            The result performance DataFrame.
        param_loc : List[Any]
            List of paths to parameter files that need to be copied.
        comment : str
            User comment for the submission.
        """
        # Create the target directory
        path_write = os.path.join(dir, ident)
        try:
            os.makedirs(path_write, exist_ok=True)
        except OSError as e:
            msg = f"Could not create directory: {path_write}. Error: {e}"
            logging.warning(msg)

        # Create a zip file for all outputs
        zip_file_path = os.path.join(path_write, f"{ident}_data.zip")
        try:
            with zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Save the input file-like object content to the zip file
                input_file_obj.seek(0)
                zf.writestr(f"input_file{extension_input_file}", input_file_obj.read())

                # Save the result performance DataFrame as a CSV in the zip file
                result_csv = result_performance.to_csv(index=False)
                zf.writestr("result_performance.csv", result_csv)

                # Save parameter files in the zip file
                for i, _file in enumerate(param_loc):
                    _file.seek(0)
                    param_filename = f"param_{i}.{extension_input_parameter_file}"  # Adjust the extension if needed
                    zf.writestr(param_filename, _file.read())

                # Save the user comment in the zip file
                zf.writestr("comment.txt", comment)

            # save intermediate performance file unzipped as well
            result_csv_path = os.path.join(path_write, "result_performance.csv")
            result_csv.to_csv(result_csv_path, index=False)

            logging.info(f"Data saved to {zip_file_path}")
        except Exception as e:
            logging.error(f"Failed to create zip file at {zip_file_path}. Error: {e}")

    def load_params_file(self, input_file: List[str], input_format: str) -> ProteoBenchParameters:
        """
        Load parameters from a metadata file depending on its format.

        Parameters
        ----------
        input_file : List[str]
            Path to the metadata file.
        input_format : str
            Format of the metadata file.

        Returns
        -------
        ProteoBenchParameters
            The parameters for the module.
        """
        params = self.EXTRACT_PARAMS_DICT[input_format](*input_file)
        params.software_name = input_format
        return params
