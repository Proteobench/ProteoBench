"""
Module for parsing peptidoform strings and extracting modifications.
"""

import math
import os
import re
import warnings
from typing import Dict

import pandas as pd


def load_input_file(input_csv: str, input_format: str) -> pd.DataFrame:
    """
    Load a dataframe from a CSV file depending on its format.

    Parameters
    ----------
    input_csv : str
        The path to the CSV file.
    input_format : str
        The format of the input file (e.g., "WOMBAT", "Custom").

    Returns
    -------
    pd.DataFrame
        The loaded dataframe with the required columns added (like "proforma").
    """
    try:
        if input_format == "MaxQuant":
            warnings.warn(
                """
                WARNING: MaxQuant proforma parsing does not take into account fixed modifications\n
                because they are implicit. Only after providing the appropriate parameter file,\n
                fixed modifications will be added correctly.
                """
            )
        load_function = _LOAD_FUNCTIONS[input_format]
    except KeyError as e:
        raise ValueError(f"Invalid input format: {input_format}") from e

    return load_function(input_csv)


def aggregate_modification_column(
    input_string_seq: str,
    input_string_modifications: str,
    special_locations: Dict[str, int] = {
        "Any N-term": 0,
        "Any C-term": -1,
        "Protein N-term": 0,
        "Protein C-term": -1,
        "N-Term": 0,  # Added to handle "N-Term"
        "C-Term": -1,  # If you also expect "C-Term"
    },
) -> str:
    """
    Aggregate modifications into a string representing the modified sequence.

    This version handles both:
    - Original format (e.g. "Methylation (C11)" or "Carbamidomethyl (Any N-term)")
    - New format (e.g. "1xCarbamidomethyl [C11]", "1xOxidation [M4]", "1xAcetyl [N-Term]")

    Parameters
    ----------
    input_string_seq : str
        The input sequence string.
    input_string_modifications : str
        The modifications applied to the sequence.
    special_locations : dict, optional
        A dictionary specifying special locations for modifications.

    Returns
    -------
    str
        The modified sequence string with aggregated modifications.
    """

    # If no modifications, return the original sequence unchanged
    if not input_string_modifications.strip():
        return input_string_seq

    # Split modifications by ';' to handle multiple modifications
    raw_mods = [x.strip() for x in input_string_modifications.split(";") if x.strip()]

    all_mods = []

    for m in raw_mods:
        # Detect format by checking for '(' or '['
        if "(" in m and "[" not in m:
            # Original format (e.g. "Carbamidomethyl (C11)" or "Methylation (Any N-term)")
            parts = m.split(" (")
            if len(parts) < 2:
                continue
            m_name = parts[0].strip()
            m_stripped = parts[1].rstrip(")")

            # Check if this is a special location
            if m_stripped in special_locations:
                loc = special_locations[m_stripped]
                if loc == -1:
                    loc = len(input_string_seq)  # C-term
                all_mods.append((m_name, loc))
            else:
                # Assume format like C11 means position 11
                loc = int(m_stripped[1:])
                all_mods.append((m_name, loc))

        else:
            # New format, e.g. "1xCarbamidomethyl [C11]", "1xAcetyl [N-Term]"
            # Remove any count prefix like "1x"
            entry = re.sub(r"\d+x", "", m).strip()

            # Extract modification name and bracketed portion
            mod_name_match = re.match(r"([A-Za-z]+)\s*\[(.+)\]", entry)
            if not mod_name_match:
                continue

            mod_name = mod_name_match.group(1)
            positions_str = mod_name_match.group(2).strip()

            # Positions could be multiple (e.g. "C10; C13")
            pos_parts = [p.strip() for p in positions_str.split(";") if p.strip()]
            if not pos_parts:
                # If there's nothing after the brackets, skip
                continue

            for pos_part in pos_parts:
                # Check if pos_part is a known special location (e.g. "N-Term")
                if pos_part in special_locations:
                    loc = special_locations[pos_part]
                    if loc == -1:
                        loc = len(input_string_seq)
                    all_mods.append((mod_name, loc))
                else:
                    # Otherwise, assume format like C11 or M4
                    if len(pos_part) > 1:
                        loc = int(pos_part[1:])
                        all_mods.append((mod_name, loc))

    # Sort modifications by descending position so we insert from the end
    all_mods.sort(key=lambda x: x[1], reverse=True)

    for name, loc in all_mods:
        # Insert the modification into the sequence.
        # 'loc' is a 1-based index if it's a residue position.
        # For terminal modifications, special_locations will have adjusted it.
        # If loc is -1 or at sequence end, we've already resolved it to len(sequence).

        # Insert the modification brackets at position 'loc'.
        # Note: If loc == 0 (N-term), insert at start of sequence.
        #       If loc == len(sequence), insert at end (C-term).
        input_string_seq = input_string_seq[:loc] + f"[{name}]" + input_string_seq[loc:]

    return input_string_seq


def count_chars(input_string: str, isalpha: bool = True, isupper: bool = True) -> int:
    """
    Count the number of characters in the string that match the given criteria.

    Parameters
    ----------
    input_string : str
        The input string.
    isalpha : bool, optional
        Whether to count alphabetic characters. Defaults to True.
    isupper : bool, optional
        Whether to count uppercase characters. Defaults to True.

    Returns
    -------
    int
        The count of characters that match the criteria.
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

    Parameters
    ----------
    input_string : str
        The input string.
    isalpha : bool, optional
        Whether to include alphabetic characters. Defaults to True.
    isupper : bool, optional
        Whether to include uppercase characters. Defaults to True.

    Returns
    -------
    str
        The stripped sequence.
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

    Parameters
    ----------
    input_string : str
        The input string.
    pattern : str, optional
        The regular expression pattern for matching modifications. Defaults to `r"\\[([^]]+)\\]"`.
    isalpha : bool, optional
        Whether to match alphabetic characters. Defaults to True.
    isupper : bool, optional
        Whether to match uppercase characters. Defaults to True.

    Returns
    -------
    tuple
        A tuple containing the matched modifications and their positions.
    """
    matches = [(match.group(), match.start(), match.end()) for match in re.finditer(pattern, input_string)]
    positions = (count_chars(input_string[0 : m[1]], isalpha=isalpha, isupper=isupper) for m in matches)
    mods = (m[0] for m in matches)
    return mods, positions


def to_lowercase(match: re.Match) -> str:
    """
    Convert a match to lowercase.

    Parameters
    ----------
    match : re.Match
        The match object from a regular expression.

    Returns
    -------
    str
        The lowercase version of the matched string.
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
    Get the proforma sequence with bracketed modifications.

    Parameters
    ----------
    input_string : str
        The input sequence string.
    before_aa : bool, optional
        Whether to add the modification before the amino acid. Defaults to True.
    isalpha : bool, optional
        Whether to include alphabetic characters. Defaults to True.
    isupper : bool, optional
        Whether to include uppercase characters. Defaults to True.
    pattern : str, optional
        The regular expression pattern for matching modifications. Defaults to `r"\[([^]]+)\]"`.
    modification_dict : dict, optional
        A dictionary of modifications and their names.

    Returns
    -------
    str
        The proforma sequence with bracketed modifications.
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


def _load_proteome_discoverer(input_csv: str) -> pd.DataFrame:
    """
    Load a Proteome Discoverer output file.

    Parameters
    ----------
    input_csv : str
        The path to the Proteome Discoverer output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    input_data_frame["Modifications"].fillna("", inplace=True)
    input_data_frame["proforma"] = input_data_frame.apply(
        lambda x: aggregate_modification_column(x["Sequence"], x["Modifications"]),
        axis=1,
    )
    return input_data_frame


def _load_wombat(input_csv: str) -> pd.DataFrame:
    """
    Load a WOMBAT output file.

    Parameters
    ----------
    input_csv : str
        The path to the WOMBAT output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    print(input_csv)
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()

    non_strings = input_data_frame["protein_group"][
        ~input_data_frame["protein_group"].apply(lambda x: isinstance(x, str))
    ]

    input_data_frame["protein_group"] = input_data_frame["protein_group"].map(
        lambda x: ";".join([mapper[protein] if protein in mapper.keys() else protein for protein in str(x).split(",")])
    )
    input_data_frame["proforma"] = input_data_frame["modified_peptide"]
    return input_data_frame


def _load_custom(input_csv: str) -> pd.DataFrame:
    """
    Load a custom output file.

    Parameters
    ----------
    input_csv : str
        The path to the custom output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    input_data_frame["proforma"] = input_data_frame["Modified sequence"]
    return input_data_frame


def _load_peaks(input_csv: str) -> pd.DataFrame:
    """
    Load a PEAKS output file.

    Parameters
    ----------
    input_csv : str
        The path to the PEAKS output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
    return input_data_frame


_LOAD_FUNCTIONS = {
    "Proteome Discoverer": _load_proteome_discoverer,
    "WOMBAT": _load_wombat,
    "Custom": _load_custom,
    "PEAKS": _load_peaks,
}
