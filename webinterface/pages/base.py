import logging

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.banner import display_banner
from pages.base_pages.utils.metrics_help import context_for_tab_method, render_metrics_help

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder

# The guided tour is an optional driver.js overlay. Importing it can fail when the
# installed streamlit_tour is incompatible with the streamlit version (e.g.
# streamlit_tour 1.1.0 raises at import under streamlit>=1.58). Degrade gracefully:
# disable the tour rather than breaking the whole page.
try:
    from streamlit_tour import Tour
except Exception:  # noqa: BLE001 - any import/component-registration failure
    Tour = None

# Default tabs of a module page, as (tab label, UIObjects method name) pairs.
DEFAULT_TABS = [
    ("View Public Results", "display_all_data_results_main"),
    ("Upload New Results (Private)", "display_submission_form"),
    ("View Single Result", "display_indepth_plots"),
    ("View Public + New Results", "display_all_data_results_submitted"),
    ("Compare Two Results", "display_workflow_comparison"),
    ("Submit New Results", "display_public_submission_ui"),
]


def run_page(variables) -> None:
    """Build and render a module page from its Variables instance.

    The Variables class names the backend module (``ionmodule``), the UIObjects class
    (``uiobjects``), and optionally ``tabs`` (default ``DEFAULT_TABS``) and ``tour``.

    Parameters
    ----------
    variables : VariablesBase
        Instance of the module's ``Variables*`` dataclass.
    """
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    BaseStreamlitUI(
        variables,
        variables.ionmodule,
        variables.uiobjects,
        variables.sidebar_label,
        tabs=variables.tabs or DEFAULT_TABS,
        tour=variables.tour,
    ).main_page()


class BaseStreamlitUI:
    """
    Streamlit UI shared by all module pages: tabs, tab headers and the guided tour.
    """

    def __init__(self, variables, ionmodule, uiobjects, page_name, tabs=DEFAULT_TABS, tour=True):
        """
        Initialize the module page UI.
        """
        pbb.proteobench_page_config()

        self.variables = variables
        self.tabs = tabs
        self.tour = tour

        if self.variables.submit not in st.session_state:
            st.session_state[self.variables.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule = ionmodule(token=token)
        self.parsesettingsbuilder = ParseSettingsBuilder(
            module_id=self.ionmodule.module_id, parse_settings_dir=self.variables.parse_settings_dir
        )

        self.uiobjects = uiobjects(self.variables, self.ionmodule, self.parsesettingsbuilder, page_name=page_name)

    def _render_tab_header(self, method_name: str = None) -> None:
        """Render common tab header elements: title, documentation link, metrics help, and banner.

        Parameters
        ----------
        method_name : str, optional
            Name of the UIObjects method rendering this tab. It selects which metrics explanation
            the popover shows, because the in-depth tab does not display the main plot.
        """
        st.title(self.variables.title)
        raw_data_url = getattr(self.variables, "raw_data_url", None)
        doc_col, download_col, metrics_col = st.columns(3)
        with doc_col:
            st.link_button(
                "Module documentation",
                url=self.variables.doc_url,
                type="secondary",
                icon="📖",
                help="link to the module documentation",
            )
        if raw_data_url:
            with download_col:
                st.link_button(
                    "Download input files",
                    url=raw_data_url,
                    type="secondary",
                    icon="⬇️",
                    help="Download the raw input files used to benchmark this module",
                )
        with metrics_col:
            render_metrics_help(self.ionmodule, self.variables, context=context_for_tab_method(method_name))
        display_banner(self.variables)

    def main_page(self) -> None:
        """
        Set up the main page layout for the Streamlit application.
        """
        # User navigated away from the homepage without answering: treat as opted out.
        if "_tour_opted_in" not in st.session_state:
            st.session_state["_tour_opted_in"] = False

        # Driver.js sets pointer-events:none on ALL elements (.driver-active *) to lock the page.
        # This prevents Streamlit selectbox dropdowns from working because they render as body-level
        # portals outside the highlighted element. We re-enable pointer events on everything, but
        # keep the SVG overlay itself non-interactive so overlay clicks don't close the tour.
        if st.session_state.get("_module_tour_in_progress", False):
            st.markdown(
                "<style>"
                ".driver-active * { pointer-events: auto !important; }"
                ".driver-active svg * { pointer-events: all !important; }"
                ".driver-active .driver-overlay,"
                ".driver-active .driver-overlay * { pointer-events: none !important; }"
                "</style>",
                unsafe_allow_html=True,
            )

        tab_config = self.tabs
        # Archived modules no longer accept public submissions.
        if getattr(self.variables, "archived_warning", False):
            tab_config = [t for t in tab_config if t[1] != "display_public_submission_ui"]
        tabs = st.tabs([name for name, _ in tab_config])
        for tab, (_, method_name) in zip(tabs, tab_config):
            with tab:
                self._render_tab_header(method_name=method_name)
                getattr(self.uiobjects, method_name)()

        # Skip tour setup entirely when the streamlit_tour component is unavailable.
        tour_steps = self.uiobjects.get_tour_steps() if self.tour and Tour is not None else None
        if tour_steps:
            if st.sidebar.button("Take a Tour", key="module_tour_trigger"):
                st.session_state["start_module_tour"] = True
        else:
            # No tour for this module — discard any stale trigger so it doesn't
            # fire unexpectedly when the user navigates to a module that has a tour.
            st.session_state.pop("start_module_tour", None)

        if tour_steps:
            module_id = getattr(self.ionmodule, "module_id", "module")
            tour_key = f"onboarding_{module_id}"
            tour_active_key = f"stTour--{tour_key}-active"
            tour_in_progress_key = "_module_tour_in_progress"

            # Detect tour completion: was in progress last render, now inactive.
            if st.session_state.get(tour_in_progress_key, False) and not st.session_state.get(tour_active_key, False):
                st.session_state.pop(tour_in_progress_key, None)
                st.session_state["_module_tour_completed"] = True

            tour = Tour(
                tour_steps,
                key=tour_key,
                show_progress=True,
                animate=True,
                overlay_opacity=0.75,
                one_time_tour=False,
            )
            auto_key = f"_tour_auto_{tour_key}"
            if st.session_state.pop("start_module_tour", False):
                # Manual button: always start regardless of opt-in.
                st.session_state[tour_in_progress_key] = True
                tour.start()
            elif (
                "_tour_opted_in" in st.session_state
                and auto_key not in st.session_state
                and not st.session_state.get("_module_tour_completed", False)
            ):
                # User has made a decision and auto-start has not been handled yet.
                st.session_state[auto_key] = True
                if st.session_state["_tour_opted_in"] is True:
                    st.session_state[tour_in_progress_key] = True
                    tour.start()
                # Opted out: mark handled, do not start.
