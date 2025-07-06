"""Streamlit-wide page settings and tools for ProteoBench."""

import streamlit as st
from pages.texts.generic_texts import WebpageTexts


def proteobench_page_config(page_layout="wide"):
    """
    Set some ProteoBench wide page settings.

    Parameters
    ----------
    page_layout : str, optional
        Layout of the page (default: "wide").

    Returns
    -------
    None
    """
    try:
        st.set_page_config(
            page_title="Proteobench",
            page_icon=":balloon:",
            layout=page_layout,
            initial_sidebar_state="expanded",
        )
    except:
        return "Set already"


def proteobench_sidebar(proteobench_logo="logos/logo_funding/main_logos_sidebar.png"):
    """
    Format the sidebar for ProteoBench.

    Parameters
    ----------
    proteobench_logo : str, optional
        Path to the ProteoBench logo image file (default: "logos/logo_funding/main_logos_sidebar.png").
    """
    texts = WebpageTexts

    import streamlit as st

    # Sidebar title
    # st.sidebar.markdown("## Navigation")
    # Quant_LFQ_DDA_ion_QExactive
    # Quant_LFQ_DDA_peptidoform
    # Quant_LFQ_DDA_ion_Astral
    # Quant_LFQ_DIA_ion_AIF
    # Quant_LFQ_DIA_ion_diaPASEF
    # Quant_LFQ_DIA_ion_Astral
    # DIA section in the sidebar
    with st.sidebar:
        st.link_button("Home", "/")

    # DDA section in the sidebar
    with st.sidebar:
        with st.expander("DDA", expanded=False):
            st.link_button("Quant LFQ DDA ion QExactive", "/Quant_LFQ_DDA_ion_QExactive")
            st.link_button("Quant LFQ DDA peptidoform", "/Quant_LFQ_DDA_peptidoform")
            st.link_button("Quant LFQ DDA ion Astral", "/Quant_LFQ_DDA_ion_Astral")

    with st.sidebar:
        with st.expander("DIA", expanded=False):
            st.link_button("Quant LFQ DIA ion diaPASEF", "/Quant_LFQ_DIA_ion_diaPASEF")
            st.link_button("Quant LFQ DIA ion Astral", "/Quant_LFQ_DIA_ion_Astral")

    with st.sidebar:
        with st.expander("Archived", expanded=False):
            st.link_button("Quant LFQ DIA ion AIF", "/Quant_LFQ_DIA_ion_AIF")

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
