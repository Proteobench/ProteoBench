"""
Scoring a datapoint and ranking a tool's submissions against each other.
"""

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from proteobench.plotting.plot_generator_denovo.results import _LEVELS, _get_metrics_leaf


def datapoint_score(row: pd.Series, evaluation_type: str = "mass", ambiguity_combo: Optional[str] = None) -> float:
    """
    Rank a datapoint by the mean of its peptide-level and amino-acid-level AUC.

    This is the single quantity "best datapoint of this tool" is decided on. Both levels are
    required: a datapoint carrying only one of them cannot be compared against one carrying
    both, so it scores as missing rather than being ranked on half the evidence.

    Parameters
    ----------
    row : pd.Series
        One datapoint, carrying the nested ``results`` dict.
    evaluation_type : str
        Evaluation type to read, ``"mass"`` or ``"exact"``.
    ambiguity_combo : str, optional
        One of ``"il"``, ``"deam"``, ``"both"`` to read that exact-mode ambiguity combination;
        ``None`` reads the baseline.

    Returns
    -------
    float
        The mean of the two AUC values, or NaN when either is absent.
    """
    values = []
    for level in _LEVELS:
        try:
            auc = _get_metrics_leaf(row, level, evaluation_type, ambiguity_combo).get("auc")
        except (KeyError, TypeError, IndexError):
            # `_get_metrics_leaf` indexes straight into the nested dict, so a legacy datapoint
            # missing a level, an evaluation type or the whole `results` block raises here.
            # Such a datapoint is simply unrankable; it must not take the page down with it.
            return float("nan")
        if isinstance(auc, (int, float)) and not isinstance(auc, bool) and not np.isnan(auc):
            values.append(float(auc))
    if len(values) < len(_LEVELS):
        return float("nan")
    return sum(values) / len(values)


def rank_within_tools(
    result_df: pd.DataFrame, evaluation_type: str = "mass", ambiguity_combo: Optional[str] = None
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Rank each datapoint against the other submissions of its own tool.

    Ranking per tool rather than globally is what keeps the display from being biased by how
    many times a tool was submitted: every tool contributes one rank-1 datapoint regardless of
    whether it was submitted once or fifteen times.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to rank. Must carry ``software_name`` and ``results``.
    evaluation_type : str
        Evaluation type to rank on, ``"mass"`` or ``"exact"``.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination to rank on; ``None`` reads the baseline.

    Returns
    -------
    tuple of (pd.Series, dict)
        The 1-based rank of each datapoint within its tool, aligned to ``result_df.index``, and
        a mapping of tool name to the index of its best datapoint. A tool whose datapoints are
        all unscorable is absent from the mapping, and its datapoints still receive a rank so
        that nothing is left unlabelled.
    """
    if "software_name" not in result_df.columns or len(result_df) == 0:
        return pd.Series(dtype="int64"), {}

    scores = pd.Series(
        [datapoint_score(row, evaluation_type, ambiguity_combo) for _, row in result_df.iterrows()],
        index=result_df.index,
        dtype=float,
    )
    ranks = pd.Series(0, index=result_df.index, dtype="int64")
    best: Dict[str, Any] = {}

    for tool, group in result_df.groupby(result_df["software_name"].astype(str), sort=False):
        # mergesort keeps submission order among ties, so an unchanged dataset ranks the same
        # way every time rather than reshuffling equal-scoring runs between reruns.
        ordered = scores.loc[group.index].sort_values(ascending=False, kind="mergesort", na_position="last")
        for position, idx in enumerate(ordered.index, start=1):
            ranks.at[idx] = position
        scorable = ordered.dropna()
        if len(scorable) > 0:
            best[str(tool)] = scorable.index[0]

    return ranks, best


def leading_datapoints(result_df: pd.DataFrame, coloured: pd.Series, ranks: pd.Series) -> set:
    """
    The best coloured datapoint of each tool.

    "Coloured" says a datapoint is drawn in its tool's colour; it no longer says the datapoint
    is that tool's representative, because a selection may hold every run a tool submitted. This
    picks the one of each tool that is drawn at full strength.

    Parameters
    ----------
    result_df : pd.DataFrame
        The datapoints being drawn. Must carry ``software_name``.
    coloured : pd.Series
        Boolean Series from :func:`resolve_coloured_datapoints`.
    ranks : pd.Series
        Ranks within each tool, from :func:`rank_within_tools`.

    Returns
    -------
    set
        Frame indices of the best coloured datapoint of each tool.
    """
    if len(result_df) == 0:
        return set()
    software = (
        result_df["software_name"].astype(str)
        if "software_name" in result_df.columns
        else pd.Series("Custom", index=result_df.index)
    )
    best: dict = {}
    for idx in result_df.index:
        if not bool(coloured.at[idx]):
            continue
        tool = software.at[idx]
        rank = int(ranks.at[idx]) if idx in ranks.index else 0
        if tool not in best or rank < best[tool][0]:
            best[tool] = (rank, idx)
    return {idx for _rank, idx in best.values()}
