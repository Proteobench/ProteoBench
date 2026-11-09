"""
Result table for the de novo module.

The quant modules render their datapoints as one flat ag-grid row each (see ``resulttable.py``,
which is shared by every quant tab and is deliberately left alone). That works when a tool appears
once. A de novo tool can be submitted many times, one datapoint per decoding strategy or
checkpoint, and then a flat table repeats the tool name down the page while the differences sit in
scattered parameter columns, most of which are identical across the very rows being compared.

This table is still one flat table, but it earns its shape differently: rows are ordered tool by
tool and best first within each tool, a ``Show`` checkbox decides what the figures draw, and only
the columns that actually differ within some tool are shown by default.

Why not grouped, collapsible rows, which is what the information really wants: AG Grid's row
grouping and master/detail are Enterprise features, and ProteoBench is Apache-2.0 and enables
neither. An earlier version of this module faked grouping with one ``st.expander`` per tool, each
holding its own small editor. That gave the machinery of grouping without its benefit, cost a
widget per tool, and collapsed itself on every rerun because the expander labels carried live
counts. One sortable table is the honest option in this stack.

Selection lives in the ``Show`` column rather than in a widget's own selection state, because
``st.dataframe``'s row selection cannot be set programmatically and the presets have to be able to
write a selection.

Nothing here is imported by the quant tabs; the de novo page calls it instead of
``tab1.render_results_table``.
"""

import uuid
from typing import Dict, Iterable, List, NamedTuple, Optional, Set

import pandas as pd
import streamlit as st

from proteobench.plotting.plot_generator_denovo import (
    build_display_labels,
    build_variant_descriptions,
    classify_datapoint_columns,
    columns_varying_within_tool,
    datapoint_score,
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

#: Columns the table always carries, before the metrics and parameters. ``Parameters`` is the
#: one that can be switched off: it repeats, in one cell, what the separate parameter columns
#: further right already say field by field.
IDENTITY_COLUMNS = ("Show", "Tool", "Datapoint", "Parameters", "Rank")

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

#: Column presets, as (key, button label, which classes to show).
COLUMN_PRESETS = (
    ("default", "Default", ("discriminating",)),
    ("context", "Add between-tool context", ("discriminating", "contextual", "uniform")),
    ("all", "Show all", ("discriminating", "contextual", "uniform", "identifier")),
)

#: Row height and chrome used to size the table, in pixels, and the bounds it is kept within.
ROW_HEIGHT = 35
TABLE_CHROME = 38
MIN_TABLE_HEIGHT = 150
MAX_TABLE_HEIGHT = 560


def table_height(rows: int) -> int:
    """
    Pixel height for a table of ``rows`` rows.

    A fixed height gave five datapoints the same tall, mostly empty box as two hundred. This
    grows with the content and stops before the table pushes the figures off the page.

    Parameters
    ----------
    rows : int
        Number of rows the table will show.

    Returns
    -------
    int
        The height to pass to ``st.data_editor``.
    """
    wanted = TABLE_CHROME + max(rows, 1) * ROW_HEIGHT
    return max(MIN_TABLE_HEIGHT, min(wanted, MAX_TABLE_HEIGHT))


class DenovoTableResult(NamedTuple):
    """
    What the table hands back to the page.

    Attributes
    ----------
    selected_ids : set of str
        ProteoBench IDs the viewer has ticked, which decide what the figures draw.
    custom_labels : dict
        ProteoBench ID to the label the viewer typed for it. Empty unless labels are editable.
    """

    selected_ids: Set[str]
    custom_labels: Dict[str, str]


def custom_labels_by_index(result_df: pd.DataFrame, by_id: Dict[str, str]) -> Dict[object, str]:
    """
    Translate ID-keyed custom labels to the index keys ``build_display_labels`` expects.

    Labels are stored against the ProteoBench ID rather than the frame index, because the index is
    rebuilt whenever the datapoints are reloaded or refiltered and would silently reassign a
    viewer's labels to different runs.

    Parameters
    ----------
    result_df : pd.DataFrame
        The datapoints currently on display.
    by_id : dict
        ProteoBench ID to label.

    Returns
    -------
    dict
        Frame index to label, for the IDs present in this frame.
    """
    if not by_id or "id" not in result_df.columns:
        return {}
    return {
        idx: by_id[str(result_df.at[idx, "id"])] for idx in result_df.index if str(result_df.at[idx, "id"]) in by_id
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
    from proteobench.plotting.plot_generator_denovo import _get_metrics_leaf

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
    editable_labels: bool = False,
    custom_labels: Optional[Dict[str, str]] = None,
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
    editable_labels : bool
        Whether to include an editable ``Label`` column.
    custom_labels : dict, optional
        ProteoBench ID to the label typed for it.
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
        if editable_labels:
            record["Label"] = (custom_labels or {}).get(point_id, "")
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


def _render_column_picker(state_key: str, variant_key: str, classes: Dict[str, List[str]], hidden: Set[str]) -> tuple:
    """
    Render the column picker and return the updated hidden set.

    The label says what the control does rather than naming the thing it acts on: "Columns" on a
    collapsed expander above a table full of columns reads as a heading, not as something to
    open. It is deliberately static, though. An earlier version put the shown/total count in it,
    which changed the element's props on every interaction and made it collapse under the
    viewer.

    Parameters
    ----------
    state_key : str
        Session-state key holding this picker's hidden-column set.
    variant_key : str
        Session-state key holding the ``Parameters`` column's checkbox.
    classes : dict
        Column class name to the columns it contains.
    hidden : set of str
        Columns hidden on entry.

    Returns
    -------
    tuple
        The columns that should stay hidden, and whether to show the ``Parameters`` column.
    """
    all_columns = ordered_datapoint_columns(classes)
    with st.expander("Choose which columns to show", expanded=False, icon=":material/view_column:"):
        shown = len(all_columns) - len(hidden & set(all_columns))
        st.caption(f"{shown} of {len(all_columns)} parameter columns shown.")

        show_variants = st.checkbox(
            "Parameters column",
            value=True,
            key=variant_key,
            help=(
                "One cell per run naming what sets it apart from the same tool's other "
                "submissions. The columns below say the same thing field by field."
            ),
        )

        preset_cols = st.columns(len(COLUMN_PRESETS))
        for container, (key, label, visible_classes) in zip(preset_cols, COLUMN_PRESETS):
            if container.button(label, key=f"{state_key}_preset_{key}", width="stretch"):
                st.session_state[state_key] = {
                    column for name, members in classes.items() if name not in visible_classes for column in members
                }
                st.rerun()

        for name in ("discriminating", "contextual", "uniform", "identifier"):
            members = classes.get(name, [])
            if not members:
                continue
            chosen = st.multiselect(
                CLASS_DESCRIPTIONS[name],
                options=members,
                default=[column for column in members if column not in hidden],
                format_func=header_for,
                key=f"{state_key}_pick_{name}",
            )
            hidden = (hidden - set(members)) | (set(members) - set(chosen))
    return hidden, show_variants


def sync_selection_from_editor(editor_key: str, order_key: str, selection_key: str) -> None:
    """
    Fold a tick made in the editor into the stored selection, before the page redraws.

    The figures on the main tabs are drawn *above* this table, so they are built before
    ``st.data_editor`` has returned and would otherwise read the selection as it stood on the
    previous run: a tick only reached the plot one interaction later, which is the "I need to
    click a couple before anything changes" the tabs showed. A widget callback runs before the
    script body of the rerun the tick triggers, so by the time the figure is built the selection
    already includes it.

    Parameters
    ----------
    editor_key : str
        Session-state key of the ``st.data_editor`` whose edits to read.
    order_key : str
        Session-state key holding the row order the edits were made against.
    selection_key : str
        Session-state key holding the set of selected ProteoBench IDs.
    """
    state = st.session_state.get(editor_key) or {}
    order = st.session_state.get(order_key) or []
    selected = set(st.session_state.get(selection_key) or set())
    for position, changes in (state.get("edited_rows") or {}).items():
        if "Show" not in changes:
            continue
        try:
            point_id = order[int(position)]
        except (ValueError, TypeError, IndexError):
            continue
        if changes["Show"]:
            selected.add(point_id)
        else:
            selected.discard(point_id)
    st.session_state[selection_key] = selected


def _render_row_controls(
    result_df: pd.DataFrame,
    state_prefix: str,
    selection_key: str,
    best_by_tool: Dict[str, object],
) -> List[str]:
    """
    Render the tool filter and the bulk-tick buttons that sit above the table.

    At a couple of hundred datapoints the table is far longer than the window, so it needs a way
    to narrow the rows and to tick them in bulk: hunting one checkbox in two hundred rows is not
    a workable way to drive the figures.

    Parameters
    ----------
    result_df : pd.DataFrame
        All datapoints, before any filtering.
    state_prefix : str
        Prefix for this table's session-state keys.
    selection_key : str
        Session-state key holding the set of selected ProteoBench IDs.
    best_by_tool : dict
        Tool name to the index of its best datapoint.

    Returns
    -------
    list of str
        The tools whose rows to show, empty for all of them.
    """
    tools = sorted(result_df["software_name"].astype(str).unique())
    has_ids = "id" in result_df.columns
    generation_key = f"{state_prefix}_editor_generation"

    def apply_bulk(ids: Set[str]) -> None:
        """Replace the selection wholesale and drop the editor's pending cell edits."""
        st.session_state[selection_key] = set(ids)
        st.session_state[generation_key] = int(st.session_state.get(generation_key, 0)) + 1
        st.rerun()

    # `vertical_alignment="bottom"` so the buttons sit on the same line as the multiselect's
    # input box rather than floating level with its label, and icons so they read as controls
    # rather than as three boxes that happen to be there.
    filter_col, button_col = st.columns([2, 3], vertical_alignment="bottom")
    shown_tools = filter_col.multiselect(
        "Show rows for",
        options=tools,
        default=[],
        key=f"{state_prefix}_tool_filter",
        placeholder="All tools",
        help="Narrows the rows in this table only. Ticks you have already made are kept.",
    )

    bulk = button_col.columns(3)
    if bulk[0].button(
        "Tick all",
        key=f"{state_prefix}_tick_all",
        icon=":material/select_all:",
        help="Draw every datapoint in the figures.",
        width="stretch",
    ):
        apply_bulk({str(point_id) for point_id in result_df["id"]} if has_ids else set())
    if bulk[1].button(
        "Tick none",
        key=f"{state_prefix}_tick_none",
        icon=":material/deselect:",
        help="Clear the figures, then tick the datapoints you want to compare.",
        width="stretch",
    ):
        apply_bulk(set())
    if bulk[2].button(
        "Best per tool",
        key=f"{state_prefix}_tick_best",
        icon=":material/star:",
        help="One datapoint per tool, each tool's highest mean AUC.",
        width="stretch",
    ):
        apply_bulk({str(result_df.at[idx, "id"]) for idx in best_by_tool.values() if has_ids})
    return shown_tools


def _reconcile_edits(
    frame: pd.DataFrame,
    edited: pd.DataFrame,
    selected: Set[str],
    typed_labels: Dict[str, str],
    editable_labels: bool,
) -> None:
    """
    Fold the editor's returned frame back into the selection and the typed labels, in place.

    ``edited`` comes back in ``frame``'s own row order -- column sorting is client-side only and
    never reaches Python -- so position lines the two up. Rows the tool filter left out are
    absent from both and keep whatever tick they already had.

    Parameters
    ----------
    frame : pd.DataFrame
        The frame handed to the editor, carrying the hidden ``_id`` column.
    edited : pd.DataFrame
        What the editor returned.
    selected : set of str
        Selected ProteoBench IDs, updated in place.
    typed_labels : dict
        ProteoBench ID to label, updated in place.
    editable_labels : bool
        Whether the editor carried a ``Label`` column.
    """
    for position, point_id in enumerate(frame["_id"]):
        if bool(edited.iloc[position]["Show"]):
            selected.add(point_id)
        else:
            selected.discard(point_id)
        if not editable_labels:
            continue
        typed = str(edited.iloc[position].get("Label", "") or "").strip()
        if typed:
            typed_labels[point_id] = typed
        else:
            typed_labels.pop(point_id, None)


def render_denovo_result_table(
    result_df: pd.DataFrame,
    state_prefix: str,
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
    selected_ids: Optional[Iterable[str]] = None,
    label_style: str = "index",
    custom_labels: Optional[Dict[str, str]] = None,
    editable_labels: bool = False,
    default_selection: str = "best",
) -> DenovoTableResult:
    """
    Render the de novo result table and return the selected ProteoBench IDs.

    One table, one row per datapoint, ordered tool by tool and best first within each tool. The
    ``Show`` checkbox decides what the figures draw. Column headers can be clicked to re-sort,
    which Streamlit handles client-side without a rerun.

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
        IDs to select, overriding whatever is stored. Used when a preset is applied.
    label_style : str
        One of ``LABEL_STYLES``, naming each datapoint.
    custom_labels : dict, optional
        ProteoBench ID to label, for the ``"custom"`` style.
    editable_labels : bool
        Whether each row offers an editable ``Label`` column.
    default_selection : str
        What is ticked before the viewer has touched anything: ``"best"`` for one datapoint per
        tool, or ``"all"`` for every datapoint. The results tabs start from ``"all"`` so nothing
        is hidden from a first-time reader; the in-depth tab starts from its own preset instead.

    Returns
    -------
    DenovoTableResult
        The selected ProteoBench IDs and any labels the viewer typed.
    """
    if result_df is None or len(result_df) == 0:
        st.info("No results available yet.", icon="ℹ️")
        return DenovoTableResult(set(), {})

    typed_labels = dict(custom_labels or {})
    ranks, best_by_tool = rank_within_tools(result_df, evaluation_type, ambiguity_combo)
    labels = build_display_labels(
        result_df,
        style=label_style,
        ranks=ranks,
        custom_labels=custom_labels_by_index(result_df, typed_labels),
    )
    classes = classify_datapoint_columns(result_df)

    # Computed over every datapoint, not over the rows the tool filter leaves: a description
    # says how a run differs from its own tool's other runs, so it must see all of them.
    variants = build_variant_descriptions(result_df)

    hidden_key = f"{state_prefix}_hidden_columns"
    if hidden_key not in st.session_state:
        st.session_state[hidden_key] = set(default_hidden_columns(classes))
    st.session_state[hidden_key], show_variants = _render_column_picker(
        hidden_key, f"{state_prefix}_show_variants", classes, set(st.session_state[hidden_key])
    )
    visible = _visible_columns(classes, set(st.session_state[hidden_key]))

    selection_key = f"{state_prefix}_selected_ids"
    if selection_key not in st.session_state:
        if default_selection == "all" and "id" in result_df.columns:
            st.session_state[selection_key] = {str(point_id) for point_id in result_df["id"]}
        else:
            st.session_state[selection_key] = {
                str(result_df.at[idx, "id"]) for idx in best_by_tool.values() if "id" in result_df.columns
            }
    if selected_ids is not None:
        st.session_state[selection_key] = {str(point_id) for point_id in selected_ids}
    selected = set(st.session_state[selection_key])

    order_key = f"{state_prefix}_row_order"
    generation_key = f"{state_prefix}_editor_generation"
    shown_tools = _render_row_controls(result_df, state_prefix, selection_key, best_by_tool)

    visible_rows = result_df
    if shown_tools:
        visible_rows = result_df[result_df["software_name"].astype(str).isin(shown_tools)]
        if visible_rows.empty:
            st.info("No datapoints for that tool.", icon="ℹ️")
            return DenovoTableResult(selected, typed_labels)

    frame = build_table_frame(
        visible_rows,
        visible,
        labels,
        ranks,
        best_by_tool,
        selected,
        evaluation_type,
        ambiguity_combo,
        editable_labels=editable_labels,
        custom_labels=typed_labels,
        variants=variants,
        show_variants=show_variants,
    )

    column_config = {
        "Show": st.column_config.CheckboxColumn("Show", help="Draw this datapoint in the figures", width="small"),
        "Tool": st.column_config.TextColumn("Tool", help="A star marks the datapoint coloured by default"),
        "Datapoint": st.column_config.TextColumn("Datapoint", width="medium"),
        "Parameters": st.column_config.TextColumn(
            "Parameters",
            help="What sets this run apart from the same tool's other submissions",
            width="medium",
        ),
        "Rank": st.column_config.NumberColumn("Rank", help="Rank within this tool, by mean AUC", width="small"),
        **{label: st.column_config.NumberColumn(label, format="%.3f") for label, _ in METRIC_COLUMNS},
    }
    if editable_labels:
        column_config["Label"] = st.column_config.TextColumn(
            "Label", help="Your own name for this run; blank falls back to tool + rank"
        )

    editable = {"Show", "Label"} if editable_labels else {"Show"}

    # Streamlit keys a data editor's pending cell edits by row position, and replays them onto
    # whatever now sits at those positions. So whenever the rows themselves change -- narrowed by
    # the tool filter, re-ordered by a different evaluation type -- the editor needs a new key,
    # or an edit made to row 3 of the old table lands on row 3 of the new one. The bulk buttons
    # bump the same counter for the same reason.
    order = list(frame["_id"])
    if st.session_state.get(order_key) != order:
        st.session_state[generation_key] = int(st.session_state.get(generation_key, 0)) + 1
    st.session_state[order_key] = order
    editor_key = f"{state_prefix}_editor_{int(st.session_state.get(generation_key, 0))}"

    edited = st.data_editor(
        frame.drop(columns=["_id"]),
        key=editor_key,
        hide_index=True,
        width="stretch",
        height=table_height(len(frame)),
        disabled=[column for column in frame.columns if column not in editable and column != "_id"],
        column_config=column_config,
        on_change=sync_selection_from_editor,
        args=(editor_key, order_key, selection_key),
    )

    _reconcile_edits(frame, edited, selected, typed_labels, editable_labels)
    st.session_state[selection_key] = selected
    return DenovoTableResult(selected, typed_labels)


def selection_summary(result_df: pd.DataFrame, selected_ids: Iterable[str]) -> str:
    """
    One line describing what is currently selected, for display above a collapsed control block.

    Parameters
    ----------
    result_df : pd.DataFrame
        The datapoints available.
    selected_ids : Iterable of str
        The selected ProteoBench IDs.

    Returns
    -------
    str
        A summary such as "8 datapoints from 8 tools", or a note that nothing is selected.
    """
    ids = {str(point_id) for point_id in selected_ids}
    if not ids or "id" not in result_df.columns:
        return "Nothing selected."
    chosen = result_df[result_df["id"].astype(str).isin(ids)]
    tools = chosen["software_name"].astype(str).nunique() if "software_name" in chosen.columns else 0
    noun = "datapoint" if len(chosen) == 1 else "datapoints"
    tool_noun = "tool" if tools == 1 else "tools"
    return f"{len(chosen)} {noun} from {tools} {tool_noun}."


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
