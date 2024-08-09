"""Streamlit-wide page settings and tools for ProteoBench."""

import streamlit as st
from pages.texts.generic_texts import WebpageTexts


def proteobench_page_config(page_layout="wide"):
    """Set some ProteoBench wide page settings"""
    try:
        st.set_page_config(
            page_title="Proteobench",
            page_icon=":rocket:",
            layout=page_layout,
            initial_sidebar_state="expanded",
        )
    except:
        return "Set already"


def proteobench_sidebar(proteobench_logo="logos/logo_funding/main_logos_sidebar.png"):
    """Format the sidebar for ProteoBench."""
    texts = WebpageTexts

    st.sidebar.image(proteobench_logo, width=300)

    st.sidebar.page_link(texts.ShortMessages.privacy_notice, label="privacy notice")
    st.sidebar.page_link(texts.ShortMessages.legal_notice, label="legal notice")

    try:
        if "tracking" in st.secrets.keys() and "html" in st.secrets["tracking"].keys():
            st.sidebar.html(st.secrets["tracking"]["html"])
    except FileNotFoundError:
        # We catch the error here if the secrets.toml file is not present
        # This is likely the case when the user is running the app locally
        # Solution would be a default config file that is loaded if the secrets.toml is
        # not present
        pass
