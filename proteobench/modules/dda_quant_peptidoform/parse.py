from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd

from proteobench.modules.dda_quant_peptidoform.parse_settings import ParseSettings
from proteobench.modules.interfaces import ParseInputsInterface


# TODO this should be generalized further
def aggregate_modification_column(
    input_string_seq: str,
    input_string_modifications: str,
    special_locations: dict = {
        "Any N-term": 0,
        "Any C-term": -1,
        "Protein N-term": 0,
        "Protein C-term": -1,
    },
):
    all_mods = []
    for m in input_string_modifications.split("; "):
        if len(m) == 0:
            continue
        m_stripped = m.split(" (")[1].rstrip(")")
        m_name = m.split(" (")[0]

        if m_stripped in special_locations.keys():
            if special_locations[m_stripped] == -1:
                all_mods.append((m_name, len(input_string_seq)))
            else:
                all_mods.append((m_name, special_locations[m_stripped]))
            continue

        all_mods.append((m_name, int(m_stripped[1:])))

    all_mods.sort(key=lambda x: x[1], reverse=True)

    for name, loc in all_mods:
        input_string_seq = input_string_seq[:loc] + f"[{name}]" + input_string_seq[loc:]

    return input_string_seq


def count_chars(input_string: str, isalpha: bool = True, isupper: bool = True):
    if isalpha and isupper:
        return sum(1 for char in input_string if char.isalpha() and char.isupper())
    if isalpha:
        return sum(1 for char in input_string if char.isalpha())
    if isupper:
        return sum(1 for char in input_string if char.isupper())


def get_stripped_seq(input_string: str, isalpha: bool = True, isupper: bool = True):
    if isalpha and isupper:
        return "".join(char for char in input_string if char.isalpha() and char.isupper())
    if isalpha:
        return "".join(char for char in input_string if char.isalpha())
    if isupper:
        return "".join(char for char in input_string if char.isupper())


def match_brackets(
    input_string: str,
    pattern: str = r"\[([^]]+)\]",
    isalpha: bool = True,
    isupper: bool = True,
):
    matches = [(match.group(1), match.start(1), match.end(1)) for match in re.finditer(pattern, input_string)]
    positions = (count_chars(input_string[0 : m[1]], isalpha=isalpha, isupper=isupper) for m in matches)
    mods = (m[0] for m in matches)
    return mods, positions


def get_proforma_bracketed(
    input_string,
    before_aa: bool = True,
    isalpha: bool = True,
    isupper: bool = True,
    pattern: str = r"\[([^]]+)\]",
    modification_dict: dict = {
        "+57.0215": "Carbamidomethyl",
        "+15.9949": "Oxidation",
        "-17.026548": "Gln->pyro-Glu",
        "-18.010565": "Glu->pyro-Glu",
        "+42": "Acetyl",
    },
):
    modifications, positions = match_brackets(input_string, pattern=pattern, isalpha=isalpha, isupper=isupper)

    new_modifications = []
    for m in modifications:
        try:
            new_modifications.append(modification_dict[m])
        except KeyError:
            new_modifications.append(m)
    modifications = new_modifications

    pos_mod_dict = dict(zip(positions, modifications))

    stripped_seq = get_stripped_seq(input_string, isalpha=isalpha, isupper=isupper)

    new_seq = ""
    for idx, aa in enumerate(stripped_seq):
        if before_aa:
            new_seq += aa
        if idx in pos_mod_dict.keys():
            if idx == 0:
                new_seq += f"[{pos_mod_dict[idx]}]-"
            elif idx == len(stripped_seq) - 1:
                new_seq += f"-[{pos_mod_dict[idx]}]"
            else:
                new_seq += f"[{pos_mod_dict[idx]}]"
        if not before_aa:
            new_seq += aa

    return new_seq


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
            df.loc[df.index, "precursor ion"] = df.loc[df.index, "proforma"]
        except KeyError:
            raise KeyError(
                f"Not all columns required for making the ion are available."
                "Is the charge available in the input file?"
            )

        return df, replicate_to_raw
