"""
Streamlit UI for the DIA quantification - precursor ions module - ZenoTOF.
"""

import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base import BaseStreamlitUI
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DIA_ion_ZenoTOF_variables import (
    VariablesDIAQuantZenoTOF,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DIA_ZenoTOF import DIAQuantIonModuleZenoTOF

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    # Instantiate and run the extended UI class
    st_ui = BaseStreamlitUI(
        variables=VariablesDIAQuantZenoTOF(),
        texts=WebpageTexts,
        ionmodule=DIAQuantIonModuleZenoTOF,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=QuantUIObjects,
        page_name="Quant LFQ DIA ion ZenoTOF",
    )
    st_ui.main_page()
