"""Streamlit-wide page settings and tools for ProteoBench."""
import streamlit as st

def proteobench_page_config(page_layout = "wide"):
    """Set some ProteoBench wide page settings"""
    st.set_page_config(
        page_title="Proteobench",
        page_icon=":rocket:",
        layout=page_layout,
        initial_sidebar_state="expanded",
    )

def proteobench_sidebar():
    """Format the sidebar for ProteoBench."""
    st.sidebar.image("logos/logo_funding/main_logos_sidebar.png", width=300)

    # add gdpr links if provided
    if "gdpr_links" in st.secrets.keys():
        st.sidebar.page_link(st.secrets["gdpr_links"]["privacy_notice_link"], label="-> privacy notice")
        st.sidebar.page_link(st.secrets["gdpr_links"]["legal_notice_link"], label="-> legal notice")
    
    if "tracking" in st.secrets.keys() and "html" in st.secrets["tracking"].keys():
        st.sidebar.html(st.secrets["tracking"]["html"])
