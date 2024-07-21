import logging
from typing import Type

import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.dda_quant_variables import VariablesDDAQuant

from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.modules.dda_quant_ion.module import IonModule


class StreamlitUI:
    def __init__(self):
        self.variables_dda_quant: VariablesDDAQuant = VariablesDDAQuant()
        self.ionmodule: IonModule = IonModule()
        self.parsesettingsbuilder = ParseSettingsBuilder()

        self.quant_uiobjects = QuantUIObjects(self.variables_dda_quant, self.ionmodule, self.parsesettingsbuilder)

        self._main_page()

    def _main_page(self) -> None:
        """
        Sets up the main page layout for the Streamlit application.
        This includes the title, module descriptions, input forms, and configuration settings.
        """
        self.quant_uiobjects.create_text_header()
        self.quant_uiobjects.create_main_submission_form()
        self.quant_uiobjects.init_slider()

        if self.quant_uiobjects.variables_quant.fig_logfc in st.session_state:
            self.quant_uiobjects.populate_results()

        self.quant_uiobjects.create_results()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()  # Instantiate and run the extended UI class
