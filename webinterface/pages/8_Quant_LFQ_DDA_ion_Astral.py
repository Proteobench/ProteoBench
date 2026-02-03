"""
Streamlit UI for the DDA quantification - precursor ions Astral module.
"""

import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DDA_ion_Astral_variables import (
    VariablesDDAQuantAstral,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_Astral import DDAQuantIonAstralModule
from pages.base import BaseStreamlitUI

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    # Instantiate and run the extended UI class
    st_ui = BaseStreamlitUI(
        variables=VariablesDDAQuantAstral(),
        texts=WebpageTexts,
        ionmodule=DDAQuantIonAstralModule,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=QuantUIObjects,
        page_name="Quant LFQ DDA ion Astral"
    )
    st_ui.main_page()
