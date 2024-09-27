import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.dia_quant_variables import VariablesDIAQuant
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.modules.dia_quant_ion.dia_quant_ion_module import DIAQuantIonModule


class StreamlitUI:
    def __init__(self):
        self.variables_dia_quant: VariablesDIAQuant = VariablesDIAQuant()
        self.texts: Type[WebpageTexts] = WebpageTexts
        self.texts.ShortMessages.title = "DIA Ion quantification"
        self.user_input: Dict[str, Any] = dict()

        pbb.proteobench_page_config()

        if self.variables_dia_quant.submit not in st.session_state:
            st.session_state[self.variables_dia_quant.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule: DIAQuantIonModule = DIAQuantIonModule(token=token)
        self.parsesettingsbuilder = ParseSettingsBuilder(acquisition_method="dia")

        self.quant_uiobjects = QuantUIObjects(self.variables_dia_quant, self.ionmodule, self.parsesettingsbuilder)

        self._main_page()

    def _main_page(self) -> None:
        """
        Sets up the main page layout for the Streamlit application.
        """
        # Create tabs
        (
            tab_description,
            tab_results_all,
            tab_submission_details,
            tab_indepth_plots,
            tab_results_new,
            tab_public_submission,
        ) = st.tabs(
            [
                "Module description",
                "Results (All Data)",
                "Submission form",
                "In-depth submission",
                "Results (New Submissions)",
                "Public Submission",
            ]
        )

        # Tab 0: Description
        with tab_description:
            self.quant_uiobjects.create_text_header()

        # Tab 1: Results (All Data)
        with tab_results_all:
            st.title(self.variables_dia_quant.texts.ShortMessages.title)
            if self.variables_dia_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_results_all_data()

        # Tab 2: Submission Details
        with tab_submission_details:
            self.quant_uiobjects.create_text_header()
            self.quant_uiobjects.create_main_submission_form()
            # self.quant_uiobjects.display_submission_details()

        # Tab 2.5: in-depth plots current data
        with tab_indepth_plots:
            st.title(self.variables_dia_quant.texts.ShortMessages.title)
            if self.variables_dia_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.plots_for_current_data(True)

        # Tab 3: Results (New Submissions)
        with tab_results_new:
            st.title(self.variables_dia_quant.texts.ShortMessages.title)
            if self.variables_dia_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_results_all_data_submitted()
            # self.quant_uiobjects.display_results_new_submissions()

        # Tab 4: Public Submission
        with tab_public_submission:
            st.title(self.variables_dia_quant.texts.ShortMessages.title)
            if self.variables_dia_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.wrap_public_submission_form()
            # self.quant_uiobjects.create_main_submission_form()
            # self.quant_uiobjects.display_public_submission_form()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()  # Instantiate and run the extended UI class
