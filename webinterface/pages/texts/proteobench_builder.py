"""Streamlit-wide page settings and tools for ProteoBench."""

import streamlit as st
import streamlit.components.v1 as components
from pages.texts.generic_texts import WebpageTexts
from pages.utils.module_registry import MODULE_CATEGORIES
from UI_utils import svg_data_uri

_ICON_PATH = "../img/proteobench-icon.svg"


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
        pass


# Release-stage badges as Streamlit color-badge Markdown directives. Appended to the
# page-link label so the badge is part of the link text: it wraps and aligns with the
# label naturally, with no separate column or custom CSS needed.
RELEASE_STAGE_BADGES = {
    "alpha": ":orange-badge[ALPHA]",
    "beta": ":blue-badge[BETA]",
    "archived": ":gray-badge[ARCH]",
}


def render_links(modules):
    """
    Render sidebar links for modules with release stage badges using native Streamlit.

    The release-stage badge is embedded in the page-link label as a color-badge
    Markdown directive, so it flows with the link text and wraps together with it
    when the sidebar is narrowed.

    Parameters
    ----------
    modules : List[ModuleMetadata]
        List of module metadata objects to render.
    """
    for module in modules:
        badge = RELEASE_STAGE_BADGES.get(module.release_stage)
        label = f"{badge} {module.label}" if badge else module.label
        st.page_link(module.file_path, label=label)


def proteobench_sidebar(current_page):
    """
    Format the sidebar for ProteoBench with active page highlighting, search, and release stage badges.

    Parameters
    ----------
    current_page : str
        The name of the current page (should match label).
    """
    from pages.base_pages.utils.auth import render_auth_status
    from pages.utils.module_registry import filter_modules, get_all_modules

    # Show signed-in user indicator on module pages (not Home — Home has its own)
    if current_page != "/":
        render_auth_status()

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

        /* Give release-stage badges a fixed width so the title always starts at the same
           offset, keeping the badge-to-title spacing equal regardless of the badge text
           (e.g. "BETA" vs the longer "ALPHA"). Adjust min-width if a badge label changes length. */
        [data-testid="stSidebar"] .stMarkdownBadge {
            min-width: 3.4rem;
            justify-content: center;
            text-align: center;
            box-sizing: border-box;
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
        st.page_link("Home.py", label=f"![Home]({svg_data_uri(_ICON_PATH)}) **ProteoBench**")

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
