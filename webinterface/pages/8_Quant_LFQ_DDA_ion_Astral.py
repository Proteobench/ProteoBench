"""
Streamlit UI for the DDA quantification - precursor ions Astral module.
"""

PAGE_NAME = "2_Quant_LFQ_DDA_ion_QExactive"

import logging
import uuid
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import pandas as pd
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DDA_ion_Astral_variables import (
    VariablesDDAQuantAstral,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_Astral import DDAQuantIonAstralModule


class StreamlitUI:
    """
    Streamlit UI for the DDA quantification - precursor ions module.
    """

    def __init__(self):
        """
        Initialize the Streamlit UI for the DDA quantification - precursor ions Astral module.
        """
        self.variables_dda_quant: VariablesDDAQuantAstral = VariablesDDAQuantAstral()
        self.texts: Type[WebpageTexts] = WebpageTexts

        self.user_input: Dict[str, Any] = dict()

        pbb.proteobench_page_config()

        if self.variables_dda_quant.submit not in st.session_state:
            st.session_state[self.variables_dda_quant.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule: DDAQuantIonAstralModule = DDAQuantIonAstralModule(token=token)
        self.parsesettingsbuilder = ParseSettingsBuilder(
            module_id=self.ionmodule.module_id, parse_settings_dir=self.variables_dda_quant.parse_settings_dir
        )

        self.quant_uiobjects = QuantUIObjects(
            self.variables_dda_quant, self.ionmodule, self.parsesettingsbuilder, page_name="Quant LFQ DDA ion Astral"
        )

        self._main_page()

    def _main_page(self) -> None:
        """
        Set up the main page layout for the Streamlit application.
        """
        # Create tabs
        (
            tab_results_all,
            tab_submission_details,
            tab_indepth_plots,
            tab_results_new,
            tab_public_submission,
        ) = st.tabs(
            [
                "Public Benchmark Runs",
                "Submit New Data",
                "Results In-Depth",
                "Results New Data",
                "Public Submission",
            ]
        )

        with tab_results_all:
            st.title(self.variables_dda_quant.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables_dda_quant.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_all_data_results_main()

        # Tab 2: Submission Details
        with tab_submission_details:
            st.title(self.variables_dda_quant.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables_dda_quant.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_submission_form()

        # Tab 2.5: in-depth plots current data
        with tab_indepth_plots:
            st.title(self.variables_dda_quant.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables_dda_quant.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_indepth_plots()

        # Tab 3: Results (New Submissions)
        with tab_results_new:
            st.title(self.variables_dda_quant.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables_dda_quant.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )

            self.quant_uiobjects.display_all_data_results_submitted()

        # Tab 4: Public Submission
        with tab_public_submission:
            st.title(self.variables_dda_quant.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables_dda_quant.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_public_submission_ui()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()  # Instantiate and run the extended UI class
