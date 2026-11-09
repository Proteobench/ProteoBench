"""
The table itself: the editor, and the selection it hands back.
"""

from typing import Iterable, Optional, Set

import pandas as pd
import streamlit as st

from proteobench.plotting.plot_generator_denovo import (
    build_display_labels,
    build_variant_descriptions,
    classify_datapoint_columns,
    default_hidden_columns,
    rank_within_tools,
)

from pages.base_pages.utils.denovo_resulttable.controls import (
    _render_column_picker,
    _render_row_controls,
    table_height,
)
from pages.base_pages.utils.denovo_resulttable.frame import (
    METRIC_COLUMNS,
    _visible_columns,
    build_table_frame,
)
from pages.base_pages.utils.denovo_resulttable.selection import (
    _reconcile_edits,
    sync_selection_from_editor,
)


def render_denovo_result_table(
    result_df: pd.DataFrame,
    state_prefix: str,
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
    selected_ids: Optional[Iterable[str]] = None,
    default_selection: str = "best",
) -> Set[str]:
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
    default_selection : str
        What is ticked before the viewer has touched anything: ``"best"`` for one datapoint per
        tool, or ``"all"`` for every datapoint. The results tabs start from ``"all"`` so nothing
        is hidden from a first-time reader; the in-depth tab starts from its own preset instead.

    Returns
    -------
    set of str
        The ProteoBench IDs the viewer has ticked.
    """
    if result_df is None or len(result_df) == 0:
        st.info("No results available yet.", icon="ℹ️")
        return set()

    ranks, best_by_tool = rank_within_tools(result_df, evaluation_type, ambiguity_combo)
    labels = build_display_labels(result_df, ranks=ranks)
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
            return selected

    frame = build_table_frame(
        visible_rows,
        visible,
        labels,
        ranks,
        best_by_tool,
        selected,
        evaluation_type,
        ambiguity_combo,
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
        disabled=[column for column in frame.columns if column not in ("Show", "_id")],
        column_config=column_config,
        on_change=sync_selection_from_editor,
        args=(editor_key, order_key, selection_key),
    )

    _reconcile_edits(frame, edited, selected)
    st.session_state[selection_key] = selected
    return selected
