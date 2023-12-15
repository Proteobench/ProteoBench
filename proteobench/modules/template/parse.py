from __future__ import annotations

from typing import Dict, List

import pandas as pd

from proteobench.modules.template.__init__ import ParseInputsInterface
from proteobench.modules.template.parse_settings import ParseSettings


class ParseInputs(ParseInputsInterface):
    def convert_to_standard_format(df: pd.DataFrame, parse_settings: ParseSettings) -> pd.DataFrame:
        """Convert a search engine output into a generic format supported by the module."""

        for k, v in parse_settings.mapper.items():
            if k not in df.columns:
                raise ImportError(
                    f"Column {k} not found in input dataframe. Please check input file and selected search engine."
                )

        df.rename(columns=parse_settings.mapper, inplace=True)

        standard_structure = {}
        for k, v in parse_settings.condition_mapper.items():
            try:
                standard_structure[v].append(k)
            except KeyError:
                standard_structure[v] = [k]

        # TODO add more standardization steps here

        return standard_structure
