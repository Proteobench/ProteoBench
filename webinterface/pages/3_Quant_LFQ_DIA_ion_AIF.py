"""
Streamlit UI for the DIA quantification - precursor ions module - AIF.
"""

import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DIA_ion_AIF_variables import VariablesDIAQuant
from pages.texts.generic_texts import WebpageTexts
from pages.base import BaseStreamlitUI

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModuleAIF

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    st_ui = BaseStreamlitUI(
        variables=VariablesDIAQuant(),
        texts=WebpageTexts,
        ionmodule=DIAQuantIonModuleAIF,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=QuantUIObjects,
        page_name="Quant LFQ DIA ion AIF"
    )
    st_ui.main_page()
