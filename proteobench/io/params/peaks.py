"""
Peaks parameter parsing.
"""

import re
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yaml

from proteobench.io.params import ProteoBenchParameters


def clean_text(text: str) -> str:
    """
    Clean the input text by removing leading and trailing spaces, colons, commas, or tabs.

    Parameters
    ----------
    text : str
        The text to be cleaned.

    Returns
    -------
    str
        The cleaned text.
    """
    text = re.sub(r"^[\s:,\t]+|[\s:,\t]+$", "", text)
    return text


def extract_value(lines: List[str], search_term: str) -> Optional[str]:
    """
    Extract the value associated with a search term from a list of lines.

    Parameters
    ----------
    lines : List[str]
        The list of lines to search through.
    search_term : str
        The term to search for in the lines.

    Returns
    -------
    Optional[str]
        The extracted value, or None if the search term is not found.
    """
    matching_line = next((line for line in lines if search_term in line), None)
    if matching_line:
        raw_value = matching_line.split(search_term, 1)[1]
        return clean_text(raw_value)
    return None


def extract_mass_tolerance(lines: List[str], search_term: str) -> Optional[str]:
    """
    Extract the mass tolerance value associated with a search term, with special handling for "System Default".

    Parameters
    ----------
    lines : List[str]
        The list of lines to search through.
    search_term : str
        The term to search for in the lines.

    Returns
    -------
    Optional[str]
        The extracted mass tolerance value, or None if the search term is not found.
    """
    value = next((clean_text(line.split(search_term)[1]) for line in lines if search_term in line), None)
    value = "40 ppm" if value == "System Default" else value
    return value


def extract_value_regex(lines: List[str], search_term: str) -> Optional[str]:
    """
    Extract the value associated with a search term using regular expressions.

    Parameters
    ----------
    lines : List[str]
        The list of lines to search through.
    search_term : str
        The regular expression to search for in the lines.

    Returns
    -------
    Optional[str]
        The extracted value, or None if the search term is not found.
    """
    return next((clean_text(re.split(search_term, line)[1]) for line in lines if re.search(search_term, line)), None)


def get_items_between(lines: list, start: str, end: str, only_last: bool = False) -> list:
    """
    Find all lines starting with '-' that appear between 'start' and 'end'.
    Return them as a list of strings, without the leading dash.

    Parameters
    ----------
    lines : list
        The list of lines to search through.
    start : str
        The start term to search for in the lines.
    end : str
        The end term to search for in the lines.
    only_last : bool
        If True, only the items found between the last occurrence of start and end will be returned.

    Returns
    -------
    list
        The list of items found between the start and end terms.
    """
    capturing = False
    items = []
    temp_items = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(start):
            capturing = True
            temp_items = []
            continue

        if capturing and stripped.startswith(end):
            capturing = False
            if only_last:
                items = temp_items[:]
            else:
                items.extend(temp_items)
            temp_items = []

        if capturing and stripped.startswith("- "):
            # Remove the dash and leading space
            item = stripped[2:].strip()
            temp_items.append(item)

    if only_last and capturing:
        items = temp_items

    return items


def read_peaks_settings(file_path: str) -> ProteoBenchParameters:
    """
    Read a PEAKS settings file, extract parameters, and return them as a `ProteoBenchParameters` object.

    Parameters
    ----------
    file_path : str
        The path to the PEAKS settings file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    if hasattr(file_path, "read"):
        lines = file_path.read().decode("utf-8").splitlines()
    else:
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise IOError(f"Failed to open or read the file at {file_path}. Error: {e}")

    lines = [line.strip() for line in lines]

    params = ProteoBenchParameters()

    params.software_name = "PEAKS"
    params.software_version = extract_value(lines, "PEAKS Version:")
    params.search_engine = "PEAKS"
    params.search_engine_version = params.software_version

    psm_fdr = extract_value(lines, "Precursor FDR:")
    # Its either "Precursor FDR:" (DIA) or "PSM FDR:" (DDA)
    if not psm_fdr:
        psm_fdr = extract_value(lines, "PSM FDR:")
    peptide_fdr = extract_value(lines, "Peptide FDR:")
    params.ident_fdr_peptide = peptide_fdr
    params.ident_fdr_psm = psm_fdr
    # peaks uses  Proteins -10LgP >= 15.0  instead of FDR
    protein_fdr = extract_value(lines, "Protein Group FDR:")
    params.ident_fdr_protein = protein_fdr
    params.enable_match_between_runs = True if extract_value(lines, "Match Between Run:") == "Yes" else False
    params.precursor_mass_tolerance = extract_mass_tolerance(lines, "Precursor Mass Error Tolerance:")
    params.fragment_mass_tolerance = extract_mass_tolerance(lines, "Fragment Mass Error Tolerance:")
    params.enzyme = extract_value(lines, "Enzyme:")
    params.allowed_miscleavages = int(extract_value(lines, "Max Missed Cleavage:"))
    try:
        peptide_length_range = extract_value(lines, "Peptide Length between:").split(",")
    except AttributeError:
        peptide_length_range = extract_value(lines, "Peptide Length Range:").split(" - ")
    params.max_peptide_length = int(peptide_length_range[1])
    params.min_peptide_length = int(peptide_length_range[0])
    fixed = get_items_between(lines, "Fixed Modifications:", "Variable Modifications:", only_last=True)
    params.fixed_mods = " ,".join(fixed)
    varmods = get_items_between(lines, "Variable Modifications:", "Database:", only_last=True)
    params.variable_mods = " ,".join(varmods)
    params.max_mods = int(extract_value(lines, "Max Variable PTM per Peptide:"))
    try:
        precursor_charge_between = extract_value(lines, "Precursor Charge between:").split(",")
    except AttributeError:
        precursor_charge_between = (
            extract_value(lines, "Charge between:").replace("[", "").replace("]", "").split(" - ")
        )
    params.min_precursor_charge = int(precursor_charge_between[0])
    params.max_precursor_charge = int(precursor_charge_between[1])

    params.scan_window = None

    params.quantification_method = extract_value(
        lines, "LFQ Method:"
    )  # "Quantity MS Level:" or "Protein LFQ Method:" or "Quantity Type:"
    params.protein_inference = None
    params.predictors_library = None
    params.abundance_normalization_ions = extract_value(lines, "Normalization Method:")
    return params


if __name__ == "__main__":
    """
    Reads PEAKS settings files, extracts parameters, and writes them to CSV files.
    """
    fnames = [
        "../../../test/params/PEAKS_parameters.txt",
        "../../../test/params/PEAKS_parameters_DDA.txt",
        "../../../test/params/PEAKS_parameters_DIA.txt",
        "../../../test/params/PEAKS_parameters_DDA_new.txt",
        "../../../test/params/PEAKS_diaPASEF.txt",
    ]

    for file in fnames:
        # Extract parameters from the settings file
        parameters = read_peaks_settings(file)

        # Convert parameters to pandas Series and save to CSV
        actual = pd.Series(parameters.__dict__)
        actual.to_csv(Path(file).with_suffix(".csv"))

        # Optionally, print the parameters to the console
        print(parameters)
