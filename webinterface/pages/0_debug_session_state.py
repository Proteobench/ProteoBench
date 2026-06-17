"""Debug session state page for development purposes."""

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.utils.session_state import ui_key_inspector, ui_overview_table
from pages.utils.module_registry import is_debug_enabled

st.title("Session State Debug")

pbb.proteobench_sidebar(current_page="/")

# Local-only: hidden from the sidebar on the server, but also block direct URL access.
if not is_debug_enabled():
    st.error(
        "The session-state debug page is only available on a local run. "
        "Set the environment variable `PROTEOBENCH_DEBUG=1` before launching Streamlit to enable it."
    )
    st.stop()

MAX_LIST_REPR = 5  # max items shown inline for lists

# UI
# ── Overview table ─────────────────────────────────────────────────────────────
ui_overview_table(max_list_repr=MAX_LIST_REPR)


# ── Per-key inspector ──────────────────────────────────────────────────────────
ui_key_inspector(max_list_repr=MAX_LIST_REPR)
# endregion
