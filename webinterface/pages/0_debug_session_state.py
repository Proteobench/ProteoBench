"""Debug session state page for development purposes."""

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.utils.session_state import ui_key_inspector, ui_overview_table

st.title("Session State Debug")

pbb.proteobench_sidebar(current_page="/")

MAX_LIST_REPR = 5  # max items shown inline for lists

# UI
# ── Overview table ─────────────────────────────────────────────────────────────
ui_overview_table(max_list_repr=MAX_LIST_REPR)


# ── Per-key inspector ──────────────────────────────────────────────────────────
ui_key_inspector(max_list_repr=MAX_LIST_REPR)
# endregion
