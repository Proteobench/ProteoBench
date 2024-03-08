from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd

from proteobench.modules.dda_quant_base.parse import get_proforma_bracketed
from proteobench.modules.dda_quant_ion.parse_settings import ParseSettings
from proteobench.modules.interfaces import ParseInputsInterface


class ParseInputs(ParseInputsInterface):
    def convert_to_standard_format(
        self, df: pd.DataFrame, parse_settings: ParseSettings
    ) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """Convert a software tool output into a generic format supported by the module."""
        # TODO add functionality/steps in docstring

        for k, v in parse_settings.mapper.items():
            if k not in df.columns:
                raise ImportError(
                    f"Column {k} not found in input dataframe." " Please check input file and selected software tool."
                )

        df.rename(columns=parse_settings.mapper, inplace=True)

        replicate_to_raw = {}
        for k, v in parse_settings.condition_mapper.items():
            try:
                replicate_to_raw[v].append(k)
            except KeyError:
                replicate_to_raw[v] = [k]

        if "Reverse" in parse_settings.mapper:
            df = df[df["Reverse"] != parse_settings.decoy_flag]

        df["contaminant"] = df["Proteins"].str.contains(parse_settings.contaminant_flag)
        for flag, species in parse_settings.species_dict.items():
            df[species] = df["Proteins"].str.contains(flag)
        df["MULTI_SPEC"] = (
            df[list(parse_settings.species_dict.values())].sum(axis=1) > parse_settings.min_count_multispec
        )

        df = df[df["MULTI_SPEC"] == False]

        # If there is "Raw file" then it is a long format, otherwise short format
        if "Raw file" not in parse_settings.mapper.values():
            meltvars = parse_settings.condition_mapper.keys()
            # Should be handled more elegant
            try:
                df = df.melt(
                    id_vars=list(set(df.columns).difference(set(meltvars))),
                    value_vars=meltvars,
                    var_name="Raw file",
                    value_name="Intensity",
                )
            except KeyError:
                df.columns = [c.replace(".mzML", ".mzML.gz") for c in df.columns]
                df = df.melt(
                    id_vars=list(set(df.columns).difference(set(meltvars))),
                    value_vars=meltvars,
                    var_name="Raw file",
                    value_name="Intensity",
                )

        df["replicate"] = df["Raw file"].map(parse_settings.condition_mapper)
        df = pd.concat([df, pd.get_dummies(df["Raw file"])], axis=1)

        if parse_settings.apply_modifications_parser:
            df["proforma"] = df[parse_settings.modifications_parse_column].apply(
                get_proforma_bracketed,
                before_aa=parse_settings.modifications_before_aa,
                isalpha=parse_settings.modifications_isalpha,
                isupper=parse_settings.modifications_isupper,
                pattern=parse_settings.modifications_pattern,
                modification_dict=parse_settings.modifications_mapper,
            )

        try:
            df.loc[df.index, "precursor ion"] = (
                df.loc[df.index, "proforma"] + "|Z=" + df.loc[df.index, "Charge"].map(str)
            )
        except KeyError:
            raise KeyError(
                f"Not all columns required for making the ion are available."
                "Is the charge available in the input file?"
            )

        return df, replicate_to_raw
