from __future__ import annotations

from typing import Dict, List

import pandas as pd

from proteobench.modules.dda_quant.parse_settings import ParseSettings
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
                    f"Column {k} not found in input dataframe."
                    " Please check input file and selected software tool."
                )

        df.rename(columns=parse_settings.mapper, inplace=True)

        replicate_to_raw = {}
        for k, v in parse_settings.replicate_mapper.items():
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
            df[list(parse_settings.species_dict.values())].sum(axis=1)
            > parse_settings.min_count_multispec
        )

        df = df[df["MULTI_SPEC"] == False]

        # If there is "Raw file" then it is a long format, otherwise short format
        # TODO we might need to generalize this with toml
        if "Raw file" not in parse_settings.mapper.values():
            meltvars = parse_settings.replicate_mapper.keys()
            df = df.melt(
                id_vars=list(set(df.columns).difference(set(meltvars))),
                value_vars=meltvars,
                var_name="Raw file",
                value_name="Intensity",
            )

        # TODO replace with condition_mapper
        df["replicate"] = df["Raw file"].map(parse_settings.replicate_mapper)
        df = pd.concat([df, pd.get_dummies(df["Raw file"])], axis=1)

        # TODO, if "Charge" is not available return a sensible error
        # TODO, include modifications for ion
        df.loc[df.index, "peptidoform"] = (
            df.loc[df.index, "proforma"] + "|Z=" + df.loc[df.index, "Charge"].map(str)
        )

        # TODO use peptide_ion or peptidoform here
        # TODO move this to datapoint, keep a count here of quantified AA
        count_non_zero = (
            df.groupby(["Sequence", "Raw file"])["Intensity"].sum() > 0.0
        ).groupby(level=[0]).sum() == 6

        allowed_peptidoforms = list(count_non_zero.index[count_non_zero])
        filtered_df = df[df["Sequence"].isin(allowed_peptidoforms)]

        return filtered_df, replicate_to_raw
