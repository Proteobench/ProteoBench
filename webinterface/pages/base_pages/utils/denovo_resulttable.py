"""
Result table for the de novo module.

The quant modules render their datapoints as one flat ag-grid row each (see ``resulttable.py``,
which is shared by every quant tab and is deliberately left alone). That works when a tool
appears once. A de novo tool can be submitted many times, one datapoint per decoding strategy or
checkpoint, and then a flat table repeats the tool name down the page while the differences sit
in scattered parameter columns, most of which are identical across the very rows being compared.

This table instead groups by tool. Each tool is one expandable row showing its best datapoint;
opening it reveals that tool's own submissions, ranked, with the columns that differ between
them highlighted and the rest greyed. Which columns are shown at all is decided by how far they
discriminate, so the ProteoBench ID and the intermediate hash stop occupying the space next to
the tool name.

Nothing here is imported by the quant tabs; the de novo page calls it instead of
``tab1.render_results_table``.
"""

import uuid
from typing import Dict, Iterable, List, Optional, Set

import pandas as pd
import streamlit as st

from proteobench.plotting.plot_generator_denovo import (
    build_display_labels,
    classify_datapoint_columns,
    columns_varying_within_tool,
    default_hidden_columns,
    ordered_datapoint_columns,
    rank_within_tools,
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

#: What each column class means, shown beside its group in the column picker so the grouping is
#: self-explaining rather than something the reader has to infer.
CLASS_DESCRIPTIONS = {
    "discriminating": "Differ within a tool - these tell a tool's own runs apart",
    "contextual": "Differ between tools only - cannot separate one tool's runs",
    "uniform": "Same for every datapoint - no information in this set",
    "identifier": "Identifiers - unique but unreadable",
}

#: Column presets offered above the table, as (key, button label, which classes to show).
COLUMN_PRESETS = (
    ("default", "Default", ("discriminating",)),
    ("context", "Add between-tool context", ("discriminating", "contextual", "uniform")),
    ("all", "Show all", ("discriminating", "contextual", "uniform", "identifier")),
)


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
    from proteobench.plotting.plot_generator_denovo import _get_metrics_leaf, datapoint_score

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


def build_group_frame(
    result_df: pd.DataFrame,
    tool: str,
    columns: Iterable[str],
    labels: pd.Series,
    ranks: pd.Series,
    best_index,
    selected_ids: Set[str],
    evaluation_type: str,
    ambiguity_combo: Optional[str] = None,
) -> pd.DataFrame:
    """
    Build the editable frame for one tool's submissions, ranked best first.

    Parameters
    ----------
    result_df : pd.DataFrame
        All datapoints.
    tool : str
        The tool whose submissions to tabulate.
    columns : Iterable of str
        Parameter columns to include, already filtered to the visible set.
    labels : pd.Series
        Display labels for every datapoint.
    ranks : pd.Series
        Ranks within each tool, from :func:`rank_within_tools`.
    best_index : object
        Index of this tool's best datapoint, or None.
    selected_ids : set of str
        ProteoBench IDs currently selected.
    evaluation_type : str
        ``"mass"`` or ``"exact"``.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination.

    Returns
    -------
    pd.DataFrame
        One row per submission, with a leading ``Show`` checkbox column.
    """
    group = result_df[result_df["software_name"].astype(str) == str(tool)]
    order = sorted(group.index, key=lambda idx: int(ranks.at[idx]) if idx in ranks.index else 0)

    rows = []
    for idx in order:
        row = result_df.loc[idx]
        point_id = str(row.get("id", ""))
        record = {
            "Show": point_id in selected_ids,
            "Datapoint": labels.at[idx] + (" ★" if idx == best_index else ""),
            "Rank": int(ranks.at[idx]) if idx in ranks.index else 0,
        }
        for label, spec in METRIC_COLUMNS:
            record[label] = metric_value(row, spec, evaluation_type, ambiguity_combo)
        for column in columns:
            value = row.get(column)
            record[header_for(column)] = "" if pd.isna(value) or value is None else str(value)
        record["_id"] = point_id
        rows.append(record)
    return pd.DataFrame(rows)


def _visible_columns(classes: Dict[str, List[str]], hidden: Set[str]) -> List[str]:
    """The ordered parameter columns that are not hidden."""
    return [column for column in ordered_datapoint_columns(classes) if column not in hidden]


def _render_column_picker(state_key: str, classes: Dict[str, List[str]], hidden: Set[str]) -> Set[str]:
    """
    Render the column picker and return the updated hidden set.

    Grouped by column class, with each group's meaning spelled out, so that hiding a column is an
    informed choice rather than a guess at what the grouping means.
    """
    all_columns = ordered_datapoint_columns(classes)
    shown = len(all_columns) - len(hidden & set(all_columns))
    with st.expander(f"Columns ({shown} of {len(all_columns)} shown)", expanded=False):
        preset_cols = st.columns(len(COLUMN_PRESETS))
        for container, (key, label, visible_classes) in zip(preset_cols, COLUMN_PRESETS):
            if container.button(label, key=f"{state_key}_preset_{key}", use_container_width=True):
                hidden = {
                    column for name, members in classes.items() if name not in visible_classes for column in members
                }
                st.session_state[state_key] = hidden
                st.rerun()

        for name in ("discriminating", "contextual", "uniform", "identifier"):
            members = classes.get(name, [])
            if not members:
                continue
            st.caption(CLASS_DESCRIPTIONS[name])
            chosen = st.multiselect(
                CLASS_DESCRIPTIONS[name],
                options=members,
                default=[column for column in members if column not in hidden],
                format_func=header_for,
                key=f"{state_key}_pick_{name}",
                label_visibility="collapsed",
            )
            hidden = (hidden - set(members)) | (set(members) - set(chosen))
    return hidden


def render_denovo_result_table(
    result_df: pd.DataFrame,
    state_prefix: str,
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
    selected_ids: Optional[Iterable[str]] = None,
    label_style: str = "index",
    custom_labels: Optional[Dict[object, str]] = None,
) -> Set[str]:
    """
    Render the grouped de novo result table and return the selected ProteoBench IDs.

    One expander per tool, titled with how many of its submissions are selected and which is its
    best. Inside, that tool's submissions are listed best first, with a ``Show`` checkbox that
    drives the figures. Columns that differ within the tool are kept; the rest are available
    through the column picker.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to display. Must carry ``software_name``, ``id`` and ``results``.
    state_prefix : str
        Prefix for this table's session-state keys, so two tables on one page stay independent.
    evaluation_type : str
        ``"mass"`` or ``"exact"``, which decides the ranking and the metric columns.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination.
    selected_ids : Iterable of str, optional
        IDs selected on entry. Defaults to each tool's best datapoint.
    label_style : str
        One of ``LABEL_STYLES``, naming each datapoint.
    custom_labels : dict, optional
        Index to label, for the ``"custom"`` style.

    Returns
    -------
    set of str
        The ProteoBench IDs the viewer has selected.
    """
    if result_df is None or len(result_df) == 0:
        st.info("No results available yet.", icon="ℹ️")
        return set()

    ranks, best_by_tool = rank_within_tools(result_df, evaluation_type, ambiguity_combo)
    labels = build_display_labels(result_df, style=label_style, ranks=ranks, custom_labels=custom_labels)
    classes = classify_datapoint_columns(result_df)

    hidden_key = f"{state_prefix}_hidden_columns"
    if hidden_key not in st.session_state:
        st.session_state[hidden_key] = set(default_hidden_columns(classes))
    st.session_state[hidden_key] = _render_column_picker(hidden_key, classes, set(st.session_state[hidden_key]))
    visible = _visible_columns(classes, set(st.session_state[hidden_key]))

    selection_key = f"{state_prefix}_selected_ids"
    if selection_key not in st.session_state:
        default = {str(result_df.at[idx, "id"]) for idx in best_by_tool.values() if "id" in result_df.columns}
        st.session_state[selection_key] = default
    if selected_ids is not None:
        st.session_state[selection_key] = {str(point_id) for point_id in selected_ids}
    selected = set(st.session_state[selection_key])

    # Tools ordered best first, so the table reads in the same order as the legend.
    tools = sorted(
        result_df["software_name"].astype(str).unique(),
        key=lambda tool: -(
            metric_value(result_df.loc[best_by_tool[tool]], "mean_auc", evaluation_type, ambiguity_combo) or -1.0
        )
        if tool in best_by_tool
        else 1.0,
    )

    for tool in tools:
        group_ids = {
            str(result_df.at[idx, "id"]) for idx in result_df.index if str(result_df.at[idx, "software_name"]) == tool
        }
        picked = len(group_ids & selected)
        best_index = best_by_tool.get(tool)
        best_label = labels.at[best_index] if best_index is not None else "—"
        varying = columns_varying_within_tool(result_df, tool, visible)

        title = f"{tool}  ·  {picked}/{len(group_ids)} shown  ·  best: {best_label}"
        with st.expander(title, expanded=False):
            if varying:
                st.caption("Differs within this tool: " + ", ".join(header_for(c) for c in varying))
            else:
                st.caption("No recorded parameter differs between this tool's submissions.")

            frame = build_group_frame(
                result_df,
                tool,
                visible,
                labels,
                ranks,
                best_index,
                selected,
                evaluation_type,
                ambiguity_combo,
            )
            edited = st.data_editor(
                frame.drop(columns=["_id"]),
                key=f"{state_prefix}_editor_{tool}",
                hide_index=True,
                use_container_width=True,
                disabled=[c for c in frame.columns if c not in ("Show", "_id")],
                column_config={
                    "Show": st.column_config.CheckboxColumn("Show", help="Draw this datapoint in the figures"),
                    "Rank": st.column_config.NumberColumn("Rank", help="Rank within this tool, by mean AUC"),
                    **{label: st.column_config.NumberColumn(label, format="%.3f") for label, _ in METRIC_COLUMNS},
                },
            )
            for position, point_id in enumerate(frame["_id"]):
                if bool(edited.iloc[position]["Show"]):
                    selected.add(point_id)
                else:
                    selected.discard(point_id)

    st.session_state[selection_key] = selected
    return selected


def new_table_state_prefix(variables) -> str:
    """
    A stable session-state prefix for this module's table.

    Parameters
    ----------
    variables : object
        The page's Variables instance, used to keep the prefix unique per module.

    Returns
    -------
    str
        A prefix derived from the module's own figure key, with a UUID fallback.
    """
    base = getattr(variables, "fig_metric", None) or str(uuid.uuid4())
    return f"{base}_denovo_table"
