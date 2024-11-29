import logging
from typing import Any, Dict, Type

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.base_pages.quant import QuantUIObjects
from pages.module_pages.quant_lfq_ion_DIA_AIF import StreamlitUI
from pages.pages_variables.Quant.lfq.ion.DIA.ion_diaPASEF import (
    VariablesDIAQuantdiaPASEF,
)
from pages.texts.generic_texts import WebpageTexts

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.lfq.ion.DIA.quant_lfq_ion_DIA_diaPASEF import (
    DIAQuantIonModulediaPASEF,
)


class StreamlitUIdiaPASEF(StreamlitUI):
    def __init__(self):
        self.variables_dia_quant: VariablesDIAQuantdiaPASEF = VariablesDIAQuantdiaPASEF()
        self.texts: Type[WebpageTexts] = WebpageTexts
        self.texts.ShortMessages.title = "DIA Ion quantification - diaPASEF"
        self.user_input: Dict[str, Any] = dict()

        pbb.proteobench_page_config()

        if self.variables_dia_quant.submit not in st.session_state:
            st.session_state[self.variables_dia_quant.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule: DIAQuantIonModulediaPASEF = DIAQuantIonModulediaPASEF(token=token)
        self.parsesettingsbuilder = ParseSettingsBuilder(
            module_id=self.ionmodule.module_id, parse_settings_dir=self.variables_dia_quant.parse_settings_dir
        )

        self.quant_uiobjects = QuantUIObjects(self.variables_dia_quant, self.ionmodule, self.parsesettingsbuilder)

        self._main_page()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUIdiaPASEF()  # Instantiate and run the extended UI class
