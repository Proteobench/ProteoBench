import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.banner import display_banner


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
