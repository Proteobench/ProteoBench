"""
Streamlit UI for the DIA quantification - precursor ions module - Plasma.
"""

import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DIA_ion_Plasma_variables import (
    VariablesDIAQuantPlasma,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DIA_Plasma import DIAQuantIonModulePlasma


class StreamlitUI:
    """
    Streamlit UI for the DIA quantification - precursor ions module - Plasma.
    """

    def __init__(self):
        """
        Initialize the Streamlit UI for the DIA quantification - precursor ions module - Plasma.
        """
        self.variables_dia_quant: VariablesDIAQuantPlasma = VariablesDIAQuantPlasma()
        self.texts: Type[WebpageTexts] = WebpageTexts
        self.user_input: Dict[str, Any] = dict()

        pbb.proteobench_page_config()

        if self.variables_dia_quant.submit not in st.session_state:
            st.session_state[self.variables_dia_quant.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule: DIAQuantIonModulePlasma = DIAQuantIonModulePlasma(token=token)
        self.parsesettingsbuilder = ParseSettingsBuilder(
            module_id=self.ionmodule.module_id, parse_settings_dir=self.variables_dia_quant.parse_settings_dir
        )

        self.quant_uiobjects = QuantUIObjects(
            self.variables_dia_quant,
            self.ionmodule,
            self.parsesettingsbuilder,
            page_name="Quant LFQ DIA ion Plasma",
        )

        self._main_page()

    def _render_header(self, key_suffix: str = "") -> None:
        """Render the shared title, documentation link, download link, and beta warning.

        ``key_suffix`` (e.g. the tab name) must be unique per call, since this is
        called once per tab within the same script run and the sign-in widget
        it embeds uses explicit widget keys.
        """
        from pages.base_pages.utils.auth import render_auth_status

        st.title(self.variables_dia_quant.title)
        with st.container(horizontal=True, gap="small"):
            st.link_button(
                "Module documentation",
                url=self.variables_dia_quant.doc_url,
                type="secondary",
                icon="📖",
                help="link to the module documentation",
            )
            st.link_button(
                "Download input files",
                url=self.variables_dia_quant.raw_data_url,
                type="secondary",
                icon="⬇️",
                help="Download the raw input files used to benchmark this module",
            )
            render_auth_status(key_suffix=key_suffix)
        if self.variables_dia_quant.beta_warning:
            st.warning(
                "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
            )

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
                "View Public Results",
                "Upload New Results (Private)",
                "View Single Result",
                "View Public + New Results",
                "Submit New Results",
            ]
        )

        # Tab 1: View Public Results
        with tab_results_all:
            self._render_header(key_suffix="_results_all")
            self.quant_uiobjects.display_all_data_results_main()

        # Tab 2: Upload New Results (Private)
        with tab_submission_details:
            self._render_header(key_suffix="_submission_details")
            self.quant_uiobjects.display_submission_form()

        # Tab 3: View Single Result
        with tab_indepth_plots:
            self._render_header(key_suffix="_indepth_plots")

            self.quant_uiobjects.display_indepth_plots()

        # Tab 4: View Public + New Results
        with tab_results_new:
            self._render_header(key_suffix="_results_new")
            self.quant_uiobjects.display_all_data_results_submitted()

        # Tab 5: Submit New Results
        with tab_public_submission:
            self._render_header(key_suffix="_public_submission")
            self.quant_uiobjects.display_public_submission_ui()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()  # Instantiate and run the extended UI class
