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


def render_links(modules, current_page):
    """
    Render sidebar links for modules with release stage badges.

    Parameters
    ----------
    modules : List[ModuleMetadata]
        List of module metadata objects to render.
    current_page : str
        The name of the current page to highlight.
    """
    from pages.utils.module_registry import ModuleMetadata

    for module in modules:
        css_class = "sidebar-link-active" if module.label == current_page else "sidebar-link"

        # Determine badge HTML based on release stage
        badge_html = ""
        if module.release_stage == "alpha":
            badge_html = ' <span style="background-color: #FF8C00; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7rem; font-weight: 600;">ALPHA</span>'
        elif module.release_stage == "beta":
            badge_html = ' <span style="background-color: #4169E1; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7rem; font-weight: 600;">BETA</span>'
        elif module.release_stage == "archived":
            badge_html = ' <span style="background-color: #808080; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7rem; font-weight: 600;">ARCHIVED</span>'
        # No badge for "live" release stage

        st.markdown(
            f'<a href="{module.path}" target="_self" class="{css_class}">{module.label}{badge_html}</a>',
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

    # Add custom CSS for links, hover, and badges
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

        # Search box
        search_query = st.text_input(
            "🔍 Search modules",
            key="sidebar_search_input",
            placeholder="Type to filter modules...",
        )

        # Filter modules based on search
        if all_modules is not None:
            filtered_modules = filter_modules(all_modules, search_query)

            # If search is active, show flat filtered list
            if search_query:
                st.markdown("### Search Results")
                all_filtered = []
                for category in ["DDA", "DIA", "Archived"]:
                    all_filtered.extend(filtered_modules[category])

                if all_filtered:
                    render_links(all_filtered, current_page=current_page)
                else:
                    st.markdown("*No modules match your search.*")
            else:
                # Show normal categorized expanders
                with st.expander("DDA", expanded=(current_page in [m.label for m in all_modules["DDA"]])):
                    render_links(filtered_modules["DDA"], current_page=current_page)

                with st.expander("DIA", expanded=(current_page in [m.label for m in all_modules["DIA"]])):
                    render_links(filtered_modules["DIA"], current_page=current_page)

                with st.expander("Archived", expanded=(current_page in [m.label for m in all_modules["Archived"]])):
                    render_links(filtered_modules["Archived"], current_page=current_page)
        else:
            dda_pages = None
            dia_pages = None
            archived_pages = None

            # Fallback rendering with old hardcoded dictionaries
            def render_links_fallback(pages, current_page):
                for label, path in pages.items():
                    css_class = "sidebar-link-active" if label == current_page else "sidebar-link"
                    st.markdown(
                        f'<a href="{path}" target="_self" class="{css_class}">{label}</a>', unsafe_allow_html=True
                    )

            with st.expander("DDA", expanded=(current_page in dda_pages)):
                render_links_fallback(dda_pages, current_page=current_page)

            with st.expander("DIA", expanded=(current_page in dia_pages)):
                render_links_fallback(dia_pages, current_page=current_page)

            with st.expander("Archived", expanded=(current_page in archived_pages)):
                render_links_fallback(archived_pages, current_page=current_page)

        st.image(proteobench_logo, width=300)
        st.page_link(texts.ShortMessages.privacy_notice, label="privacy notice")
        st.page_link(texts.ShortMessages.legal_notice, label="legal notice")

        if "tracking" in st.secrets and "html_js" in st.secrets["tracking"]:
            json_html = st.secrets["tracking"]["html_js"]
            json_html = json_html.replace("<HERE_THE_URL>", st.context.url)
            components.html(json_html, width=0, height=0)
