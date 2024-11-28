from __future__ import annotations

import math
import os
import re
from typing import Dict, Generator, List, Optional, Tuple, Union

import pandas as pd


def load_input_file(input_csv: str, input_format: str) -> pd.DataFrame:
    """
    Loads a DataFrame from a CSV file based on the specified format. The reading
    can be customized based on the format to handle specific columns and data. Only
    things that cannot be (easily) generalized are handled here when reading.

    Parameters:
        input_csv (str): Path to the input CSV file.
        input_format (str): Format of the input file (e.g., MaxQuant, Sage, AlphaPept).

    Returns:
        pd.DataFrame: The loaded DataFrame with additional processing as per the format.
    """
    input_data_frame: pd.DataFrame
    if input_format == "MaxQuant":
        input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
    elif input_format == "AlphaPept":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, dtype={"charge": int})
    elif input_format == "Sage":
        input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
    elif input_format == "FragPipe":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        input_data_frame["Protein"] = input_data_frame["Protein"] + "," + input_data_frame["Mapped Proteins"].fillna("")
    elif input_format == "WOMBAT":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
        input_data_frame["proforma"] = input_data_frame["modified_peptide"]
    elif input_format == "ProlineStudio":
        input_data_frame = pd.read_excel(input_csv, sheet_name="Quantified peptide ions", header=0, index_col=None)
        input_data_frame["modifications"] = input_data_frame["modifications"].fillna("")
        input_data_frame["proforma"] = input_data_frame.apply(
            lambda x: aggregate_modification_column(x.sequence, x.modifications), axis=1
        )
    elif input_format == "i2MassChroQ":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        input_data_frame["proforma"] = input_data_frame["ProForma"]
    elif input_format == "Custom":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        input_data_frame["proforma"] = input_data_frame["Modified sequence"]
    elif input_format == "DIA-NN":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    elif input_format == "AlphaDIA":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
        mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
        mapper = mapper_df["description"].to_dict()
        input_data_frame["genes"] = input_data_frame["genes"].map(
            lambda x: ";".join([mapper[protein] if protein in mapper.keys() else protein for protein in x.split(";")])
        )
        input_data_frame["proforma"] = input_data_frame.apply(
            lambda x: aggregate_modification_sites_column(x.sequence, x.mods, x.mod_sites), axis=1
        )
    elif input_format == "FragPipe (DIA-NN quant)":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
        mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
        mapper = mapper_df["description"].to_dict()
        input_data_frame["Protein.Names"] = input_data_frame["Protein.Ids"].map(mapper)
    elif input_format == "Spectronaut":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        if input_data_frame["FG.Quantity"].dtype == object:
            input_csv.seek(0)
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t", decimal=",")
        input_data_frame["FG.LabeledSequence"] = input_data_frame["FG.LabeledSequence"].str.strip("_")
        mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
        mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
        mapper = mapper_df["description"].to_dict()
        input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].str.split(";")
        input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].map(
            lambda x: [mapper[protein] if protein in mapper.keys() else protein for protein in x]
        )
        input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].str.join(";")
    elif input_format == "MSAID":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")

    return input_data_frame


def aggregate_modification_column(
    input_string_seq: str,
    input_string_modifications: str,
    special_locations: Dict[str, int] = {
        "Any N-term": 0,
        "Any C-term": -1,
        "Protein N-term": 0,
        "Protein C-term": -1,
    },
) -> str:
    """
    Inserts modifications into a peptide sequence based on provided positions.

    Parameters:
        input_string_seq (str): The peptide sequence.
        input_string_modifications (str): Modifications with positions.
        special_locations (Dict[str, int]): Mapping of special locations to sequence positions.

    Returns:
        str: The peptide sequence with modifications inserted.
    """
    # Logic to process modification columns
    ...


def aggregate_modification_sites_column(
    input_string_seq: str, input_string_modifications: str, input_string_sites: Union[str, float]
) -> str:
    """
    Processes modification sites and inserts them into the peptide sequence.

    Parameters:
        input_string_seq (str): The peptide sequence.
        input_string_modifications (str): Modifications at sites.
        input_string_sites (Union[str, float]): Modification site positions.

    Returns:
        str: The peptide sequence with modifications at specific sites.
    """
    if isinstance(input_string_modifications, float) and math.isnan(input_string_modifications):
        return input_string_seq

    mods_list = input_string_modifications.split(";")
    sites_list = list(map(int, str(input_string_sites).split(";")))
    mods_and_sites = sorted(zip(mods_list, sites_list), key=lambda x: x[1], reverse=True)

    for mod, site in mods_and_sites:
        mod_name = mod.split("@")[0]
        if site == 0:
            input_string_seq = f"[{mod_name}]-" + input_string_seq
        elif site == -1:
            input_string_seq += f"-[{mod_name}]"
        else:
            input_string_seq = input_string_seq[:site] + f"[{mod_name}]" + input_string_seq[site:]

    return input_string_seq


def count_chars(input_string: str, isalpha: bool = True, isupper: bool = True) -> int:
    """
    Counts characters in a string based on provided criteria.

    Parameters:
        input_string (str): The string to analyze.
        isalpha (bool): If True, count only alphabetic characters.
        isupper (bool): If True, count only uppercase characters.

    Returns:
        int: The count of matching characters.
    """
    return sum(
        1 for char in input_string if (char.isalpha() if isalpha else True) and (char.isupper() if isupper else True)
    )


def get_stripped_seq(input_string: str, isalpha: bool = True, isupper: bool = True) -> str:
    """
    Strips a sequence to only matching characters based on criteria.

    Parameters:
        input_string (str): The input sequence.
        isalpha (bool): If True, retain only alphabetic characters.
        isupper (bool): If True, retain only uppercase characters.

    Returns:
        str: The stripped sequence.
    """
    return "".join(
        char for char in input_string if (char.isalpha() if isalpha else True) and (char.isupper() if isupper else True)
    )


def match_brackets(
    input_string: str,
    pattern: str = r"\[([^]]+)\]",
    isalpha: bool = True,
    isupper: bool = True,
) -> Tuple[Generator[str, None, None], Generator[int, None, None]]:
    """
    Matches and extracts bracketed content from a string.

    Parameters:
        input_string (str): The string to analyze.
        pattern (str): Regex pattern for matching brackets. Default is r"\[([^]]+)\]".
        isalpha (bool): If True, count only alphabetic characters.
        isupper (bool): If True, count only uppercase characters.

    Returns:
        Tuple[Generator[str, None, None], Generator[int, None, None]]:
            A tuple of modifications and their positions.
    """
    matches = [(match.group(), match.start(), match.end()) for match in re.finditer(pattern, input_string)]
    positions = (count_chars(input_string[0 : m[1]], isalpha=isalpha, isupper=isupper) for m in matches)
    mods = (m[0] for m in matches)
    return mods, positions


def to_lowercase(match: re.Match) -> str:
    """
    Converts a regex match to lowercase.

    Parameters:
        match (re.Match): The match object.

    Returns:
        str: The lowercase version of the match.
    """
    return match.group(0).lower()


def get_proforma_bracketed(
    input_string: str,
    before_aa: bool = True,
    isalpha: bool = True,
    isupper: bool = True,
    pattern: str = r"\[([^]]+)\]",
    modification_dict: Dict[str, str] = {
        "+57.0215": "Carbamidomethyl",
        "+15.9949": "Oxidation",
        "-17.026548": "Gln->pyro-Glu",
        "-18.010565": "Glu->pyro-Glu",
        "+42": "Acetyl",
    },
) -> str:
    """
    Processes a sequence to include ProForma bracketed modifications.

    Parameters:
        input_string (str): The peptide sequence.
        before_aa (bool): If True, place modifications before the amino acid.
        isalpha (bool): If True, count only alphabetic characters.
        isupper (bool): If True, count only uppercase characters.
        pattern (str): Regex pattern for bracketed content. Default is r"\[([^]]+)\]".
        modification_dict (Dict[str, str]): Dictionary mapping modifications to ProForma names.

    Returns:
        str: The modified ProForma sequence.
    """
    input_string = re.sub(pattern, to_lowercase, input_string)
    modifications, positions = match_brackets(input_string, pattern=pattern, isalpha=isalpha, isupper=isupper)
    new_modifications = [modification_dict.get(m, m) for m in modifications]

    pos_mod_dict = dict(zip(positions, new_modifications))
    stripped_seq = get_stripped_seq(input_string, isalpha=isalpha, isupper=isupper)

    new_seq = ""
    for idx, aa in enumerate(stripped_seq):
        if before_aa:
            new_seq += aa
        if idx in pos_mod_dict:
            if idx == 0:
                new_seq += f"[{pos_mod_dict[idx]}]-"
            elif idx == len(stripped_seq):
                new_seq += f"-[{pos_mod_dict[idx]}]"
            else:
                new_seq += f"[{pos_mod_dict[idx]}]"
        if not before_aa:
            new_seq += aa
    return new_seq
