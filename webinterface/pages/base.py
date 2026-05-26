import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.banner import display_banner
from streamlit_tour import Tour


class BaseStreamlitUI:
    """
    Streamlit UI for the DDA quantification - precursor ions module.
    """

    def __init__(self, variables, texts, ionmodule, parsesettingsbuilder, uiobjects, page_name):
        """
        Initialize the Streamlit UI for the DDA quantification - precursor ions module.
        """
        self.variables = variables
        self.texts = texts

        self.user_input = dict()

        pbb.proteobench_page_config()

        if self.variables.submit not in st.session_state:
            st.session_state[self.variables.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule = ionmodule(token=token)
        self.parsesettingsbuilder = parsesettingsbuilder(
            module_id=self.ionmodule.module_id, parse_settings_dir=self.variables.parse_settings_dir
        )

        self.uiobjects = uiobjects(self.variables, self.ionmodule, self.parsesettingsbuilder, page_name=page_name)

    def _render_tab_header(self) -> None:
        """Render common tab header elements: title, documentation link, and banner."""
        st.title(self.variables.title)
        st.link_button(
            "Go to module documentation",
            url=self.variables.doc_url,
            type="secondary",
            help="link to the module documentation",
        )
        display_banner(self.variables)

    def get_tab_config(self) -> list:
        """Return tab configuration as list of (tab_name, method_name) tuples.

        Override this method in subclasses to customize tabs.
        """
        return [
            ("View Public Results", "display_all_data_results_main"),
            ("Upload New Results (Private)", "display_submission_form"),
            ("View Single Result", "display_indepth_plots"),
            ("View Public + New Results", "display_all_data_results_submitted"),
            ("Compare Two Results", "display_workflow_comparison"),
            ("Submit New Results", "display_public_submission_ui"),
        ]

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
                ".driver-active .driver-overlay { pointer-events: none !important; }"
                "</style>",
                unsafe_allow_html=True,
            )

        if st.sidebar.button("Take a Tour", key="module_tour_trigger"):
            st.session_state["start_module_tour"] = True

        # Get tab configuration
        tab_config = self.get_tab_config()
        tab_names = [name for name, _ in tab_config]

        # Create tabs dynamically
        tabs = st.tabs(tab_names)

        # Render each tab
        for tab, (tab_name, method_name) in zip(tabs, tab_config):
            with tab:
                self._render_tab_header()
                # Call the appropriate method on uiobjects
                getattr(self.uiobjects, method_name)()

        tour_steps = self.uiobjects.get_tour_steps()
        if tour_steps:
            module_id = getattr(self.ionmodule, "module_id", "module")
            tour_key = f"onboarding_{module_id}"
            tour_active_key = f"stTour--{tour_key}-active"
            tour_in_progress_key = "_module_tour_in_progress"

            # Detect tour completion: was in progress last render, now inactive.
            if st.session_state.get(tour_in_progress_key, False) and not st.session_state.get(
                tour_active_key, False
            ):
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
