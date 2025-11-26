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

import numpy as np
import pandas as pd

import proteobench
from proteobench.datapoint.datapoint_base import DatapointBase


def filter_df_numquant_epsilon(
    row: Dict[str, Any], min_quant: int = 3, metric: str = "median", mode: str = "global"
) -> float | None:
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
        return row[min_quant].get("{}_abs_epsilon_{}".format(metric, mode))

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
class QuantDatapointHYE(DatapointBase):
    """
    A data structure used to store the results of a quantification benchmark run.

    This class extends DatapointBase to implement quantification-specific metrics and metadata
    storage for LFQ benchmarking runs.

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
        median_abs_epsilon_global (float): Median absolute epsilon value (global calculation).
        mean_abs_epsilon_global (float): Mean absolute epsilon value (global calculation).
        median_abs_epsilon_eq_species (float): Median absolute epsilon value (equal weighted species).
        mean_abs_epsilon_eq_species (float): Mean absolute epsilon value (equal weighted species).
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
    median_abs_epsilon_global: float = 0
    mean_abs_epsilon_global: float = 0
    median_abs_epsilon_eq_species: float = 0
    mean_abs_epsilon_eq_species: float = 0
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
        intermediate: pd.DataFrame,
        input_format: str,
        user_input: dict,
        default_cutoff_min_prec: int = 3,
        max_nr_observed: int = None,
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
        max_nr_observed : int, optional
            Maximum nr_observed value to calculate metrics for. If None, defaults to 6.

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

        result_datapoint = QuantDatapointHYE(
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

        # Use provided max_nr_observed or default to 6
        if max_nr_observed is None:
            max_nr_observed = 6

        results = dict(
            ChainMap(
                *[
                    QuantDatapointHYE.get_metrics(intermediate, nr_observed)
                    for nr_observed in range(1, int(max_nr_observed) + 1)
                ]
            )
        )
        result_datapoint.results = results
        result_datapoint.median_abs_epsilon_global = result_datapoint.results[default_cutoff_min_prec][
            "median_abs_epsilon_global"
        ]
        result_datapoint.mean_abs_epsilon_global = result_datapoint.results[default_cutoff_min_prec][
            "mean_abs_epsilon_global"
        ]
        result_datapoint.median_abs_epsilon_eq_species = result_datapoint.results[default_cutoff_min_prec][
            "median_abs_epsilon_eq_species"
        ]
        result_datapoint.mean_abs_epsilon_eq_species = result_datapoint.results[default_cutoff_min_prec][
            "mean_abs_epsilon_eq_species"
        ]
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

        # 2) Compute abs-epsilon only once, globally
        eps_global = df_slice["epsilon"].abs()

        # 3) Batch the CV quantiles in one go
        #    This returns a DataFrame with index [0.50, 0.75, 0.90, 0.95]
        cv_q = df_slice[["CV_A", "CV_B"]].quantile([0.5, 0.75, 0.9, 0.95])
        #    Then average across the two columns for each quantile
        cv_avg = cv_q.mean(axis=1)

        return {
            min_nr_observed: {
                "median_abs_epsilon_global": eps_global.median(),
                "mean_abs_epsilon_global": eps_global.mean(),
                "variance_epsilon_global": df_slice["epsilon"].var(),
                "median_abs_epsilon_eq_species": pd.Series(
                    [
                        df_slice[df_slice["species"] == species]["epsilon"].abs().median()
                        for species in df_slice["species"].unique()
                    ]
                ).mean(),
                "mean_abs_epsilon_eq_species": pd.Series(
                    [
                        df_slice[df_slice["species"] == species]["epsilon"].abs().mean()
                        for species in df_slice["species"].unique()
                    ]
                ).mean(),
                "nr_prec": nr_prec,
                "CV_median": cv_avg.loc[0.50],
                "CV_q75": cv_avg.loc[0.75],
                "CV_q90": cv_avg.loc[0.90],
                "CV_q95": cv_avg.loc[0.95],
            }
        }


class QuantDatapointPYE(QuantDatapointHYE):
    """
    A data structure used to store the results of a quantification benchmark run for plasma (PYE) setups.

    This class extends QuantDatapointHYE to implement plasma-specific metrics and metadata
    storage for quantification benchmarking runs on plasma samples. The PYE module benchmarks
    quantification performance across three species (yeast, E. coli, and human plasma) with
    metrics for visualization in a scatterplot format.

    Attributes:
        Inherits all attributes from QuantDatapointHYE.
        median_abs_log2_fc_error_spike_ins (float): Median absolute log2 fold-change error for yeast and E. coli spike-ins.
        nr_quantified_spike_ins (int): Number of quantified yeast and E. coli spike-in precursors (quantification depth).
        dynamic_range_human_plasma (float): Dynamic range of human plasma precursors (log10 difference between 90th and 10th percentile).
        median_abs_epsilon_human_plasma (float): Median absolute epsilon for human plasma precursors (quantification accuracy).
    """

    # Add plasma-specific metric attributes
    median_abs_log2_fc_error_spike_ins: float = 0.0
    nr_quantified_spike_ins: int = 0
    dynamic_range_human_plasma: float = 0.0
    median_abs_epsilon_human_plasma: float = 0.0

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame,
        input_format: str,
        user_input: dict,
        default_cutoff_min_prec: int = 3,
        max_nr_observed: int = None,
    ) -> pd.Series:
        """
        Generate a Datapoint object containing metadata and results from the plasma benchmark run.

        This method extends the parent implementation to compute plasma-specific metrics:
        - Median fold-change error for yeast and E. coli spike-ins (for x-axis)
        - Number of quantified spike-in precursors (for y-axis)
        - Dynamic range of human plasma precursors (for dot size)
        - Quantification accuracy for human plasma (for transparency/opacity)

        Parameters
        ----------
        intermediate : pd.DataFrame
            The intermediate DataFrame containing benchmark results with species annotations.
        input_format : str
            The format of the input data (e.g., file format).
        user_input : dict
            User-defined input values for the benchmark.
        default_cutoff_min_prec : int, optional
            The default minimum precursor cutoff value. Defaults to 3.
        max_nr_observed : int, optional
            Maximum nr_observed value to calculate metrics for. If None, defaults to 6.

        Returns
        -------
        pd.Series
            A Pandas Series containing the Datapoint's attributes as key-value pairs.
        """
        # Call parent class implementation to get base datapoint
        result_series = QuantDatapointHYE.generate_datapoint(
            intermediate, input_format, user_input, default_cutoff_min_prec, max_nr_observed
        )

        # Convert to mutable dict for plasma-specific metrics
        result_dict = result_series.to_dict()

        # Compute plasma-specific metrics for each min_nr_observed threshold
        # This mirrors the structure of the parent class results dictionary
        plasma_metrics = QuantDatapointPYE._get_plasma_metrics(intermediate, max_nr_observed)

        # Flatten and merge plasma metrics into results dictionary
        for min_nr_obs, metrics in plasma_metrics.items():
            # Store plasma-specific metrics at each min_nr_observed level
            if "results" in result_dict and min_nr_obs in result_dict["results"]:
                result_dict["results"][min_nr_obs].update(metrics)

        # Assign default cutoff metrics to top-level fields for backward compatibility
        if default_cutoff_min_prec in plasma_metrics:
            result_dict["median_abs_log2_fc_error_spike_ins"] = plasma_metrics[default_cutoff_min_prec].get(
                "median_abs_log2_fc_error_spike_ins", 0.0
            )
            result_dict["nr_quantified_spike_ins"] = plasma_metrics[default_cutoff_min_prec].get(
                "nr_quantified_spike_ins", 0
            )
            result_dict["dynamic_range_human_plasma"] = plasma_metrics[default_cutoff_min_prec].get(
                "dynamic_range_human_plasma_mean", 0.0
            )
            result_dict["median_abs_epsilon_human_plasma"] = plasma_metrics[default_cutoff_min_prec].get(
                "median_abs_epsilon_human_plasma", 0.0
            )

        # Convert back to Series
        result_series = pd.Series(result_dict)

        return result_series

    @staticmethod
    def _get_plasma_metrics(intermediate: pd.DataFrame, max_nr_observed: int = None) -> dict[int, dict[str, float]]:
        """
        Compute plasma-specific metrics for each min_nr_observed threshold.

        Parameters
        ----------
        intermediate : pd.DataFrame
            The intermediate DataFrame containing benchmark results with species annotations.
        max_nr_observed : int, optional
            Maximum nr_observed value to calculate metrics for. If None, defaults to 6.

        Returns
        -------
        dict[int, dict[str, float]]
            Dictionary with min_nr_observed as keys and plasma metrics as values.
        """
        plasma_metrics = {}

        # Use provided max_nr_observed or default to 6
        if max_nr_observed is None:
            max_nr_observed = 12

        # Compute metrics for each min_nr_observed level up to the maximum
        for min_nr_obs in range(1, int(max_nr_observed) + 1):
            # Filter data for this min_nr_observed threshold
            df_slice = intermediate[intermediate["nr_observed"] >= min_nr_obs]

            # If no precursors meet this threshold, return zero metrics for this level
            if len(df_slice) == 0:
                plasma_metrics[min_nr_obs] = {
                    "median_abs_log2_fc_error_spike_ins": 0.0,
                    "nr_quantified_spike_ins": 0,
                    "dynamic_range_human_plasma_A": 0.0,
                    "dynamic_range_human_plasma_B": 0.0,
                    "dynamic_range_human_plasma_mean": 0.0,
                    "median_abs_epsilon_human_plasma": 0.0,
                }
                continue

            # Compute median absolute log2 fold-change error for spike-ins (yeast and E. coli)
            spike_ins_df = df_slice[df_slice["species"].isin(["YEAST", "ECOLI"])]
            median_abs_log2_fc_error_spike_ins = (
                spike_ins_df["epsilon"].abs().median() if len(spike_ins_df) > 0 else 0.0
            )

            # Compute number of quantified spike-in precursors
            nr_quantified_spike_ins = len(spike_ins_df)

            # Compute dynamic range of human plasma precursors
            human_plasma_df = df_slice[df_slice["species"] == "HUMAN"]

            dynamic_ranges = {}
            for condition in ["A", "B"]:
                if f"Intensity_mean_{condition}" not in human_plasma_df.columns:
                    human_plasma_df[f"Intensity_mean_{condition}"] = np.nan
                else:
                    human_plasma_df[f"log10_Intensity_mean_{condition}"] = np.log10(
                        human_plasma_df[f"Intensity_mean_{condition}"].clip(lower=1e-10)
                    )
                    dynamic_ranges[condition] = human_plasma_df[f"log10_Intensity_mean_{condition}"].quantile(
                        0.90
                    ) - human_plasma_df[f"log10_Intensity_mean_{condition}"].quantile(0.10)
            if dynamic_ranges:
                dynamic_range_human_plasma_mean = np.mean(list(dynamic_ranges.values()))
            else:
                dynamic_range_human_plasma_mean = 0.0

            # Compute median absolute epsilon for human plasma
            median_abs_epsilon_human_plasma = (
                human_plasma_df["epsilon"].abs().median() if len(human_plasma_df) > 0 else 0.0
            )

            plasma_metrics[min_nr_obs] = {
                "median_abs_log2_fc_error_spike_ins": median_abs_log2_fc_error_spike_ins,
                "nr_quantified_spike_ins": nr_quantified_spike_ins,
                "dynamic_range_human_plasma_A": dynamic_ranges.get("A", 0.0),
                "dynamic_range_human_plasma_B": dynamic_ranges.get("B", 0.0),
                "dynamic_range_human_plasma_mean": dynamic_range_human_plasma_mean if dynamic_ranges else 0.0,
                "median_abs_epsilon_human_plasma": median_abs_epsilon_human_plasma,
            }

        return plasma_metrics
