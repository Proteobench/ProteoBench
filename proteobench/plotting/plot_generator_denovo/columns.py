"""
Classifying a datapoint's parameter columns by what they can tell apart.
"""

from typing import Dict, Iterable, List, Mapping, Optional

import pandas as pd

from proteobench.plotting.plot_generator_denovo.results import _LEVELS
from proteobench.plotting.plot_generator_denovo.labels import _is_blank


#: Columns that identify a datapoint uniquely but say nothing about how it was produced. Being
#: unique makes them trivially the most "discriminating" columns, which is exactly why they are
#: ranked separately: sorting on discrimination would otherwise put them first, where they are
#: the widest and least informative thing on screen.
IDENTIFIER_COLUMNS = ("id", "intermediate_hash")

#: Columns that are not run parameters and so never belong in the parameter table: metric
#: payloads, display bookkeeping, and the flat metric fields the figures read instead.
_NON_PARAMETER_COLUMNS = frozenset(
    {
        "results",
        "old_new",
        "is_temporary",
        "Highlight",
        "selected",
        "open_source",
        "color",
        "opacity",
        "line_width",
        "marker",
        "hover_text",
        "scatter_size",
        "display_label",
        "is_coloured",
        "engine",
        "precision_peptide",
        "precision_aa",
        "recall_peptide",
        "recall_aa",
        "proteobench_version",
        "comments",
        "submission_comments",
        "nr_feature",
        "nr_prec",
    }
)


def columns_varying_within_tool(result_df: pd.DataFrame, tool: str, columns: Iterable[str]) -> List[str]:
    """
    The columns on which one tool's own datapoints differ from each other.

    A column needs two distinct non-blank values within the tool to count: a value every
    submission of a tool shares cannot tell those submissions apart, which is the only job this
    distinction has.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to inspect. Must carry ``software_name``.
    tool : str
        The tool whose submissions are compared against each other.
    columns : Iterable of str
        Columns to consider.

    Returns
    -------
    list of str
        The subset of ``columns`` that differ within this tool, in the given order.
    """
    if "software_name" not in result_df.columns:
        return []
    group = result_df[result_df["software_name"].astype(str) == str(tool)]
    varying = []
    for column in columns:
        if column not in group.columns:
            continue
        seen = {str(value).strip() for value in group[column] if not _is_blank(value)}
        if len(seen) > 1:
            varying.append(column)
    return varying


def classify_datapoint_columns(
    result_df: pd.DataFrame,
    columns: Optional[Iterable[str]] = None,
) -> Dict[str, List[str]]:
    """
    Sort datapoint columns by how far they actually discriminate.

    This decides both the column order of the result table and what it hides by default. A table
    that leads with the ProteoBench ID and the intermediate hash puts its two widest and least
    informative columns where the eye lands first.

    The four classes:

    - ``discriminating``: differs between at least one tool's own datapoints. These are what tell
      a tool's repeat submissions apart, so they belong closest to the tool name.
    - ``contextual``: constant within every tool but not across the set. Useful background, but
      it cannot separate one tool's submissions from each other.
    - ``uniform``: one value, or none, across the whole set. Carries no information here.
    - ``identifier``: :data:`IDENTIFIER_COLUMNS`, kept out of the ranking deliberately.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to classify.
    columns : Iterable of str, optional
        Columns to classify. Defaults to every column that is not a metric payload or display
        bookkeeping, and that at least one datapoint fills in.

    Returns
    -------
    dict
        Maps each class name to its columns. Classes with no columns map to an empty list.
    """
    if columns is None:
        columns = [
            column
            for column in result_df.columns
            if column not in _NON_PARAMETER_COLUMNS
            and not any(column.startswith(f"{level}_") for level in _LEVELS)
            and any(not _is_blank(value) for value in result_df[column])
        ]
    columns = [column for column in columns if column != "software_name"]

    classes: Dict[str, List[str]] = {name: [] for name in ("discriminating", "contextual", "uniform", "identifier")}
    if len(result_df) == 0:
        classes["identifier"] = [c for c in columns if c in IDENTIFIER_COLUMNS]
        classes["uniform"] = [c for c in columns if c not in IDENTIFIER_COLUMNS]
        return classes

    tools = result_df["software_name"].astype(str).unique() if "software_name" in result_df.columns else []
    for column in columns:
        if column in IDENTIFIER_COLUMNS:
            classes["identifier"].append(column)
            continue
        if any(columns_varying_within_tool(result_df, tool, [column]) for tool in tools):
            classes["discriminating"].append(column)
            continue
        distinct = {str(value).strip() for value in result_df[column] if not _is_blank(value)}
        classes["contextual" if len(distinct) > 1 else "uniform"].append(column)
    return classes


def ordered_datapoint_columns(classes: Mapping[str, List[str]]) -> List[str]:
    """
    Flatten a classification into display order, most discriminating first.

    Parameters
    ----------
    classes : Mapping
        As returned by :func:`classify_datapoint_columns`.

    Returns
    -------
    list of str
        Column names, discriminating first and identifiers last.
    """
    return [
        column for name in ("discriminating", "contextual", "uniform", "identifier") for column in classes.get(name, [])
    ]


def default_hidden_columns(classes: Mapping[str, List[str]]) -> List[str]:
    """
    The columns a table hides until asked.

    Only the columns that differ within some tool are shown. A column constant within every tool
    cannot separate a tool's own submissions, which is what the table is for, so it is context to
    reveal rather than width to pay for up front.

    Parameters
    ----------
    classes : Mapping
        As returned by :func:`classify_datapoint_columns`.

    Returns
    -------
    list of str
        Column names to hide by default.
    """
    return [column for name in ("contextual", "uniform", "identifier") for column in classes.get(name, [])]
