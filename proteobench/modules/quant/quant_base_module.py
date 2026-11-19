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
from contextlib import contextmanager
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Type

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import (
    QuantDatapointHYE,
    filter_df_numquant_epsilon,
    filter_df_numquant_nr_feature,
)
from proteobench.exceptions import (
    ConvertStandardFormatError,
    DatapointAppendError,
    DatapointGenerationError,
    DatasetAlreadyExistsOnServerError,
    IntermediateFormatGenerationError,
    ParseError,
    ParseSettingsError,
    QuantificationError,
)
from proteobench.github.gh import GithubProteobotRepo
from proteobench.io.params import ProteoBenchParameters, normalize_dataframe_columns
from proteobench.io.params.alphadia import extract_params as extract_params_alphadia
from proteobench.io.params.alphapept import extract_params as extract_params_alphapept
from proteobench.io.params.diann import extract_params as extract_params_diann
from proteobench.io.params.fragger import extract_params as extract_params_fragger
from proteobench.io.params.i2masschroq import (
    extract_params as extract_params_i2masschroq,
)
from proteobench.io.params.maxquant import extract_params as extract_params_maxquant
from proteobench.io.params.metamorpheus import (
    extract_params as extract_params_metamorpheus,
    get_incomplete_upload_warning as validate_metamorpheus_files,
)
from proteobench.io.params.msaid import extract_params as extract_params_msaid
from proteobench.io.params.msangel import extract_params as extract_params_msangel
from proteobench.io.params.peaks import extract_params as extract_params_peaks
from proteobench.io.params.proline import extract_params as extract_params_proline
from proteobench.io.params.quantms import extract_params as extract_params_quantms
from proteobench.io.params.sage import extract_params as extract_params_sage
from proteobench.io.params.spectronaut import (
    read_spectronaut_settings as extract_params_spectronaut,
)
from proteobench.io.params.wombat import extract_params as extract_params_wombat
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.plotting.plot_generator_base import PlotGeneratorBase
from proteobench.plotting.plot_generator_lfq_HYE import LFQHYEPlotGenerator
from proteobench.score.quantscoresHYE import QuantScoresHYE


@contextmanager
def _benchmarking_step(error_type: Type[Exception], message: str):
    """
    Re-raise any exception from the wrapped step as ``error_type``, prefixed with ``message``.

    Parameters
    ----------
    error_type : Type[Exception]
        The ProteoBench exception the step's failures are reported as.
    message : str
        Prefix for the re-raised exception's message.

    Yields
    ------
    None
        Control to the wrapped benchmarking step.
    """
    try:
        yield
    except Exception as e:
        raise error_type(f"{message}: {e}") from e


class QuantModule:
    """
    Base Module for Quantification.

    A concrete module is configured entirely through class attributes; the pipeline in
    :meth:`benchmarking` is shared by all of them.

    Parameters
    ----------
    token : Optional[str]
        The GitHub token.
    proteobot_repo_name : str, optional
        The ProteoBot repository for pull requests. Defaults to ``Proteobot/<results_repo>``.
    proteobench_repo_name : str, optional
        The ProteoBench repository with public results. Defaults to ``Proteobench/<results_repo>``.
    branch : Optional[str]
        If set, check out this branch of the Proteobench repo after cloning.
        Useful for previewing a PR branch without merging.
    """

    # Maps format name to a function(files) -> str warning when the upload is incomplete.
    # Only formats that require multiple files need an entry here.
    VALIDATE_FILES_DICT: Dict[str, Any] = {
        "MetaMorpheus": validate_metamorpheus_files,
    }
    y_axis_title: str = "Total number of features quantified in the selected number of raw files"

    # Per-module configuration, overridden by the concrete module classes.
    module_id: str = ""
    results_repo: str = ""
    precursor_column_name: str = "precursor ion"
    score_cls: type = QuantScoresHYE
    datapoint_cls: type = QuantDatapointHYE
    plot_generator_cls: type = LFQHYEPlotGenerator
    default_cutoff_min_feature: int = 3
    max_nr_observed: Optional[int] = None

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
        "MetaMorpheus": extract_params_metamorpheus,
    }

    def __init__(
        self,
        token: Optional[str],
        proteobot_repo_name: Optional[str] = None,
        proteobench_repo_name: Optional[str] = None,
        branch: Optional[str] = None,
    ):
        """
        Initialize the module: clone its results repository and locate its parse settings.

        Parameters
        ----------
        token : Optional[str]
            The GitHub token.
        proteobot_repo_name : str, optional
            The ProteoBot repository for pull requests. Defaults to ``Proteobot/<results_repo>``.
        proteobench_repo_name : str, optional
            The ProteoBench repository with public results. Defaults to ``Proteobench/<results_repo>``.
        branch : Optional[str]
            If set, check out this branch of the Proteobench repo after cloning.
        """
        self.t_dir = TemporaryDirectory().name
        self.t_dir_pr = TemporaryDirectory().name
        self.github_repo = GithubProteobotRepo(
            token,
            proteobot_repo_name=proteobot_repo_name or f"Proteobot/{self.results_repo}",
            proteobench_repo_name=proteobench_repo_name or f"Proteobench/{self.results_repo}",
            clone_dir=self.t_dir,
            clone_dir_pr=self.t_dir_pr,
            branch=branch,
        )
        self.github_repo.clone_repo()
        self.parse_settings_dir = MODULE_SETTINGS_DIRS[self.module_id]

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

        all_datapoints = normalize_dataframe_columns(all_datapoints)
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

        # Add new metric columns with mode suffixes
        all_datapoints["median_abs_epsilon_global"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, mode="global")
            for v in all_datapoints["results"]
        ]

        all_datapoints["mean_abs_epsilon_global"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, metric="mean", mode="global")
            for v in all_datapoints["results"]
        ]

        all_datapoints["median_abs_epsilon_eq_species"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, mode="eq_species")
            for v in all_datapoints["results"]
        ]

        all_datapoints["mean_abs_epsilon_eq_species"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, metric="mean", mode="eq_species")
            for v in all_datapoints["results"]
        ]

        # Also maintain legacy column names for backwards compatibility with old datapoints
        # These will be used as fallback when new metrics don't exist
        all_datapoints["median_abs_epsilon"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, mode="global")
            for v in all_datapoints["results"]
        ]

        all_datapoints["mean_abs_epsilon"] = [
            filter_df_numquant_epsilon(v, min_quant=default_val_slider, metric="mean", mode="global")
            for v in all_datapoints["results"]
        ]

        all_datapoints["nr_feature"] = [
            filter_df_numquant_nr_feature(v, min_quant=default_val_slider) for v in all_datapoints["results"]
        ]

        return all_datapoints

    def benchmarking(
        self,
        input_file: str,
        input_format: str,
        user_input: dict,
        all_datapoints: Optional[pd.DataFrame],
        default_cutoff_min_feature: Optional[int] = None,
        input_file_secondary: Optional[str] = None,
        max_nr_observed: Optional[int] = None,
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """
        Main workflow of the module. Used to benchmark workflow results.

        Each step's failures are re-raised as the matching ProteoBench exception.

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
        default_cutoff_min_feature : int, optional
            Minimum number of runs a feature has to be identified in. Defaults to the module's
            ``default_cutoff_min_feature``.
        input_file_secondary : str, optional
            Path to a secondary input file (used for some formats like AlphaDIA).
        max_nr_observed : int, optional
            Maximum number of quantification depth levels to calculate metrics for. Defaults to the
            module's ``max_nr_observed``.

        Returns
        -------
        tuple[DataFrame, DataFrame, DataFrame]
            A tuple containing the intermediate data structure, all data points, and the input DataFrame.
        """
        if default_cutoff_min_feature is None:
            default_cutoff_min_feature = self.default_cutoff_min_feature
        if max_nr_observed is None:
            max_nr_observed = self.max_nr_observed

        try:
            input_df = self.load_input(input_file, input_format, input_file_secondary)
        except pd.errors.ParserError as e:
            raise ParseError(
                f"Error parsing {input_format} file, please ensure the format is correct "
                f"and the correct software tool is chosen: {e}"
            ) from e
        except Exception as e:
            raise ParseError(f"Error parsing the input file: {e}") from e

        with _benchmarking_step(ParseSettingsError, "Error parsing settings file for parsing"):
            parse_settings = ParseSettingsBuilder(
                parse_settings_dir=self.parse_settings_dir, module_id=self.module_id
            ).build_parser(input_format)
        with _benchmarking_step(ConvertStandardFormatError, "Error converting to standard format"):
            standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
        with _benchmarking_step(QuantificationError, "Error generating quantification scores"):
            quant_score = self.score_cls(
                self.precursor_column_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
            )
        with _benchmarking_step(IntermediateFormatGenerationError, "Error generating intermediate data structure"):
            intermediate = quant_score.generate_intermediate(standard_format, replicate_to_raw)
        with _benchmarking_step(DatapointGenerationError, "Error generating datapoint"):
            current_datapoint = self.datapoint_cls.generate_datapoint(
                intermediate,
                input_format,
                user_input,
                default_cutoff_min_feature=default_cutoff_min_feature,
                max_nr_observed=max_nr_observed,
            )
        with _benchmarking_step(DatapointAppendError, "Error adding current data point"):
            all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=all_datapoints)

        return intermediate, all_datapoints, input_df

    def load_input(self, input_file: str, input_format: str, input_file_secondary: Optional[str] = None) -> DataFrame:
        """
        Load the workflow output file. Peptidoform modules override this.

        Parameters
        ----------
        input_file : str
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        input_file_secondary : str, optional
            Path to a secondary input file (used for some formats like AlphaDIA).

        Returns
        -------
        DataFrame
            The loaded workflow output.
        """
        return load_input_file(input_file, input_format, input_file_secondary)

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
            True if the new data point has a unique hash.

        Raises
        ------
        DatasetAlreadyExistsOnServerError
            If the run was previously submitted (its hash overlaps an existing data point).
        """
        current_datapoint = datapoints[datapoints["old_new"] == "new"]
        all_datapoints_old = datapoints[datapoints["old_new"] == "old"]

        set_current_datapoint = set(list(current_datapoint["intermediate_hash"]))
        set_all_datapoints_old = set(list(all_datapoints_old["intermediate_hash"]))

        overlap = set_current_datapoint.intersection(set_all_datapoints_old)

        if len(overlap) > 0:
            overlap_name = all_datapoints_old.loc[all_datapoints_old["intermediate_hash"] == list(overlap)[0], "id"]
            raise DatasetAlreadyExistsOnServerError(
                f"The run you want to submit has been previously submitted under the identifier: {str(overlap_name)}"
            )
        return True

    def clone_pr(
        self,
        temporary_datapoints: pd.DataFrame,
        datapoint_params: Any,
        remote_git: str,
        submission_comments: str = "no comments",
        submission_source: str = "unknown",
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
        submission_source : str, optional
            Origin of the submission: 'web-server', 'local', or 'resubmission-script'.
            Defaults to 'unknown'.

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

        # Raises DatasetAlreadyExistsOnServerError if this run was already submitted.
        self.check_new_unique_hash(all_datapoints)

        # Create a new branch for the pull request with a unique branch name, this unique
        # branch name is important for batch resubmission to avoid clashes. We do guarentee
        # the same identifier name.
        hash_input = f"{datetime.now().isoformat()}_{uuid.uuid4()}".encode("utf-8")
        short_hash = hashlib.sha256(hash_input).hexdigest()[:10]  # First 10 hex characters

        branch_name = current_datapoint["id"].replace(" ", "_").replace("(", "").replace(")", "") + "_" + short_hash

        path_write_individual_point = os.path.join(self.t_dir_pr, current_datapoint["intermediate_hash"] + ".json")
        logging.info(f"Writing the json (single point) to: {path_write_individual_point}")
        datapoint_dict = current_datapoint.to_dict()
        for key in ("color", "hover_text", "scatter_size", "marker"):
            datapoint_dict.pop(key, None)
        with open(path_write_individual_point, "w") as f:
            json.dump(datapoint_dict, f, indent=2)

        commit_name = f"Added new run with id {branch_name}"
        commit_message = f"User comments: {submission_comments}"

        try:
            self.github_repo.create_branch(branch_name)
            self.github_repo.commit(commit_name, commit_message)
            pr_id = self.github_repo.create_pull_request(
                commit_name, commit_message, submission_source=submission_source
            )
        except Exception as e:
            logging.error(f"Error in PR: {e}")
            return "Unable to create PR. Please check the logs."

        return "https://" + remote_git.replace(".git", "") + "/pull/" + str(pr_id)

    def write_intermediate_raw(
        self,
        directory: str,
        ident: str,
        input_file_obj: Any,
        result_performance: pd.DataFrame,
        param_loc: List[Any],
        comment: str,
        extension_input_file: str = ".txt",
        extension_input_parameter_file: str = ".txt",
        input_file_secondary_obj: Any = None,
    ) -> None:
        """
        Write intermediate and raw data to a directory in zipped form.

        Parameters
        ----------
        directory : str
            Directory to write to.
        ident : str
            Identifier to create a subdirectory for this submission.
        input_file_obj : Any
            File-like object representing the raw input file.
        result_performance : pd.DataFrame
            The result performance DataFrame (intermediate data).
        param_loc : List[Any]
            List of paths to parameter files that need to be copied.
        comment : str
            User comment for the submission.
        input_file_secondary_obj : Any, optional
            File-like object representing a secondary input file (e.g., for AlphaDIA).
        """
        # Create the target directory
        path_write = os.path.join(directory, ident)
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

                # Save the secondary input file if provided
                if input_file_secondary_obj is not None:
                    input_file_secondary_obj.seek(0)
                    zf.writestr(f"input_file_secondary{extension_input_file}", input_file_secondary_obj.read())

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

            logging.info(f"Data saved to {zip_file_path}")
        except Exception as e:
            logging.error(f"Failed to create zip file at {zip_file_path}. Error: {e}")

    def validate_params_files(self, input_file: List, input_format: str) -> Optional[str]:
        """
        Validate the uploaded parameter files before parsing.

        Parameters
        ----------
        input_file : List
            List of uploaded files.
        input_format : str
            Format of the parameter file.

        Returns
        -------
        Optional[str]
            A warning message if validation fails, or None if the upload is complete.
        """
        validator = self.VALIDATE_FILES_DICT.get(input_format)
        if validator is None:
            return None
        if len(input_file) < 2:
            return validator(input_file)
        return None

    def load_params_file(self, input_file: List[str], input_format: str, json_file: str) -> ProteoBenchParameters:
        """
        Load parameters from a metadata file depending on its format.

        Parameters
        ----------
        input_file : List[str]
            Path to the metadata file.
        input_format : str
            Format of the metadata file.
        json_file : str
            Path to the JSON file containing additional module specific parameters.

        Returns
        -------
        ProteoBenchParameters
            The parameters for the module.
        """
        params = self.EXTRACT_PARAMS_DICT[input_format](
            *input_file,
            json_file=json_file,
        )
        params.software_name = input_format
        return params

    def get_plot_generator(self, y_axis_title: str = None) -> PlotGeneratorBase:
        """
        Get the module's plot generator (``plot_generator_cls``).

        Parameters
        ----------
        y_axis_title : str, optional
            Override the default y-axis title. If None, the class default is used.

        Returns
        -------
        PlotGeneratorBase
            The plot generator instance.
        """
        title = y_axis_title if y_axis_title is not None else self.y_axis_title
        return self.plot_generator_cls(y_axis_title=title)
