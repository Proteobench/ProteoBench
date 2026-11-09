"""
The controls above the table: the column picker, the tool filter and the bulk tick buttons.
"""

from typing import Dict, List, Set

import pandas as pd
import streamlit as st

from proteobench.plotting.plot_generator_denovo import ordered_datapoint_columns

from pages.base_pages.utils.denovo_resulttable.frame import header_for


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
