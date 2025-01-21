import re
from pathlib import Path
from typing import List, Optional
import yaml

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def clean_text(text: str) -> str:
    """
    Clean the input text by removing leading and trailing spaces, colons, commas, or tabs.

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    text = re.sub(r"^[\s:,\t]+|[\s:,\t]+$", "", text)
    return text


def extract_value(lines: List[str], search_term: str) -> Optional[str]:
    """
    Extract the value associated with a search term from a list of lines.

    Args:
        lines (List[str]): The list of lines to search through.
        search_term (str): The term to search for in the lines.

    Returns:
        Optional[str]: The extracted value, or None if the search term is not found.
    """
    matching_line = next((line for line in lines if search_term in line), None)
    # Step 2: If a matching line is found, extract and clean the value
    if matching_line:
        # Extract the part after the search term
        raw_value = matching_line.split(search_term, 1)[1]
        # Clean the extracted value
        return clean_text(raw_value)

    # Step 3: Return None if no matching line is found
    return None
    # return next((clean_text(line.split(search_term)[1]) for line in lines if search_term in line), None)


def extract_mass_tolerance(lines: List[str], search_term: str) -> Optional[str]:
    """
    Extract the mass tolerance value associated with a search term, with special handling for "System Default".

    Args:
        lines (List[str]): The list of lines to search through.
        search_term (str): The term to search for in the lines.

    Returns:
        Optional[str]: The extracted mass tolerance value, or None if the search term is not found.
    """
    value = next((clean_text(line.split(search_term)[1]) for line in lines if search_term in line), None)
    value = "40 ppm" if value == "System Default" else value
    return value


def extract_value_regex(lines: List[str], search_term: str) -> Optional[str]:
    """
    Extract the value associated with a search term using regular expressions.

    Args:
        lines (List[str]): The list of lines to search through.
        search_term (str): The regular expression to search for in the lines.

    Returns:
        Optional[str]: The extracted value, or None if the search term is not found.
    """
    return next((clean_text(re.split(search_term, line)[1]) for line in lines if re.search(search_term, line)), None)


def get_items_between(lines: list, start: str, end: str) -> list:
    """
    Finds all lines starting with '-' that appear
    between 'Fixed Modifications:' and 'Variable Modifications:'.
    Returns them as a list of strings, without the leading dash.
    """

    capturing = False
    items = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(start):
            capturing = True
            continue

        if stripped.startswith(end):
            capturing = False
            break

        if capturing and stripped.startswith("- "):
            # Remove the dash and leading space
            item = stripped[2:].strip()
            items.append(item)

    return items


def read_peaks_settings(file_path: str) -> ProteoBenchParameters:
    """
    Read a Spectronaut settings file, extract parameters, and return them as a `ProteoBenchParameters` object.

    Args:
        file_path (str): The path to the Spectronaut settings file.

    Returns:
        ProteoBenchParameters: The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    # Try to read the file contents

    try:
        # Attempt to open and read the file
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise IOError(f"Failed to open or read the file at {file_path}. Error: {e}")

    # Remove any trailing newline characters from each line
    lines = [line.strip() for line in lines]

    params = ProteoBenchParameters()

    params.software_name = "Peaks"
    params.software_version = None
    params.search_engine = "Peaks"
    params.search_engine_version = params.software_version

    params.ident_fdr_psm = None
    fdr = extract_value(lines, "Peptide FDR:")
    fdr = float(fdr[:-1]) / 100  # Convert percentage to a decimal
    params.ident_fdr_peptide = fdr
    # peaks uses  Proteins -10LgP >= 15.0  instead of FDR
    params.ident_fdr_protein = None
    params.enable_match_between_runs = extract_value(lines, "Match Between Run:")
    params.precursor_mass_tolerance = extract_mass_tolerance(lines, "Precursor Mass Error Tolerance:")
    params.fragment_mass_tolerance = extract_mass_tolerance(lines, "Fragment Mass Error Tolerance:")
    params.enzyme = extract_value(lines, "Enzyme:")
    params.allowed_miscleavages = int(extract_value(lines, "Max Missed Cleavage:"))

    peptide_length_range = extract_value(lines, "Peptide Length between:").split(",")
    params.max_peptide_length = int(peptide_length_range[1])
    params.min_peptide_length = int(peptide_length_range[0])
    fixed = get_items_between(lines, "Fixed Modifications:", "Variable Modifications:")
    params.fixed_mods = " ,".join(fixed)
    varmods = get_items_between(lines, "Variable Modifications:", "Database:")
    params.variable_mods = " ,".join(varmods)
    params.max_mods = int(extract_value(lines, "Max Variable PTM per Peptide:"))

    precursor_charge_between = extract_value(lines, "Precursor Charge between:").split(",")
    params.min_precursor_charge = int(precursor_charge_between[0])
    params.max_precursor_charge = int(precursor_charge_between[1])

    params.scan_window = None

    params.quantification_method = extract_value(
        lines, "LFQ Method:"
    )  # "Quantity MS Level:" or "Protein LFQ Method:" or "Quantity Type:"
    params.second_pass = None
    params.protein_inference = None
    params.predictors_library = None
    params.abundance_normalization_ions = extract_value(lines, "Normalization Method:")
    return params


if __name__ == "__main__":
    """
    Reads Spectronaut settings files, extracts parameters, and writes them to CSV files.
    """
    fnames = ["../../../test/params/PEAKS_parameters.txt"]

    for file in fnames:
        # Extract parameters from the settings file
        parameters = read_peaks_settings(file)

        # Convert parameters to pandas Series and save to CSV
        actual = pd.Series(parameters.__dict__)
        actual.to_csv(Path(file).with_suffix(".csv"))

        # Optionally, print the parameters to the console
        print(parameters)
