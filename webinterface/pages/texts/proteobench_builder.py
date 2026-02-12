"""Streamlit-wide page settings and tools for ProteoBench."""

import streamlit as st
import streamlit.components.v1 as components
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
    except Exception:
        return "Set already"


def render_links(modules):
    """
    Render sidebar links for modules with release stage badges using native Streamlit.

    Parameters
    ----------
    modules : List[ModuleMetadata]
        List of module metadata objects to render.
    """
    for module in modules:
        # Use wider column ratio to prevent text cutoff
        cols = st.columns([5, 1])

        with cols[0]:
            st.page_link(module.file_path, label=module.label)

        with cols[1]:
            # Add styled badge based on release stage
            if module.release_stage == "alpha":
                st.markdown(
                    '<span style="background-color: #FF8C00; color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.6rem; font-weight: 600; white-space: nowrap; display: inline-block;">ALPHA</span>',
                    unsafe_allow_html=True,
                )
            elif module.release_stage == "beta":
                st.markdown(
                    '<span style="background-color: #4169E1; color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.6rem; font-weight: 600; white-space: nowrap; display: inline-block;">BETA</span>',
                    unsafe_allow_html=True,
                )
            elif module.release_stage == "archived":
                st.markdown(
                    '<span style="background-color: #808080; color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.6rem; font-weight: 600; white-space: nowrap; display: inline-block;">ARCH</span>',
                    unsafe_allow_html=True,
                )


def proteobench_sidebar(current_page, proteobench_logo="logos/logo_funding/main_logos_sidebar.png"):
    """
    Format the sidebar for ProteoBench with active page highlighting, search, and release stage badges.

    Parameters
    ----------
    current_page : str
        The name of the current page (should match label).
    proteobench_logo : str, optional
        Path to the ProteoBench logo image file.
    """
    from pages.utils.module_registry import filter_modules, get_all_modules

    texts = WebpageTexts
    all_modules = get_all_modules()

    # Sidebar layout
    with st.sidebar:
        st.page_link("Home.py", label="Home")

        # Search box
        search_query = st.text_input(
            "🔍 Search modules",
            key="sidebar_search_input",
            placeholder="Type to filter modules...",
        )

        # Filter modules based on search
        filtered_modules = filter_modules(all_modules, search_query)

        # If search is active, show flat filtered list
        if search_query:
            st.markdown("### Search Results")
            all_filtered = []
            for category in ["DDA", "DIA", "Archived"]:
                all_filtered.extend(filtered_modules[category])

            if all_filtered:
                render_links(all_filtered)
            else:
                st.markdown("*No modules match your search.*")
        else:
            # Show normal categorized expanders
            with st.expander("DDA", expanded=(current_page in [m.label for m in all_modules["DDA"]])):
                render_links(filtered_modules["DDA"])

            with st.expander("DIA", expanded=(current_page in [m.label for m in all_modules["DIA"]])):
                render_links(filtered_modules["DIA"])

            with st.expander("Archived", expanded=(current_page in [m.label for m in all_modules["Archived"]])):
                render_links(filtered_modules["Archived"])

        st.image(proteobench_logo, width=300)
        st.page_link(texts.ShortMessages.privacy_notice, label="privacy notice")
        st.page_link(texts.ShortMessages.legal_notice, label="legal notice")

        if "tracking" in st.secrets and "html_js" in st.secrets["tracking"]:
            json_html = st.secrets["tracking"]["html_js"]
            json_html = json_html.replace("<HERE_THE_URL>", st.context.url)
            components.html(json_html, width=0, height=0)
