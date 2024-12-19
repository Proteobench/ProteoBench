import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq.ion.DDA.variables import VariablesDDAQuant
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.lfq.ion.DDA.quant_lfq_ion_DDA import DDAQuantIonModule


class StreamlitUI:
    def __init__(self):
        self.variables_dda_quant: VariablesDDAQuant = VariablesDDAQuant()
        self.texts: Type[WebpageTexts] = WebpageTexts

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
            st.write(f"The full description of the module is available [here]({self.variables_dda_quant.doc_url})")
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_all_data_results_main()

        # Tab 2: Submission Details
        with tab_submission_details:
            st.title(self.variables_dda_quant.title)

            st.write(f"The full description of the module is available [here]({self.variables_dda_quant.doc_url})")
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_submission_form()

        # Tab 2.5: in-depth plots current data
        with tab_indepth_plots:
            st.title(self.variables_dda_quant.title)

            st.write(f"The full description of the module is available [here]({self.variables_dda_quant.doc_url})")
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.generate_current_data_plots(True)

        # Tab 3: Results (New Submissions)
        with tab_results_new:
            st.title(self.variables_dda_quant.title)
            st.write(f"The full description of the module is available [here]({self.variables_dda_quant.doc_url})")
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )

            self.quant_uiobjects.display_all_data_results_submitted()

        # Tab 4: Public Submission
        with tab_public_submission:
            st.title(self.variables_dda_quant.title)
            st.write(f"The full description of the module is available [here]({self.variables_dda_quant.doc_url})")
            if self.variables_dda_quant.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.quant_uiobjects.display_public_submission_ui()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()  # Instantiate and run the extended UI class
