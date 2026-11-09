"""
Reading the nested ``results`` dict a de novo datapoint stores.
"""

from typing import Optional

import numpy as np
import pandas as pd


# Metrics shown for a bin or species that a datapoint has no entry for.
EMPTY_METRICS = {"exact": 0.0, "mass": 0.0, "n_spectra": 0}


def _metrics_or_empty(value):
    """
    Return a datapoint's in-depth metrics, or empty metrics where the datapoint has none.

    Parameters
    ----------
    value : dict or float
        A ``{"exact", "mass", "n_spectra"}`` dict, or NaN/None where the datapoint lacks the bin.

    Returns
    -------
    dict
        The metrics dict itself, or a copy of `EMPTY_METRICS`.

    Raises
    ------
    TypeError
        If the value is neither a dict nor missing.
    """
    if isinstance(value, dict):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return dict(EMPTY_METRICS)
    raise TypeError(f"Expected in-depth metrics as a dict, got {type(value).__name__}: {value!r:.60}")


_LEVELS = ("peptide", "aa")

_EVALUATION_TYPES = ("mass", "exact")

_METRICS = ("precision", "recall", "coverage", "auc")


def _get_metrics_leaf(row: pd.Series, level: str, evaluation_type: str, ambiguity_combo: Optional[str] = None) -> dict:
    """
    Return the `{precision, recall, coverage, auc}` dict for one level/evaluation-type,
    optionally reading an ambiguity-toggle combination instead of the baseline.

    Ambiguity combinations only exist under exact-mode matching (mass-mode metrics are
    identical regardless, since I/L are isomeric and deamidated Q/N are isobaric with E/D
    either way), so `ambiguity_combo` is ignored for `evaluation_type == "mass"`.
    """
    leaf = row["results"][level][evaluation_type]
    if evaluation_type == "exact" and ambiguity_combo:
        return leaf["ambiguity"][ambiguity_combo]
    return leaf


def datapoint_has_required_fields(
    results_dict: dict,
    evaluation_type: str,
    needs_auc: bool,
    ambiguity_combo: Optional[str],
    needs_curve: bool = False,
) -> bool:
    """
    Check whether a datapoint's `results` dict has the fields the main plot needs for the
    currently selected evaluation type, metric (precision or AUC), and ambiguity combination.

    Used to silently hide datapoints submitted before a given field existed (e.g. `auc`,
    `curve`, or the `ambiguity` sub-dict) rather than erroring, mirroring the HYE plot
    generator's handling of legacy datapoints missing newer metric fields.
    """
    try:
        for level in _LEVELS:
            leaf = _get_metrics_leaf({"results": results_dict}, level, evaluation_type, ambiguity_combo)
            if needs_auc and "auc" not in leaf:
                return False
            if needs_curve and "curve" not in leaf:
                return False
    except (TypeError, KeyError):
        return False
    return True


def flatten_results_column(df: pd.DataFrame, ambiguity_combo: Optional[str] = None) -> pd.DataFrame:
    """
    Flatten each row's nested `results` dict into flat `{level}_{evaluation_type}_{metric}`
    columns for plotting.

    Parameters
    ----------
    ambiguity_combo : str, optional
        One of `"il"`, `"deam"`, `"both"` to read the corresponding exact-mode ambiguity
        combination instead of the baseline; `None` (default) reads the baseline. Ignored
        for mass-mode fields, which don't have ambiguity combinations (see
        `_get_metrics_leaf`).
    """
    results = {"engine": []}
    for level in _LEVELS:
        for evaluation_type in _EVALUATION_TYPES:
            for metric in _METRICS:
                results[f"{level}_{evaluation_type}_{metric}"] = []

    for _, row in df.iterrows():
        results["engine"].append(row["software_name"])
        for level in _LEVELS:
            for evaluation_type in _EVALUATION_TYPES:
                try:
                    leaf = _get_metrics_leaf(row, level, evaluation_type, ambiguity_combo)
                except (TypeError, KeyError):
                    # Every level/evaluation-type column is computed eagerly, including the one
                    # not currently selected. `datapoint_has_required_fields` only validated the
                    # selected evaluation type, so a datapoint carrying just "mass" reaches here
                    # and must yield empty columns rather than raise.
                    leaf = {}
                for metric in _METRICS:
                    # `.get(..., nan)`, not `[...]`: a legacy datapoint may lack "auc" even
                    # when it's not the metric currently being plotted (datapoint_has_
                    # required_fields already decided visibility for the active selection;
                    # this must not crash just because it computes every column eagerly).
                    results[f"{level}_{evaluation_type}_{metric}"].append(leaf.get(metric, float("nan")))

    return pd.DataFrame(results)


def _ambiguity_combo_for(evaluation_type: str, allow_il: bool, allow_deamidation: bool) -> Optional[str]:
    """
    The stored ambiguity key for a set of toggle positions.

    Ambiguity combinations only exist under exact-mode matching: mass-mode metrics are identical
    regardless, since I/L are isomeric and deamidated Q/N isobaric with E/D.
    """
    if evaluation_type != "exact":
        return None
    if allow_il and allow_deamidation:
        return "both"
    if allow_il:
        return "il"
    if allow_deamidation:
        return "deam"
    return None
