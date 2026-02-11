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
from sklearn.metrics import roc_auc_score

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
    mode : str, optional
        The mode of metric calculation, defaults to "global".
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
        # Try with mode suffix first (new format)
        metric_key_with_mode = "{}_abs_epsilon_{}".format(metric, mode)
        result = row[min_quant].get(metric_key_with_mode)

        # Fallback to legacy format without mode suffix (for old datapoints)
        if result is None:
            metric_key_legacy = "{}_abs_epsilon".format(metric)
            result = row[min_quant].get(metric_key_legacy)

        return result

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


def compute_roc_auc(df: pd.DataFrame, unchanged_species: str = None) -> float:
    """
    Compute ROC-AUC for distinguishing unchanged from changed species.

    Uses absolute log2 fold change as the score to separate species that should
    show no change (e.g., HUMAN with 1:1 ratio) from species that should show
    change (e.g., YEAST, ECOLI with different ratios).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'species' and 'log2_A_vs_B' columns.
        Optionally 'log2_expectedRatio' for auto-detecting unchanged species.
    unchanged_species : str, optional
        Species name for the unchanged/control group. If None, auto-detects
        from data as the species with smallest absolute expected log2 ratio.

    Returns
    -------
    float
        ROC-AUC score, or np.nan if computation is not possible
        (e.g., only one class present or all scores are NaN).
    """
    if "species" not in df.columns or "log2_A_vs_B" not in df.columns:
        return np.nan

    if len(df) == 0:
        return np.nan

    # Auto-detect unchanged species if not provided
    if unchanged_species is None:
        unchanged_species = _detect_unchanged_species(df)
        if unchanged_species is None:
            return np.nan

    y_true = (df["species"] != unchanged_species).astype(int)
    y_score = df["log2_A_vs_B"].abs()

    # Need both classes and valid scores
    if len(y_true.unique()) < 2 or y_score.isna().all():
        return np.nan

    # Handle NaN scores by dropping them
    valid_mask = ~y_score.isna()
    if valid_mask.sum() < 2:
        return np.nan

    return roc_auc_score(y_true[valid_mask], y_score[valid_mask])


def _detect_unchanged_species(df: pd.DataFrame) -> str | None:
    """
    Detect the unchanged species from the data.

    The unchanged species is the one with the smallest absolute expected log2 ratio
    (i.e., ratio closest to 1:1).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'species' and 'log2_expectedRatio' columns.

    Returns
    -------
    str or None
        Species name for the unchanged group, or None if detection fails.
    """
    if "log2_expectedRatio" not in df.columns or "species" not in df.columns:
        return None

    if len(df) == 0:
        return None

    # Get unique species-ratio pairs and find the one closest to 1:1
    species_ratios = df[["species", "log2_expectedRatio"]].drop_duplicates()
    idx = species_ratios["log2_expectedRatio"].abs().idxmin()
    return species_ratios.loc[idx, "species"]


def compute_roc_auc_directional(df: pd.DataFrame) -> float:
    """
    Compute directional ROC-AUC for distinguishing changed from unchanged species.

    Unlike the abs-based ROC-AUC, this method accounts for the expected direction
    of fold change for each species:
    - For species with positive expected log2 ratio (e.g., YEAST): Uses raw log2_FC
    - For species with negative expected log2 ratio (e.g., ECOLI): Uses -log2_FC

    This approach is more robust to systematic bias where the unchanged species
    may not be centered at zero.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'species', 'log2_A_vs_B', and 'log2_expectedRatio' columns.

    Returns
    -------
    float
        Average ROC-AUC score across all changed species, or np.nan if computation
        is not possible.
    """
    required_cols = ["species", "log2_A_vs_B", "log2_expectedRatio"]
    if not all(col in df.columns for col in required_cols):
        return np.nan

    if len(df) == 0:
        return np.nan

    # Detect unchanged species (closest to 1:1 ratio)
    unchanged_species = _detect_unchanged_species(df)
    if unchanged_species is None:
        return np.nan

    # Get unique species and their expected ratios
    species_ratios = df[["species", "log2_expectedRatio"]].drop_duplicates()
    changed_species = species_ratios[species_ratios["species"] != unchanged_species]

    if len(changed_species) == 0:
        return np.nan

    roc_aucs = []

    for _, row in changed_species.iterrows():
        species_name = row["species"]
        expected_ratio = row["log2_expectedRatio"]

        # Filter to unchanged and this changed species
        df_binary = df[df["species"].isin([unchanged_species, species_name])].copy()

        if len(df_binary) == 0:
            continue

        # Labels: 1 for changed species, 0 for unchanged
        y_true = (df_binary["species"] == species_name).astype(int)

        # Score: Use direction based on expected ratio
        # If expected ratio > 0, changed species should have higher log2_FC
        # If expected ratio < 0, changed species should have lower log2_FC (so negate)
        if expected_ratio >= 0:
            y_score = df_binary["log2_A_vs_B"]
        else:
            y_score = -df_binary["log2_A_vs_B"]

        # Need both classes and valid scores
        if len(y_true.unique()) < 2 or y_score.isna().all():
            continue

        # Handle NaN scores
        valid_mask = ~y_score.isna()
        if valid_mask.sum() < 2:
            continue

        try:
            auc = roc_auc_score(y_true[valid_mask], y_score[valid_mask])
            roc_aucs.append(auc)
        except ValueError:
            continue

    if len(roc_aucs) == 0:
        return np.nan

    return np.mean(roc_aucs)


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
        median_abs_epsilon_global (float): Median absolute epsilon value for the benchmark.
        mean_abs_epsilon_global (float): Mean absolute epsilon value for the benchmark.
        median_abs_epsilon_eq_species (float): Median absolute epsilon value for equivalently weighted species.
        mean_abs_epsilon_eq_species (float): Mean absolute epsilon value for equivalently weighted species.
        median_abs_epsilon_precision_global (float): Median absolute precision epsilon (deviation from empirical center).
        mean_abs_epsilon_precision_global (float): Mean absolute precision epsilon (deviation from empirical center).
        median_abs_epsilon_precision_eq_species (float): Median absolute precision epsilon for equivalently weighted species.
        mean_abs_epsilon_precision_eq_species (float): Mean absolute precision epsilon for equivalently weighted species.
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
    median_abs_epsilon_precision_global: float = 0
    mean_abs_epsilon_precision_global: float = 0
    median_abs_epsilon_precision_eq_species: float = 0
    mean_abs_epsilon_precision_eq_species: float = 0
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
        result_datapoint.median_abs_epsilon_precision_global = result_datapoint.results[default_cutoff_min_prec][
            "median_abs_epsilon_precision_global"
        ]
        result_datapoint.mean_abs_epsilon_precision_global = result_datapoint.results[default_cutoff_min_prec][
            "mean_abs_epsilon_precision_global"
        ]
        result_datapoint.median_abs_epsilon_precision_eq_species = result_datapoint.results[default_cutoff_min_prec][
            "median_abs_epsilon_precision_eq_species"
        ]
        result_datapoint.mean_abs_epsilon_precision_eq_species = result_datapoint.results[default_cutoff_min_prec][
            "mean_abs_epsilon_precision_eq_species"
        ]
        result_datapoint.nr_prec = result_datapoint.results[default_cutoff_min_prec]["nr_prec"]

        results_series = pd.Series(dataclasses.asdict(result_datapoint))

        return results_series

    @staticmethod
    def get_epsilon_metrics(df: pd.DataFrame, min_nr_observed: int, agg: str = "median") -> dict[str, float]:
        """
        Compute epsilon-based accuracy metrics using specified aggregation.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with epsilon column (deviation from expected ratio)
        min_nr_observed : int
            Filter threshold for minimum observations
        agg : str
            Aggregation method: "median" or "mean"

        Returns
        -------
        dict
            Accuracy metrics: global, equal-species average, and per-species values
        """
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        agg_func = (lambda x: x.abs().median()) if agg == "median" else (lambda x: x.abs().mean())
        per_species_acc = df_slice.groupby("species")["epsilon"].apply(agg_func)

        return {
            f"{agg}_abs_epsilon_global": agg_func(df_slice["epsilon"]),
            f"{agg}_abs_epsilon_eq_species": per_species_acc.mean(),
            **{f"{agg}_abs_epsilon_{sp}": v for sp, v in per_species_acc.items()},
        }

    @staticmethod
    def get_precision_metrics(df: pd.DataFrame, min_nr_observed: int, agg: str = "median") -> dict[str, float]:
        """
        Compute precision metrics directly from log2FC (log2_A_vs_B) column.

        Precision measures deviation from the empirical center (reproducibility),
        computed independently from expected ratios.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with log2_A_vs_B and species columns
        min_nr_observed : int
            Filter threshold for minimum observations
        agg : str
            Aggregation method: "median" or "mean"

        Returns
        -------
        dict
            Precision metrics including:
            - {agg}_log2_empirical_{species}: Center of log2FC distribution per species
            - {agg}_abs_epsilon_precision_global: Global aggregated precision
            - {agg}_abs_epsilon_precision_eq_species: Equal-weighted species average
            - {agg}_abs_epsilon_precision_{species}: Per-species precision values
        """
        df_slice = df[df["nr_observed"] >= min_nr_observed]

        # Compute empirical center per species
        center_func = (lambda x: x.median()) if agg == "median" else (lambda x: x.mean())
        per_species_center = df_slice.groupby("species")["log2_A_vs_B"].transform(center_func)

        # Precision = deviation from empirical center
        epsilon_precision = df_slice["log2_A_vs_B"] - per_species_center

        # Aggregate precision per species
        agg_func = (lambda x: x.abs().median()) if agg == "median" else (lambda x: x.abs().mean())

        # Create temp df for groupby
        prec_df = df_slice[["species"]].copy()
        prec_df["epsilon_precision"] = epsilon_precision
        per_species_prec = prec_df.groupby("species")["epsilon_precision"].apply(agg_func)

        # Get the empirical centers per species
        empirical_centers = df_slice.groupby("species")["log2_A_vs_B"].apply(center_func)

        return {
            **{f"{agg}_log2_empirical_{sp}": v for sp, v in empirical_centers.items()},
            f"{agg}_abs_epsilon_precision_global": agg_func(epsilon_precision),
            f"{agg}_abs_epsilon_precision_eq_species": per_species_prec.mean(),
            **{f"{agg}_abs_epsilon_precision_{sp}": v for sp, v in per_species_prec.items()},
        }

    @staticmethod
    def get_cv_metrics(df: pd.DataFrame, min_nr_observed: int) -> dict[str, float]:
        """Compute CV quantiles."""
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        cv_q = df_slice[["CV_A", "CV_B"]].quantile([0.5, 0.75, 0.9, 0.95])
        cv_avg = cv_q.mean(axis=1)
        return {
            "CV_median": cv_avg.loc[0.50],
            "CV_q75": cv_avg.loc[0.75],
            "CV_q90": cv_avg.loc[0.90],
            "CV_q95": cv_avg.loc[0.95],
        }

    @staticmethod
    def get_metrics(df: pd.DataFrame, min_nr_observed: int = 3) -> Dict[int, Dict[str, float]]:
        """
        Compute statistical metrics from the provided DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate results.
        min_nr_observed : int
            Minimum number of observations threshold.

        Returns
        -------
        Dict[int, Dict[str, float]]
            Dictionary mapping quantification cutoffs to their computed metrics.
        """
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        nr_prec = len(df_slice)

        # Combine all metrics
        metrics = {
            **QuantDatapointHYE.get_epsilon_metrics(df, min_nr_observed, "median"),
            **QuantDatapointHYE.get_epsilon_metrics(df, min_nr_observed, "mean"),
            **QuantDatapointHYE.get_precision_metrics(df, min_nr_observed, "median"),
            **QuantDatapointHYE.get_precision_metrics(df, min_nr_observed, "mean"),
            **QuantDatapointHYE.get_cv_metrics(df, min_nr_observed),
            "variance_epsilon_global": df_slice["epsilon"].var() if len(df_slice) > 0 else 0.0,
            "nr_prec": nr_prec,
        }

        return {min_nr_observed: metrics}


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
                    # Global metrics (legacy key names for backward compatibility)
                    "median_abs_log2_fc_error_spike_ins": 0.0,
                    "mean_abs_log2_fc_error_spike_ins": 0.0,
                    # Species-weighted metrics
                    "median_abs_log2_fc_error_spike_ins_global": 0.0,
                    "mean_abs_log2_fc_error_spike_ins_global": 0.0,
                    "median_abs_log2_fc_error_spike_ins_eq_species": 0.0,
                    "mean_abs_log2_fc_error_spike_ins_eq_species": 0.0,
                    # Common metrics
                    "nr_quantified_spike_ins": 0,
                    "dynamic_range_human_plasma_A": 0.0,
                    "dynamic_range_human_plasma_B": 0.0,
                    "dynamic_range_human_plasma_mean": 0.0,
                    "median_abs_epsilon_human_plasma": 0.0,
                    "mean_abs_epsilon_human_plasma": 0.0,
                }
                continue

            # Compute spike-in metrics (yeast and E. coli combined)
            spike_ins_df = df_slice[df_slice["species"].isin(["YEAST", "ECOLI"])]

            # Global: Simple aggregation across all spike-ins
            median_abs_log2_fc_error_spike_ins_global = (
                spike_ins_df["epsilon"].abs().median() if len(spike_ins_df) > 0 else 0.0
            )
            mean_abs_log2_fc_error_spike_ins_global = (
                spike_ins_df["epsilon"].abs().mean() if len(spike_ins_df) > 0 else 0.0
            )

            # Species-weighted: Calculate per species, then average
            median_per_species = []
            mean_per_species = []
            for species in ["YEAST", "ECOLI"]:
                species_df = df_slice[df_slice["species"] == species]
                if len(species_df) > 0:
                    median_per_species.append(species_df["epsilon"].abs().median())
                    mean_per_species.append(species_df["epsilon"].abs().mean())

            median_abs_log2_fc_error_spike_ins_eq_species = np.mean(median_per_species) if median_per_species else 0.0
            mean_abs_log2_fc_error_spike_ins_eq_species = np.mean(mean_per_species) if mean_per_species else 0.0

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

            # Compute human plasma metrics (global only - no species weighting needed for single species)
            median_abs_epsilon_human_plasma = (
                human_plasma_df["epsilon"].abs().median() if len(human_plasma_df) > 0 else 0.0
            )
            mean_abs_epsilon_human_plasma = human_plasma_df["epsilon"].abs().mean() if len(human_plasma_df) > 0 else 0.0

            plasma_metrics[min_nr_obs] = {
                # Global metrics (legacy key names for backward compatibility)
                "median_abs_log2_fc_error_spike_ins": median_abs_log2_fc_error_spike_ins_global,
                "mean_abs_log2_fc_error_spike_ins": mean_abs_log2_fc_error_spike_ins_global,
                # Species-weighted metrics
                "median_abs_log2_fc_error_spike_ins_global": median_abs_log2_fc_error_spike_ins_global,
                "mean_abs_log2_fc_error_spike_ins_global": mean_abs_log2_fc_error_spike_ins_global,
                "median_abs_log2_fc_error_spike_ins_eq_species": median_abs_log2_fc_error_spike_ins_eq_species,
                "mean_abs_log2_fc_error_spike_ins_eq_species": mean_abs_log2_fc_error_spike_ins_eq_species,
                # Common metrics
                "nr_quantified_spike_ins": nr_quantified_spike_ins,
                "dynamic_range_human_plasma_A": dynamic_ranges.get("A", 0.0),
                "dynamic_range_human_plasma_B": dynamic_ranges.get("B", 0.0),
                "dynamic_range_human_plasma_mean": dynamic_range_human_plasma_mean if dynamic_ranges else 0.0,
                "median_abs_epsilon_human_plasma": median_abs_epsilon_human_plasma,
                "mean_abs_epsilon_human_plasma": mean_abs_epsilon_human_plasma,
            }

        return plasma_metrics
