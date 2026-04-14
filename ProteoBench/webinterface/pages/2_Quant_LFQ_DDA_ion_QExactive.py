"""
Streamlit UI for the DDA quantification - precursor ions module.
"""

import logging

from pages.base import BaseStreamlitUI
from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.Quant.lfq_DDA_ion_QExactive_variables import (
    VariablesDDAQuant,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import (
    DDAQuantIonModuleQExactive,
)

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

    # Instantiate and run the extended UI class
    st_ui = BaseStreamlitUI(
        variables=VariablesDDAQuant(),
        texts=WebpageTexts,
        ionmodule=DDAQuantIonModuleQExactive,
        parsesettingsbuilder=ParseSettingsBuilder,
        uiobjects=QuantUIObjects,
        page_name="Quant LFQ DDA ion QExactive",
    )
    st_ui.main_page()
