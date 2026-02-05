"""
Main Streamlit UI for the DDA quantification - peptidoform module.
"""

import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base import BaseStreamlitUI
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DDA_peptidoform_variables import VariablesDDAQuant
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import (
    DDAQuantPeptidoformModule,
)

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    # Instantiate and run the extended UI class
    st_ui = BaseStreamlitUI(
        variables=VariablesDDAQuant(),
        texts=WebpageTexts,
        ionmodule=DDAQuantPeptidoformModule,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=QuantUIObjects,
        page_name="Quant LFQ DDA peptidoform",
    )
    st_ui.main_page()
