"""Helpers for inspecting Streamlit ``st.session_state`` on the debug page.

Provides two small UI builders used by ``pages/0_debug_session_state.py``:

- :func:`ui_overview_table` renders a table of every key currently in
  ``st.session_state`` with its type and an abbreviated value preview.
- :func:`ui_key_inspector` renders a selectbox to pick a single key and shows
  its full value.

Both are deliberately defensive: a value that cannot be rendered must not crash
the whole page, so failures are caught and shown inline.
"""

from __future__ import annotations

import pprint
from typing import Any

import pandas as pd
import streamlit as st

from pages.base_pages.utils.general import prepare_df_for_display

_MAX_SCALAR_REPR = 200  # max chars for an inline scalar repr before truncation
_MAX_FULL_REPR = 20000  # max chars for the full-value view in the inspector


def _type_name(value: Any) -> str:
    """Return the short class name of a value.

    Parameters
    ----------
    value : Any
        The value to describe.

    Returns
    -------
    str
        The value's type name (e.g. ``"DataFrame"``, ``"list"``).
    """
    return type(value).__name__


def _abbreviate(value: Any, max_list_repr: int = 5) -> str:
    """Return a short, human-readable preview of a session-state value.

    Lists/tuples/sets are capped at ``max_list_repr`` items and DataFrames and
    Series are summarized by shape/length rather than dumped in full.

    Parameters
    ----------
    value : Any
        The value to summarize.
    max_list_repr : int, optional
        Maximum number of items shown inline for sequences and dict keys,
        by default 5.

    Returns
    -------
    str
        A compact preview string.
    """
    try:
        if isinstance(value, pd.DataFrame):
            cols = list(map(str, value.columns[:max_list_repr]))
            more = f", +{value.shape[1] - max_list_repr} more" if value.shape[1] > max_list_repr else ""
            return f"DataFrame(shape={value.shape}, columns=[{', '.join(cols)}{more}])"
        if isinstance(value, pd.Series):
            return f"Series(len={len(value)}, dtype={value.dtype})"
        if isinstance(value, (list, tuple, set)):
            seq = list(value)
            shown = ", ".join(repr(x) for x in seq[:max_list_repr])
            more = f", +{len(seq) - max_list_repr} more" if len(seq) > max_list_repr else ""
            open_b, close_b = {list: ("[", "]"), tuple: ("(", ")"), set: ("{", "}")}[type(value)]
            return f"{type(value).__name__}{open_b}{shown}{more}{close_b}"
        if isinstance(value, dict):
            keys = list(value.keys())
            shown = ", ".join(repr(k) for k in keys[:max_list_repr])
            more = f", +{len(keys) - max_list_repr} more" if len(keys) > max_list_repr else ""
            return f"dict(len={len(keys)}, keys={{{shown}{more}}})"
        text = repr(value)
        return text if len(text) <= _MAX_SCALAR_REPR else text[:_MAX_SCALAR_REPR] + " …"
    except Exception as exc:  # never let preview rendering break the table
        return f"<unrepresentable: {exc}>"


def ui_overview_table(max_list_repr: int = 5) -> None:
    """Render an overview table of all current ``st.session_state`` keys.

    Each row shows the key, the value's type, and an abbreviated preview.

    Parameters
    ----------
    max_list_repr : int, optional
        Maximum number of items shown inline for sequences and dict keys,
        by default 5.
    """
    state = st.session_state
    keys = list(state.keys())

    st.subheader("Overview")
    st.caption(f"{len(keys)} key(s) in st.session_state")

    if not keys:
        st.info("Session state is empty.")
        return

    rows = []
    for key in keys:
        try:
            value = state[key]
            rows.append({"key": str(key), "type": _type_name(value), "preview": _abbreviate(value, max_list_repr)})
        except Exception as exc:  # robust to keys that raise on access
            rows.append({"key": str(key), "type": "?", "preview": f"<error: {exc}>"})

    overview = pd.DataFrame(rows, columns=["key", "type", "preview"]).sort_values("key").reset_index(drop=True)
    st.dataframe(prepare_df_for_display(overview), hide_index=True)


def ui_key_inspector(max_list_repr: int = 5) -> None:
    """Render a per-key inspector for ``st.session_state``.

    A selectbox chooses one key; its full value is shown using a widget
    appropriate to the value's type (DataFrame/Series as tables, collections
    as pretty-printed text, scalars as code).

    Parameters
    ----------
    max_list_repr : int, optional
        Maximum number of items shown in the selectbox help preview,
        by default 5.
    """
    state = st.session_state
    keys = list(state.keys())

    st.subheader("Inspect a key")

    if not keys:
        st.info("Session state is empty.")
        return

    # Map the displayed (string) label back to the real key, which may be a UUID
    # object or other non-string used as a widget key.
    label_to_key = {str(k): k for k in keys}
    selected_label = st.selectbox("Select a session-state key", sorted(label_to_key.keys()))
    if selected_label is None:
        return

    actual_key = label_to_key[selected_label]
    try:
        value = state[actual_key]
    except Exception as exc:
        st.error(f"Could not read key {selected_label!r}: {exc}")
        return

    st.markdown(f"**Type:** `{_type_name(value)}` — **preview:** `{_abbreviate(value, max_list_repr)}`")

    if isinstance(value, pd.DataFrame):
        st.caption(f"shape={value.shape}")
        st.dataframe(prepare_df_for_display(value))
    elif isinstance(value, pd.Series):
        st.caption(f"len={len(value)}, dtype={value.dtype}")
        st.dataframe(prepare_df_for_display(value.to_frame(name=str(actual_key))))
    elif isinstance(value, (dict, list, tuple, set)):
        text = pprint.pformat(value, width=100)
        st.code(text if len(text) <= _MAX_FULL_REPR else text[:_MAX_FULL_REPR] + "\n… (truncated)", language="python")
    else:
        text = repr(value)
        st.code(text if len(text) <= _MAX_FULL_REPR else text[:_MAX_FULL_REPR] + " …", language="python")
