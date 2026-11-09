"""
The selection the table owns: which datapoints are ticked, and the session state holding it.
"""

from typing import Iterable, Set

import pandas as pd
import streamlit as st


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


def _reconcile_edits(frame: pd.DataFrame, edited: pd.DataFrame, selected: Set[str]) -> None:
    """
    Fold the editor's returned frame back into the selection, in place.

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
    """
    for position, point_id in enumerate(frame["_id"]):
        if bool(edited.iloc[position]["Show"]):
            selected.add(point_id)
        else:
            selected.discard(point_id)


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
