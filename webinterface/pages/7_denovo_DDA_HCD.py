"""
Streamlit UI for the DDA quantification - precursor ions module.
"""

import logging

from pages.base import BaseStreamlitUI
from pages.base_pages.denovo import DeNovoUIObjects
from pages.pages_variables.DeNovo.DDA_HCD_variables import VariablesDDADeNovo
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule


class StreamlitUI(BaseStreamlitUI):
    """
    Streamlit UI for the DDA de novo identification module.
    """

    def __init__(self, **kwargs):
        """
        Initialize the Streamlit UI for the DDA de novo identification module.
        """
        super().__init__(**kwargs)

    def get_tab_config(self) -> list:
        """Override tab configuration for De Novo module (5 tabs instead of 6)."""
        return [
            ("View Public Results", "display_all_data_results_main"),
            ("Upload New Results (Private)", "display_submission_form"),
            ("View Public + New Results", "display_all_data_results_submitted"),
            ("Compare Results", "display_indepth_plots"),
            ("Submit New Results", "display_public_submission_ui"),
        ]


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    # Instantiate and run the extended UI class
    st_ui = StreamlitUI(
        variables=VariablesDDADeNovo(),
        texts=WebpageTexts,
        ionmodule=DDAHCDDeNovoModule,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=DeNovoUIObjects,
        page_name="De novo DDA-HCD peptidoform",
    )
    st_ui.main_page()
