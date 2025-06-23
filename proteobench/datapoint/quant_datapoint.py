"""
This module provides functionality for handling and processing quantitative datapoints in the ProteoBench framework.
"""

from __future__ import annotations

import dataclasses
import hashlib
import logging
from collections import ChainMap, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pandas as pd

import proteobench


def filter_df_numquant_epsilon(row: Dict[str, Any], min_quant: int = 3, metric: str = "median") -> float | None:
    """
    Extract the 'median_abs_epsilon' value from a row (assumed to be a dictionary).

    Parameters
    ----------
    row : dict
        The row from which to extract the value. Expected to be a dictionary.
    min_quant : int or str, optional
        The key for the desired value. Defaults to 3.
    metric : str
        The metric to be calculated. Should be either median or mean, defaults to median.

    Returns
    -------
    float or None
        The 'median_abs_epsilon' value if found, otherwise None.
    """
    if not row:  # Handle empty dictionary
        return None

    if isinstance(list(row.keys())[0], str):
        min_quant = str(min_quant)
    if isinstance(row, dict) and min_quant in row and isinstance(row[min_quant], dict):
        return row[min_quant].get("{}_abs_epsilon".format(metric))

    return None


def filter_df_numquant_nr_prec(row: pd.Series, min_quant: int = 3) -> int | None:
    """
    Extract the 'nr_prec' value from a row (assumed to be a dictionary).

    Parameters
    ----------
    row : pd.Series
        The row from which to extract the value. Expected to be a dictionary or Series.
    min_quant : int or str, optional
        The key for the desired value. Defaults to 3.

    Returns
    -------
    int, None
        The 'nr_prec' value if found, otherwise None.
    """
    if isinstance(list(row.keys())[0], str):
        min_quant = str(min_quant)
    if isinstance(row, dict) and min_quant in row and isinstance(row[min_quant], dict):
        return row[min_quant].get("nr_prec")
    return None


@dataclass
class QuantDatapoint:
    """
    A data structure used to store the results of a benchmark run.

    Attributes:
        id (str): Unique identifier for the benchmark run.
        software_name (str): Name of the software used in the benchmark.
        software_version (str): Version of the software.
        search_engine (str): Name of the search engine used.
        search_engine_version (str): Version of the search engine.
        ident_fdr_psm (float): False discovery rate for PSMs.
        ident_fdr_peptide (float): False discovery rate for peptides.
        ident_fdr_protein (float): False discovery rate for proteins.
        enable_match_between_runs (bool): Whether matching between runs is enabled.
        precursor_mass_tolerance (str): Mass tolerance for precursor ions.
        fragment_mass_tolerance (str): Mass tolerance for fragment ions.
        enzyme (str): Enzyme used for digestion.
        allowed_miscleavages (int): Number of allowed miscleavages.
        min_peptide_length (int): Minimum peptide length.
        max_peptide_length (int): Maximum peptide length.
        is_temporary (bool): Whether the data is temporary.
        intermediate_hash (str): Hash of the intermediate result.
        results (dict): A dictionary of metrics for the benchmark run.
        median_abs_epsilon (float): Median absolute epsilon value for the benchmark.
        mean_abs_epsilon (float): Mean absolute epsilon value for the benchmark.
        nr_prec (int): Number of precursors identified.
        comments (str): Any additional comments.
        proteobench_version (str): Version of the Proteobench tool used.
    """

    id: str = None
    software_name: str = None
    software_version: int = 0
    search_engine: str = None
    search_engine_version: int = 0
    ident_fdr_psm: int = 0
    ident_fdr_peptide: int = 0
    ident_fdr_protein: int = 0
    enable_match_between_runs: bool = False
    precursor_mass_tolerance: str = None
    fragment_mass_tolerance: str = None
    enzyme: str = None
    allowed_miscleavages: int = 0
    min_peptide_length: int = 0
    max_peptide_length: int = 0
    is_temporary: bool = True
    intermediate_hash: str = ""
    results: dict = None
    median_abs_epsilon: float = 0
    mean_abs_epsilon: float = 0
    nr_prec: int = 0
    comments: str = ""
    proteobench_version: str = ""

    def generate_id(self) -> None:
        """
        Generate a unique ID for the benchmark run by combining the software name and a timestamp.

        This ID is used to uniquely identify each run of the benchmark.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = "_".join([self.software_name, str(time_stamp)])
        logging.info(f"Assigned the following ID to this run: {self.id}")

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame, input_format: str, user_input: dict, default_cutoff_min_prec: int = 3
    ) -> pd.Series:
        """
        Generate a Datapoint object containing metadata and results from the benchmark run.

        Parameters
        ----------
        intermediate : pd.DataFrame
            The intermediate DataFrame containing benchmark results.
        input_format : str
            The format of the input data (e.g., file format).
        user_input : dict
            User-defined input values for the benchmark.
        default_cutoff_min_prec : int, optional
            The default minimum precursor cutoff value. Defaults to 3.

        Returns
        -------
        pd.Series
            A Pandas Series containing the Datapoint's attributes as key-value pairs.
        """
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        if "comments_for_plotting" not in user_input.keys():
            user_input["comments_for_plotting"] = ""

        try:
            user_input = defaultdict(
                user_input.default_factory,  # Preserve the default factory
                {key: ("" if value is None else value) for key, value in user_input.items()},
            )
        except AttributeError:
            user_input = {key: ("" if value is None else value) for key, value in user_input.items()}

        result_datapoint = QuantDatapoint(
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
            comments=user_input["comments_for_plotting"],
            proteobench_version=proteobench.__version__,
        )

        result_datapoint.generate_id()

        results = dict(
            ChainMap(*[QuantDatapoint.get_metrics(intermediate, nr_observed) for nr_observed in range(1, 7)])
        )
        result_datapoint.results = results
        result_datapoint.median_abs_epsilon = result_datapoint.results[default_cutoff_min_prec]["median_abs_epsilon"]
        result_datapoint.mean_abs_epsilon = result_datapoint.results[default_cutoff_min_prec]["mean_abs_epsilon"]
        result_datapoint.nr_prec = result_datapoint.results[default_cutoff_min_prec]["nr_prec"]

        results_series = pd.Series(dataclasses.asdict(result_datapoint))

        return results_series

    def get_metrics(df: pd.DataFrame, min_nr_observed: int = 1) -> dict[int, dict[str, float]]:
        """
        Compute various statistical metrics from the provided DataFrame for the benchmark,
        but optimized to do fewer passes over the data.
        """
        # 1) Filter once
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        nr_prec = len(df_slice)

        # 2) Compute abs-epsilon only once
        eps = df_slice["epsilon"].abs()

        # 3) Batch the CV quantiles in one go
        #    This returns a DataFrame with index [0.50, 0.75, 0.90, 0.95]
        cv_q = df_slice[["CV_A", "CV_B"]].quantile([0.5, 0.75, 0.9, 0.95])
        #    Then average across the two columns for each quantile
        cv_avg = cv_q.mean(axis=1)

        return {
            min_nr_observed: {
                "median_abs_epsilon": eps.median(),
                "mean_abs_epsilon": eps.mean(),
                "variance_epsilon": df_slice["epsilon"].var(),
                "nr_prec": nr_prec,
                "CV_median": cv_avg.loc[0.50],
                "CV_q75": cv_avg.loc[0.75],
                "CV_q90": cv_avg.loc[0.90],
                "CV_q95": cv_avg.loc[0.95],
            }
        }

    @staticmethod
    def get_metrics_old(df: pd.DataFrame, min_nr_observed: int = 1) -> Dict[int, Dict[str, float]]:
        """
        Compute various statistical metrics from the provided DataFrame for the benchmark.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame containing the benchmark results.
        min_nr_observed : int, optional
            The minimum number of observed values for a valid computation. Defaults to 1.

        Returns
        -------
        dict
            A dictionary containing computed metrics such as 'median_abs_epsilon', 'variance_epsilon', etc.
        """
        # Filter DataFrame by the minimum number of observations
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        nr_prec = len(df_slice)

        # Calculate the median absolute epsilon (insensitive to outliers)
        median_abs_epsilon = df_slice["epsilon"].abs().median()
        # Calculate the mean absolute epsilon (sensitive to outliers)
        mean_abs_epsilon = df_slice["epsilon"].abs().mean()

        # Calculate the variance of epsilon (sensitive to outliers)
        variance_epsilon = df_slice["epsilon"].var()

        # Compute the median of the coefficient of variation (CV) for both 'CV_A' and 'CV_B'
        cv_median = (df_slice["CV_A"].median() + df_slice["CV_B"].median()) / 2
        cv_q75 = (df_slice["CV_A"].quantile(0.75) + df_slice["CV_B"].quantile(0.75)) / 2
        cv_q90 = (df_slice["CV_A"].quantile(0.9) + df_slice["CV_B"].quantile(0.9)) / 2
        cv_q95 = (df_slice["CV_A"].quantile(0.95) + df_slice["CV_B"].quantile(0.95)) / 2

        return {
            min_nr_observed: {
                "median_abs_epsilon": median_abs_epsilon,
                "mean_abs_epsilon": mean_abs_epsilon,
                "variance_epsilon": variance_epsilon,
                "nr_prec": nr_prec,
                "CV_median": cv_median,
                "CV_q90": cv_q90,
                "CV_q75": cv_q75,
                "CV_q95": cv_q95,
            }
        }
