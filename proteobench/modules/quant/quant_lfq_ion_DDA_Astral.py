"""
DDA Quantification Module for Ion level Quantification.
"""

from __future__ import annotations
from typing import Dict, Tuple

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import QuantDatapoint
from proteobench.exceptions import (
    ConvertStandardFormatError,
    IntermediateFormatGenerationError,
    ParseError,
    ParseSettingsError,
    QuantificationError,
)
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_base_module import QuantModule
from proteobench.score.quant.quantscores import QuantScores
from proteobench.modules.quant.benchmarking import run_benchmarking_with_timing


class DDAQuantIonAstralModule(QuantModule):
    """
    DDA Quantification Module for Ion level Quantification.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str, optional
        Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DDA".
    proteobench_repo_name : str, optional
        Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DDA".

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    module_id = "quant_lfq_DDA_ion_Astral"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_ion_DDA_Astral",
        proteobench_repo_name: str = "Proteobench/Results_quant_ion_DDA_Astral",
    ):
        """
        Initialize the DDA Quantification Module for Ion level Quantification for Astral.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DDA".
        proteobench_repo_name : str, optional
            Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DDA".
        """

        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=MODULE_SETTINGS_DIRS[self.module_id],
            module_id=self.module_id,
        )
        self.precursor_column_name = "precursor ion"

    def is_implemented(self) -> bool:
        """
        Return whether the module is fully implemented.

        Returns
        -------
        bool
            True if the module is fully implemented, False otherwise.
        """
        return True

    def benchmarking(
        self,
        input_file_loc: any,
        input_format: str,
        user_input: dict,
        all_datapoints: pd.DataFrame,
        default_cutoff_min_prec: int = 3,
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """
        Main workflow of the module. Used to benchmark workflow results.

        Parameters
        ----------
        input_file_loc : any
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        user_input : dict
            User provided parameters for plotting.
        all_datapoints : pd.DataFrame
            DataFrame containing all datapoints from the proteobench repo.
        default_cutoff_min_prec : int
            Minimum number of runs an ion has to be identified in.

        Returns
        -------
        tuple[DataFrame, DataFrame, DataFrame]
            Tuple containing the intermediate data structure, all datapoints, and the input DataFrame.
        """
        result = run_benchmarking_with_timing(
            input_file=input_file_loc,
            input_format=input_format,
            user_input=user_input,
            all_datapoints=all_datapoints,
            parse_settings_dir=self.parse_settings_dir,
            module_id=self.module_id,
            precursor_column_name=self.precursor_column_name,
            default_cutoff_min_prec=default_cutoff_min_prec,
            add_datapoint_func=self.add_current_data_point,
        )
        # Return only the first three elements (without timings)
        return result[:3]

    def benchmarking_2(
        self,
        input_file_loc: str,
        input_format: str,
        user_input: dict[str, object],
        all_datapoints: pd.DataFrame,
        default_cutoff_min_prec: int = 3,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
        """
        Main workflow of the module with timing information. Used to benchmark workflow results.

        Parameters
        ----------
        input_file_loc : str
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        user_input : dict[str, object]
            User provided parameters for plotting.
        all_datapoints : pd.DataFrame
            DataFrame containing all datapoints from the proteobench repo.
        default_cutoff_min_prec : int, optional
            Minimum number of runs an ion has to be identified in (default is 3).

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]
            A 4-tuple containing:
              - intermediate_metric_structure (pd.DataFrame)
              - all_datapoints (pd.DataFrame)
              - input_df (pd.DataFrame)
              - timings (dict of step names to elapsed seconds)
        """
        return run_benchmarking_with_timing(
            input_file=input_file_loc,
            input_format=input_format,
            user_input=user_input,
            all_datapoints=all_datapoints,
            parse_settings_dir=self.parse_settings_dir,
            module_id=self.module_id,
            precursor_column_name=self.precursor_column_name,
            default_cutoff_min_prec=default_cutoff_min_prec,
            add_datapoint_func=self.add_current_data_point,
        )
