"""
Streamlit UI for the DIA entrapment - precursor ions module - Plasma.
"""

import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base import BaseStreamlitUI
from pages.base_pages.entrapment import EntrapmentUIObjects
from pages.pages_variables.Entrapment.Entrapment_DIA_ion_Astral_variables import (
    VariablesDIAEntrapmentAstral,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.entrapment.entrapment_ion_DIA_Astral import DIAEntrapmentIonModuleAstral

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    # Instantiate and run the extended UI class
    st_ui = BaseStreamlitUI(
        variables=VariablesDIAEntrapmentAstral(),
        texts=WebpageTexts,
        ionmodule=DIAEntrapmentIonModuleAstral,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=EntrapmentUIObjects,
        page_name="Entrapment DIA ion Astral",
    )
    st_ui.main_page()
