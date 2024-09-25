import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.dda_quant_variables import VariablesDDAQuant
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.modules.dda_quant_ion.dda_quant_ion_module import DDAQuantIonModule


class StreamlitUI:
    def __init__(self):
        self.variables_dda_quant: VariablesDDAQuant = VariablesDDAQuant()
        self.texts: Type[WebpageTexts] = WebpageTexts
        self.texts.ShortMessages.title = "DDA Ion quantification"
        self.user_input: Dict[str, Any] = dict()

        pbb.proteobench_page_config()

        if self.variables_dda_quant.submit not in st.session_state:
            st.session_state[self.variables_dda_quant.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule: DDAQuantIonModule = DDAQuantIonModule(token=token)
        self.parsesettingsbuilder = ParseSettingsBuilder()

        self.quant_uiobjects = QuantUIObjects(self.variables_dda_quant, self.ionmodule, self.parsesettingsbuilder)

        self._main_page()

    def _main_page(self) -> None:
        """
        Sets up the main page layout for the Streamlit application.
        """
        # Create tabs
        tab_results_all, tab_submission_details, tab_results_new, tab_public_submission = st.tabs(
            ["Results (All Data)", "Submission Details", "Results (New Submissions)", "Public Submission"]
        )

        # Tab 1: Results (All Data)
        with tab_results_all:
            self.quant_uiobjects.display_results_all_data()

        # Tab 2: Submission Details
        with tab_submission_details:
            self.quant_uiobjects.display_submission_details()

        # Tab 3: Results (New Submissions)
        with tab_results_new:
            self.quant_uiobjects.display_results_new_submissions()

        # Tab 4: Public Submission
        with tab_public_submission:
            self.quant_uiobjects.display_public_submission_form()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()  # Instantiate and run the extended UI class
