from __future__ import annotations

from typing import Tuple, Any

import pandas as pd
from pandas import DataFrame

from proteobench.github.gh import DDA_QUANT_RESULTS_REPO
from proteobench.modules.dda_quant_base.module import Module
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings_ion import (
    PRECURSOR_NAME,
    ParseSettingsBuilder,
)


class IonModule(Module):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(self):
        self.dda_quant_results_repo = DDA_QUANT_RESULTS_REPO
        self.precursor_name = PRECURSOR_NAME

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    def benchmarking(
        self, input_file: str, input_format: str, user_input: dict, all_datapoints, default_cutoff_min_prec: int = 3
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """Main workflow of the module. Used to benchmark workflow results."""

        # Parse user config
        input_df = load_input_file(input_file, input_format)
        parse_settings = ParseSettingsBuilder().build_parser(input_format)

        standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

        # Get quantification data
        intermediate_data_structure = self.generate_intermediate(standard_format, replicate_to_raw, parse_settings)

        current_datapoint = self.generate_datapoint(
            intermediate_data_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
        )

        all_datapoints = self.add_current_data_point(all_datapoints, current_datapoint)

        # TODO check why there are NA and inf/-inf values
        return (
            intermediate_data_structure,
            all_datapoints,
            input_df,
        )
