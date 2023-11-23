from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd

from proteobench.modules.dda_quant.parse_settings import ParseSettings
from proteobench.modules.interfaces import ParseInputsInterface


def count_chars(input_string):
    return sum(1 for char in input_string if char.isalpha() and char.isupper())


def match_brackets(input_string):
    pattern = r"\[([^]]+)\]"
    matches = [
        (match.group(1), match.start(1), match.end(1))
        for match in re.finditer(pattern, input_string)
    ]
    positions = (count_chars(input_string[0 : m[1]]) for m in matches)
    mods = (m[0] for m in matches)
    return mods, positions


def get_proforma_sage(
    input_string,
    modification_dict={
        "+57.0215": "Carbamidomethyl",
        "+15.9949": "Oxidation",
        "-17.026548": "Gln->pyro-Glu",
        "-18.010565": "Glu->pyro-Glu",
        "+42": "Acetyl",
    },
):
    modifications, positions = match_brackets(input_string)

    new_modifications = []
    for m in modifications:
        try:
            new_modifications.append(modification_dict[m])
        except KeyError:
            new_modifications.append("")
    modifications = new_modifications

    pos_mod_dict = dict(zip(positions, modifications))

    stripped_seq = "".join(
        char for char in input_string if char.isalpha() and char.isupper()
    )

    new_seq = ""
    for idx, aa in enumerate(stripped_seq):
        if idx in pos_mod_dict.keys():
            new_seq += f"[{pos_mod_dict[idx]}]"
        new_seq += aa

    return new_seq


def get_proforma_msfragger(
    input_string,
    modification_dict={
        "57.0215": "Carbamidomethyl",
        "15.9949": "Oxidation",
        "-17.026548": "Gln->pyro-Glu",
        "-18.010565": "Glu->pyro-Glu",
        "42.0106": "Acetyl",
    },
):
    modifications, positions = match_brackets(input_string)

    new_modifications = []
    for m in modifications:
        try:
            new_modifications.append(modification_dict[m])
        except KeyError:
            new_modifications.append("")
    modifications = new_modifications

    pos_mod_dict = dict(zip(positions, modifications))

    stripped_seq = "".join(
        char for char in input_string if char.isalpha() and char.isupper()
    )

    new_seq = ""
    for idx, aa in enumerate(stripped_seq):
        if idx in pos_mod_dict.keys():
            new_seq += f"[{pos_mod_dict[idx]}]"
        new_seq += aa

    return new_seq


def get_proforma_alphapept(
    input_string,
    modification_dict={
        "ox": "Oxidation",
        "c": "Carbamidomethyl",
        "a": "Acetyl",
        "decoy": "",
    },
):
    modifications, positions = match_seq(input_string, pattern=re.compile(r"([a-z]+)"))
    modifications = (modification_dict[m] for m in modifications)
    pos_mod_dict = dict(zip(positions, modifications))

    stripped_seq = "".join(char for char in input_string if not char.islower())

    new_seq = ""
    for idx, aa in enumerate(stripped_seq):
        new_seq += aa
        if idx in pos_mod_dict.keys():
            new_seq += f"[{pos_mod_dict[idx]}]"
    return new_seq


def count_upper_chars(input_string):
    return sum(1 for char in input_string if char.isupper())


def match_seq(input_string, pattern=re.compile(r"([a-z]+)")):
    matches = [
        (match.group(1), match.start(1), match.end(1))
        for match in pattern.finditer(input_string)
    ]
    positions = (count_upper_chars(input_string[0 : m[1]]) for m in matches)
    mods = (m[0] for m in matches)
    return mods, positions


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
        try:
            df.loc[df.index, "peptidoform"] = (
                df.loc[df.index, "proforma"]
                + "|Z="
                + df.loc[df.index, "Charge"].map(str)
            )
        except KeyError:
            # TODO if charge is not available it is now replaced with 2
            df.loc[df.index, "peptidoform"] = df.loc[df.index, "proforma"] + "|Z=2"

        # TODO use peptide_ion or peptidoform here
        # TODO move this to datapoint, keep a count here of quantified AA
        count_non_zero = (
            df.groupby(["Sequence", "Raw file"])["Intensity"].sum() > 0.0
        ).groupby(level=[0]).sum() == 6

        allowed_peptidoforms = list(count_non_zero.index[count_non_zero])
        filtered_df = df[df["Sequence"].isin(allowed_peptidoforms)]

        return filtered_df, replicate_to_raw
