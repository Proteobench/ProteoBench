from __future__ import annotations

import dataclasses
import hashlib
import logging
from collections import ChainMap
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Union

import pandas as pd

import proteobench


def filter_df_numquant_median_abs_epsilon(
    row: Dict[Union[int, str], Dict[str, Union[int, float]]], min_quant: int = 3
) -> Optional[float]:
    """
    Extracts the median absolute epsilon value for a specific quantification level.
    Function requires a dictionary that is part of the dataframe holding results expressed
    as a key for the metric followed by a dictionary containing the metric values.

    Parameters:
        row (dict): A dictionary-like row containing nested quantification data.
        min_quant (int): Minimum quantification level to filter (default: 3).

    Returns:
        Optional[float]: The median absolute epsilon value if available; otherwise, None.
    """
    if isinstance(list(row.keys())[0], str):
        min_quant = str(min_quant)
    if isinstance(row, dict) and min_quant in row and isinstance(row[min_quant], dict):
        return row[min_quant].get("median_abs_epsilon")

    return None


def filter_df_numquant_nr_prec(
    row: Dict[Union[int, str], Dict[str, Union[int, float]]], min_quant: int = 3
) -> Optional[int]:
    """
    Extracts the number of precursors for a specific quantification level.
    Function requires a dictionary that is part of the dataframe holding results expressed
    as a key for the metric followed by a dictionary containing the metric values.

    Parameters:
        row (pd.Series): A dictionary-like row containing nested quantification data.
        min_quant (int): Minimum quantification level to filter (default: 3).

    Returns:
        Optional[int]: The number of precursors if available; otherwise, None.
    """
    if isinstance(list(row.keys())[0], str):
        min_quant = str(min_quant)
    if isinstance(row, dict) and min_quant in row and isinstance(row[min_quant], dict):
        return row[min_quant].get("nr_prec")
    return None


@dataclass
class Datapoint:
    """
    Represents the metadata and results of a single benchmarking run.

    Attributes:
        id (str): Unique identifier for the datapoint.
        software_name (str): Name of the software used.
        software_version (int): Version of the software.
        search_engine (str): Name of the search engine used.
        search_engine_version (int): Version of the search engine.
        ident_fdr_psm (int): False discovery rate for PSM identification.
        ident_fdr_peptide (int): False discovery rate for peptide identification.
        ident_fdr_protein (int): False discovery rate for protein identification.
        enable_match_between_runs (bool): Whether matches between runs are enabled.
        precursor_mass_tolerance (str): Tolerance for precursor mass.
        fragment_mass_tolerance (str): Tolerance for fragment mass.
        enzyme (str): Enzyme used in the process.
        allowed_miscleavages (int): Number of allowed miscleavages.
        min_peptide_length (int): Minimum peptide length.
        max_peptide_length (int): Maximum peptide length.
        is_temporary (bool): Whether the datapoint is temporary.
        intermediate_hash (str): Hash of the intermediate data.
        results (dict): Computed results for the datapoint.
        median_abs_epsilon (int): Median absolute epsilon value.
        nr_prec (int): Number of precursors (default is 0).
        comments (str): Comments for plotting or analysis.
        proteobench_version (str): Version of the ProteoBench framework.
    """

    id: Optional[str] = None
    software_name: Optional[str] = None
    software_version: int = 0
    search_engine: Optional[str] = None
    search_engine_version: int = 0
    ident_fdr_psm: int = 0
    ident_fdr_peptide: int = 0
    ident_fdr_protein: int = 0
    enable_match_between_runs: bool = False
    precursor_mass_tolerance: Optional[str] = None
    fragment_mass_tolerance: Optional[str] = None
    enzyme: Optional[str] = None
    allowed_miscleavages: int = 0
    min_peptide_length: int = 0
    max_peptide_length: int = 0
    is_temporary: bool = True
    intermediate_hash: str = ""
    results: Optional[Dict] = None
    median_abs_epsilon: int = 0
    nr_prec: int = 0
    comments: str = ""
    proteobench_version: str = ""

    def generate_id(self) -> None:
        """
        Generates a unique identifier for the datapoint using the current timestamp
        and the software name.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = "_".join([self.software_name, str(time_stamp)])
        logging.info(f"Assigned the following ID to this run: {self.id}")

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame,
        input_format: str,
        user_input: Dict[str, Union[str, int, bool]],
        default_cutoff_min_prec: int = 3,
    ) -> pd.Series:
        """
        Creates a new Datapoint instance, computes its metadata and results, and returns it as a Pandas Series.

        Parameters:
            intermediate (pd.DataFrame): Intermediate results data.
            input_format (str): Format of the input data (e.g., software name).
            user_input (dict): User-provided parameters for the datapoint.
            default_cutoff_min_prec (int): Default minimum quantification level (default: 3).

        Returns:
            pd.Series: Datapoint instance represented as a Pandas Series.
        """
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        user_input = {key: ("" if value is None else value) for key, value in user_input.items()}
        result_datapoint = Datapoint(
            id=f"{input_format}_{user_input['software_version']}_{formatted_datetime}",
            software_name=input_format,
            software_version=int(user_input["software_version"]),
            search_engine=user_input["search_engine"],
            search_engine_version=int(user_input["search_engine_version"]),
            ident_fdr_psm=int(user_input["ident_fdr_psm"]),
            ident_fdr_peptide=int(user_input["ident_fdr_peptide"]),
            ident_fdr_protein=int(user_input["ident_fdr_protein"]),
            enable_match_between_runs=bool(user_input["enable_match_between_runs"]),
            precursor_mass_tolerance=user_input["precursor_mass_tolerance"],
            fragment_mass_tolerance=user_input["fragment_mass_tolerance"],
            enzyme=user_input["enzyme"],
            allowed_miscleavages=int(user_input["allowed_miscleavages"]),
            min_peptide_length=int(user_input["min_peptide_length"]),
            max_peptide_length=int(user_input["max_peptide_length"]),
            intermediate_hash=hashlib.sha1(intermediate.to_string().encode("utf-8")).hexdigest(),
            comments=user_input.get("comments_for_plotting", ""),
            proteobench_version=proteobench.__version__,
        )

        result_datapoint.generate_id()
        results = dict(ChainMap(*[Datapoint.get_metrics(intermediate, nr_observed) for nr_observed in range(1, 7)]))
        result_datapoint.results = results
        result_datapoint.median_abs_epsilon = results[default_cutoff_min_prec]["median_abs_epsilon"]

        return pd.Series(dataclasses.asdict(result_datapoint))

    @staticmethod
    def get_metrics(df: pd.DataFrame, min_nr_observed: int = 1) -> Dict[int, Dict[str, Union[int, float]]]:
        """
        Computes statistical metrics for data with a minimum number of observations.

        Parameters:
            df (pd.DataFrame): DataFrame containing quantification data.
            min_nr_observed (int): Minimum number of observations to include (default: 1).

        Returns:
            dict: Statistical metrics, including median absolute epsilon, variance,
                  and descriptive statistics for coefficients of variation (CVs).
        """
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        nr_prec = len(df_slice)

        # TODO should be moved to scoring
        median_abs_epsilon = df_slice["epsilon"].abs().median()
        variance_epsilon = df_slice["epsilon"].var()
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
