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


def render_links(pages, current_page):
    for label, path in pages.items():
        css_class = "sidebar-link-active" if label == current_page else "sidebar-link"
        st.markdown(f'<a href="{path}" target="_self" class="{css_class}">{label}</a>', unsafe_allow_html=True)


def proteobench_sidebar(current_page, proteobench_logo="logos/logo_funding/main_logos_sidebar.png"):
    """
    Format the sidebar for ProteoBench with active page highlighting and hover effect.

    Parameters
    ----------
    current_page : str
        The name of the current page (should match label).
    proteobench_logo : str, optional
        Path to the ProteoBench logo image file.
    """
    import streamlit as st
    from pages.texts.generic_texts import WebpageTexts

    texts = WebpageTexts

    # Define pages
    dda_pages = {
        "Quant LFQ DDA ion QExactive": "/Quant_LFQ_DDA_ion_QExactive",
        "Quant LFQ DDA ion Astral": "/Quant_LFQ_DDA_ion_Astral",
        "Quant LFQ DDA peptidoform": "/Quant_LFQ_DDA_peptidoform",
    }
    dia_pages = {
        "Quant LFQ DIA ion diaPASEF": "/Quant_LFQ_DIA_ion_diaPASEF",
        "Quant LFQ DIA ion Astral": "/Quant_LFQ_DIA_ion_Astral",
    }
    archived_pages = {
        "Quant LFQ DIA ion AIF": "/Quant_LFQ_DIA_ion_AIF",
    }

    # Add custom CSS for links and hover
    st.markdown(
        """
    <style>
    .sidebar-link, .sidebar-link:link, .sidebar-link:visited, .sidebar-link:hover, .sidebar-link:active {
        display: block;
        padding: 0.3em 0;
        color: black !important;
        text-decoration: none;
        font-size: 0.95rem;
        transition: all 0.2s ease-in-out;
    }
    .sidebar-link:hover {
        font-weight: 600;
    }
    .sidebar-link-active, .sidebar-link-active:visited {
        font-weight: 700;
        color: black !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar layout
    with st.sidebar:
        home_class = "sidebar-link-active" if current_page == "Home" else "sidebar-link"
        st.markdown(f'<a href="/" class="{home_class}">Home</a>', unsafe_allow_html=True)

        with st.expander("DDA", expanded=(current_page in dda_pages)):
            render_links(dda_pages, current_page=current_page)

        with st.expander("DIA", expanded=(current_page in dia_pages)):
            render_links(dia_pages, current_page=current_page)

        with st.expander("Archived", expanded=(current_page in archived_pages)):
            render_links(archived_pages, current_page=current_page)

        st.image(proteobench_logo, width=300)
        st.page_link(texts.ShortMessages.privacy_notice, label="privacy notice")
        st.page_link(texts.ShortMessages.legal_notice, label="legal notice")

        try:
            if "tracking" in st.secrets and "html" in st.secrets["tracking"]:
                st.html(st.secrets["tracking"]["html"])
        except FileNotFoundError:
            pass
