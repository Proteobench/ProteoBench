import re
from typing import Dict, Optional

import pandas as pd


def load_input_file(input_csv: str, input_format: str) -> pd.DataFrame:
    """
    Loads a dataframe from a CSV file depending on its format.

    Args:
        input_csv (str): The path to the CSV file.
        input_format (str): The format of the input file (e.g., "WOMBAT", "Custom").

    Returns:
        pd.DataFrame: The loaded dataframe with the required columns added (like "proforma").
    """
    input_data_frame: pd.DataFrame
    if input_format == "WOMBAT":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
        input_data_frame["proforma"] = input_data_frame["modified_peptide"]
    elif input_format == "Custom":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        input_data_frame["proforma"] = input_data_frame["Modified sequence"]

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
    Aggregate modifications into a string representing the modified sequence.

    Args:
        input_string_seq (str): The input sequence string.
        input_string_modifications (str): The modifications applied to the sequence.
        special_locations (Dict[str, int], optional): A dictionary specifying special locations for modifications.

    Returns:
        str: The modified sequence string with aggregated modifications.
    """
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


def count_chars(input_string: str, isalpha: bool = True, isupper: bool = True) -> int:
    """
    Count the number of characters in the string that match the given criteria.

    Args:
        input_string (str): The input string.
        isalpha (bool, optional): Whether to count alphabetic characters. Defaults to True.
        isupper (bool, optional): Whether to count uppercase characters. Defaults to True.

    Returns:
        int: The count of characters that match the criteria.
    """
    if isalpha and isupper:
        return sum(1 for char in input_string if char.isalpha() and char.isupper())
    if isalpha:
        return sum(1 for char in input_string if char.isalpha())
    if isupper:
        return sum(1 for char in input_string if char.isupper())


def get_stripped_seq(input_string: str, isalpha: bool = True, isupper: bool = True) -> str:
    """
    Get a stripped version of the sequence containing only characters that match the given criteria.

    Args:
        input_string (str): The input string.
        isalpha (bool, optional): Whether to include alphabetic characters. Defaults to True.
        isupper (bool, optional): Whether to include uppercase characters. Defaults to True.

    Returns:
        str: The stripped sequence.
    """
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
) -> tuple:
    """
    Match and extract bracketed modifications from the string.

    Args:
        input_string (str): The input string.
        pattern (str, optional): The regular expression pattern for matching modifications. Defaults to `r"\[([^]]+)\]"`.
        isalpha (bool, optional): Whether to match alphabetic characters. Defaults to True.
        isupper (bool, optional): Whether to match uppercase characters. Defaults to True.

    Returns:
        tuple: A tuple containing the matched modifications and their positions.
    """
    matches = [(match.group(), match.start(), match.end()) for match in re.finditer(pattern, input_string)]
    positions = (count_chars(input_string[0 : m[1]], isalpha=isalpha, isupper=isupper) for m in matches)
    mods = (m[0] for m in matches)
    return mods, positions


def to_lowercase(match: re.Match) -> str:
    """
    Convert a match to lowercase.

    Args:
        match (re.Match): The match object from a regular expression.

    Returns:
        str: The lowercase version of the matched string.
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
    Generate a proforma string with bracketed modifications.

    Args:
        input_string (str): The input sequence string.
        before_aa (bool, optional): Whether to add the modification before the amino acid. Defaults to True.
        isalpha (bool, optional): Whether to include alphabetic characters. Defaults to True.
        isupper (bool, optional): Whether to include uppercase characters. Defaults to True.
        pattern (str, optional): The regular expression pattern for matching modifications. Defaults to `r"\[([^]]+)\]"`.
        modification_dict (Dict[str, str], optional): A dictionary of modifications and their names.

    Returns:
        str: The proforma sequence with bracketed modifications.
    """
    input_string = re.sub(pattern, to_lowercase, input_string)
    modifications, positions = match_brackets(input_string, pattern=pattern, isalpha=isalpha, isupper=isupper)
    new_modifications = []

    for m in modifications:
        if m in modification_dict:
            new_modifications.append(modification_dict[m])
        else:
            new_modifications.append(m)

    modifications = new_modifications
    pos_mod_dict = dict(zip(positions, modifications))

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
