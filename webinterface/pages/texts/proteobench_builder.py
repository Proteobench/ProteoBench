"""Streamlit-wide page settings and tools for ProteoBench."""

import base64

import streamlit as st
import streamlit.components.v1 as components
from pages.texts.generic_texts import WebpageTexts
from pages.utils.module_registry import MODULE_CATEGORIES

_ICON_PATH = "../img/proteobench-icon.svg"


def _svg_data_uri(path: str) -> str:
    """Encode an SVG file as a base64 data URI for embedding in markdown labels."""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


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
        cols = st.columns([7, 1])

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


def proteobench_sidebar(current_page):
    """
    Format the sidebar for ProteoBench with active page highlighting, search, and release stage badges.

    Parameters
    ----------
    current_page : str
        The name of the current page (should match label).
    """
    from pages.utils.module_registry import filter_modules, get_all_modules

    texts = WebpageTexts
    all_modules = get_all_modules()

    # Add CSS to prevent sidebar text cutoff
    st.markdown(
        """
        <style>
        /* Prevent text cutoff in sidebar */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: normal !important;
        }
        
        /* Ensure sidebar links wrap properly */
        [data-testid="stSidebar"] a {
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: normal !important;
            line-height: 1.4 !important;
        }
        
        /* Allow columns in sidebar to wrap content */
        [data-testid="stSidebar"] [data-testid="column"] {
            overflow: visible !important;
        }
        
        /* Ensure expander content wraps */
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            overflow-wrap: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar layout
    with st.sidebar:
        st.page_link("Home.py", label=f"![Home]({_svg_data_uri(_ICON_PATH)}) **ProteoBench**")

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
            for category in MODULE_CATEGORIES:
                all_filtered.extend(filtered_modules[category])

            if all_filtered:
                render_links(all_filtered)
            else:
                st.markdown("*No modules match your search.*")
        else:
            # Show normal categorized expanders
            for category in MODULE_CATEGORIES:
                # Skip categories with no modules (e.g. Debug when not enabled locally)
                if not all_modules[category]:
                    continue
                with st.expander(category, expanded=(current_page in [m.label for m in all_modules[category]])):
                    render_links(filtered_modules[category])

        st.image("logos/logo_funding/main_logos_sidebar_only_eubic_eupa.png", width=220)
        st.page_link(texts.ShortMessages.privacy_notice, label="privacy notice")
        st.page_link(texts.ShortMessages.legal_notice, label="legal notice")

        if "tracking" in st.secrets and "html_js" in st.secrets["tracking"]:
            json_html = st.secrets["tracking"]["html_js"]
            json_html = json_html.replace("<HERE_THE_URL>", st.context.url)
            components.html(json_html, width=0, height=0)
