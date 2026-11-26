"""
Building the de novo result table's contents: one row per datapoint, in display order.

Deliberately free of Streamlit, so what the table would show can be tested without
rendering it.
"""

from typing import Dict, Iterable, List, Optional, Set

import pandas as pd

from proteobench.plotting.plot_generator_denovo import (
    build_variant_descriptions,
    datapoint_score,
    ordered_datapoint_columns,
)


#: Metric columns shown before the parameter columns, as (label, results-path) pairs. Mean AUC
#: comes first because it is what "best datapoint of this tool" is decided on, so the column the
#: ranking uses sits next to the name it ranks.
METRIC_COLUMNS = (
    ("Mean AUC", "mean_auc"),
    ("Pep. AUC", ("peptide", "auc")),
    ("AA AUC", ("aa", "auc")),
    ("Pep. prec.", ("peptide", "precision")),
    ("AA prec.", ("aa", "precision")),
)

#: Human-readable headers for the parameter columns. Anything absent falls back to the raw name.
COLUMN_HEADERS = {
    "software_version": "Version",
    "checkpoint": "Checkpoint",
    "decoding_strategy": "Decoding",
    "n_beams": "Beams",
    "precursor_mass_tolerance": "Prec. tol.",
    "remove_precursor_tol": "Rm prec. tol.",
    "isotope_error_range": "Isotope range",
    "n_peaks": "Peaks",
    "min_mz": "Min m/z",
    "max_mz": "Max m/z",
    "min_intensity": "Min int.",
    "max_intensity": "Max int.",
    "min_peptide_length": "Min pep. len.",
    "max_peptide_length": "Max pep. len.",
    "min_precursor_charge": "Min charge",
    "max_precursor_charge": "Max charge",
    "tokens": "Tokens",
    "id": "ProteoBench ID",
    "intermediate_hash": "Hash",
}


def header_for(column: str) -> str:
    """
    The display header for a parameter column.

    Parameters
    ----------
    column : str
        Raw column name.

    Returns
    -------
    str
        A human-readable header, or the raw name when none is registered.
    """
    return COLUMN_HEADERS.get(column, column)


def metric_value(row: pd.Series, spec, evaluation_type: str, ambiguity_combo: Optional[str]) -> Optional[float]:
    """
    Read one metric column for a datapoint.

    Parameters
    ----------
    row : pd.Series
        The datapoint.
    spec : str or tuple
        ``"mean_auc"``, or a ``(level, metric)`` pair to read from the results tree.
    evaluation_type : str
        ``"mass"`` or ``"exact"``.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination, or ``None`` for the baseline.

    Returns
    -------
    float or None
        The value, or None when this datapoint does not carry it.
    """
    from proteobench.plotting.plot_generator_denovo.results import _get_metrics_leaf

    if spec == "mean_auc":
        score = datapoint_score(row, evaluation_type, ambiguity_combo)
        return None if pd.isna(score) else float(score)
    level, metric = spec
    try:
        value = _get_metrics_leaf(row, level, evaluation_type, ambiguity_combo).get(metric)
    except (KeyError, TypeError):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool) and not pd.isna(value):
        return float(value)
    return None


def row_order(
    result_df: pd.DataFrame,
    ranks: pd.Series,
    best_by_tool: Dict[str, object],
    evaluation_type: str,
    ambiguity_combo: Optional[str] = None,
) -> List[object]:
    """
    Order the rows tool by tool, best tool first and best datapoint first within each tool.

    This ordering is what carries the grouping that collapsible rows would otherwise provide: a
    tool's submissions sit together, and the row the figures colour by default is the first of
    each block. The viewer can re-sort any column afterwards, which is handled client-side and
    costs no rerun.

    Parameters
    ----------
    result_df : pd.DataFrame
        The datapoints to order.
    ranks : pd.Series
        Ranks within each tool, from :func:`rank_within_tools`.
    best_by_tool : dict
        Tool name to the index of its best datapoint.
    evaluation_type : str
        Evaluation type the ranking is based on.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination the ranking is based on.

    Returns
    -------
    list
        Frame indices in display order.
    """
    if len(result_df) == 0:
        return []
    software = result_df["software_name"].astype(str)

    def tool_score(tool: str) -> float:
        if tool not in best_by_tool:
            return float("-inf")
        score = datapoint_score(result_df.loc[best_by_tool[tool]], evaluation_type, ambiguity_combo)
        return float("-inf") if pd.isna(score) else float(score)

    tools = sorted(software.unique(), key=lambda tool: -tool_score(tool))
    ordered: List[object] = []
    for tool in tools:
        members = [idx for idx in result_df.index if software.at[idx] == tool]
        members.sort(key=lambda idx: int(ranks.at[idx]) if idx in ranks.index else 0)
        ordered.extend(members)
    return ordered


def build_table_frame(
    result_df: pd.DataFrame,
    columns: Iterable[str],
    labels: pd.Series,
    ranks: pd.Series,
    best_by_tool: Dict[str, object],
    selected_ids: Set[str],
    evaluation_type: str,
    ambiguity_combo: Optional[str] = None,
    variants: Optional[pd.Series] = None,
    show_variants: bool = True,
) -> pd.DataFrame:
    """
    Build the editable frame for every datapoint, one row each.

    Parameters
    ----------
    result_df : pd.DataFrame
        All datapoints.
    columns : Iterable of str
        Parameter columns to include, already filtered to the visible set.
    labels : pd.Series
        Display labels for every datapoint.
    ranks : pd.Series
        Ranks within each tool, from :func:`rank_within_tools`.
    best_by_tool : dict
        Tool name to the index of its best datapoint.
    selected_ids : set of str
        ProteoBench IDs currently selected.
    evaluation_type : str
        ``"mass"`` or ``"exact"``.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination.
    variants : pd.Series, optional
        What sets each datapoint apart from its own tool's other submissions, from
        :func:`build_variant_descriptions`. Computed from ``result_df`` when not given.
    show_variants : bool
        Whether to carry the ``Parameters`` column at all.

    Returns
    -------
    pd.DataFrame
        One row per datapoint, ordered by :func:`row_order`, with a hidden ``_id`` column.
    """
    if variants is None:
        variants = build_variant_descriptions(result_df)
    rows = []
    for idx in row_order(result_df, ranks, best_by_tool, evaluation_type, ambiguity_combo):
        row = result_df.loc[idx]
        point_id = str(row.get("id", ""))
        tool = str(row.get("software_name", ""))
        record = {
            "Show": point_id in selected_ids,
            # The star marks the datapoint the figures colour by default for this tool.
            "Tool": f"{tool} ★" if best_by_tool.get(tool) == idx else tool,
            "Datapoint": labels.at[idx],
        }
        if show_variants:
            # Beside the name rather than inside it: the name stays short and sortable, and the
            # settings that actually separate a tool's runs get a column the reader can widen,
            # sort and copy out of.
            record["Parameters"] = str(variants.at[idx]) if idx in variants.index else ""
        record["Rank"] = int(ranks.at[idx]) if idx in ranks.index else 0
        for label, spec in METRIC_COLUMNS:
            record[label] = metric_value(row, spec, evaluation_type, ambiguity_combo)
        for column in columns:
            value = row.get(column)
            record[header_for(column)] = "" if pd.isna(value) or value is None else str(value)
        record["_id"] = point_id
        rows.append(record)
    return pd.DataFrame(rows)


def _visible_columns(classes: Dict[str, List[str]], hidden: Set[str]) -> List[str]:
    """
    The ordered parameter columns that are not hidden.

    Parameters
    ----------
    classes : dict
        Column class name to the columns it contains.
    hidden : set of str
        Columns to leave out.

    Returns
    -------
    list of str
        The visible columns, in display order.
    """
    return [column for column in ordered_datapoint_columns(classes) if column not in hidden]
