from __future__ import annotations

import pandas as pd

from proteobench.modules.dda_quant_base.module import Module
from proteobench.modules.dda_quant_peptidoform.parse import (
    ParseInputs,
    aggregate_modification_column,
)
from proteobench.modules.dda_quant_peptidoform.parse_settings import ParseSettings


class PeptidoformModule(Module):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(self, parse_settings):
        super().__init__(parse_settings)

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

