"""
Proline Studio is a quantification tool. The search engine is often Mascot.
The parameters are provided per raw file in separate sheets of an Excel file.

Relevant information in sheets:
- "Search settings and infos",
- "Import and filters"
- "Quant config"
"""

import re
from pathlib import Path
from typing import List

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

# Column names for different sheets in the Excel file
use_columns = {
    "Search settings and infos": [
        "software_name",
        "software_version",
        "enzymes",
        "max_missed_cleavages",
        "fixed_ptms",
        "variable_ptms",
        "peptide_charge_states",
        "peptide_mass_error_tolerance",
        "fragment_mass_error_tolerance",
    ],
    "Import and filters": [
        "psm_filter_expected_fdr",
        "psm_filter_2",
    ],
    "Quant config": [],
}

# Regular expressions for finding minimum peptide length and charge states
PATTERN_MIN_PEP_LENGTH = r"\[threshold_value=([0-9].*)\]"
PATTERN_CHARGE = r"[\d+]+"


def find_charge(string: str) -> List[int]:
    """
    Extract charge states from a string using a regular expression.

    Parameters
    ----------
    string : str
        The string containing charge states.

    Returns
    -------
    List[int]
        A list of charge states as integers.
    """
    charges = re.findall(PATTERN_CHARGE, string)
    charges = [int(c[:-1]) for c in charges]  # Remove any trailing non-digit characters
    return charges


def find_min_pep_length(string: str) -> int:
    """
    Extract the minimum peptide length from a string using a regular expression.

    Parameters
    ----------
    string : str
        The string containing the minimum peptide length.

    Returns
    -------
    int
        The minimum peptide length as an integer.
    """
    min_length = re.findall(PATTERN_MIN_PEP_LENGTH, string)[0]
    return int(min_length)


def extract_params(fname: str) -> ProteoBenchParameters:
    """
    Parse Proline Studio parameter file (Excel) and extract relevant parameters.

    Parameters
    ----------
    fname : str
        The path to the Proline Studio Excel parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    params = ProteoBenchParameters()
    excel = pd.ExcelFile(fname)

    # Parse the "Search settings and infos" sheet
    sheet_name = "Search settings and infos"
    cols = use_columns[sheet_name]
    sheet = excel.parse(sheet_name, dtype="object", index_col=0).T
    idx = sheet["quant_channel_name"].to_list()
    stats = sheet.describe()

    # Validate unique entries in the selected columns
    assert all(stats.loc["unique", cols] == 1), "Not all columns are unique"

    # Filter and reset index
    sheet = sheet[cols].drop_duplicates().reset_index(drop=True)

    # Extract relevant parameters from the sheet
    params.software_name = "ProlineStudio"
    params.search_engine = sheet.loc[0, "software_name"]
    params.search_engine_version = sheet.loc[0, "software_version"]
    params.enzyme = sheet.loc[0, "enzymes"]
    params.allowed_miscleavages = sheet.loc[0, "max_missed_cleavages"]
    params.fixed_mods = sheet.loc[0, "fixed_ptms"]
    params.variable_mods = sheet.loc[0, "variable_ptms"]
    _precursor_mass_tolerance = sheet.loc[0, "peptide_mass_error_tolerance"]
    params.precursor_mass_tolerance = f"[-{_precursor_mass_tolerance}, {_precursor_mass_tolerance}]"
    _fragment_mass_tolerance = sheet.loc[0, "fragment_mass_error_tolerance"]
    params.fragment_mass_tolerance = f"[-{_fragment_mass_tolerance}, {_fragment_mass_tolerance}]"

    # Extract charge states and set min/max precursor charge
    charges = find_charge(sheet.loc[0, "peptide_charge_states"])
    params.min_precursor_charge = min(charges)
    params.max_precursor_charge = max(charges)

    # Parse the "Import and filters" sheet
    sheet_name = "Import and filters"
    cols = use_columns[sheet_name]
    sheet = excel.parse(sheet_name, dtype="object", index_col=0).T.loc[idx, cols]
    stats = sheet.describe()
    assert all(stats.loc["unique", cols] == 1), "Not all columns are unique"
    sheet = sheet[cols].drop_duplicates().reset_index(drop=True)

    # Extract FDR and peptide length information
    try:
        params.ident_fdr_psm = int(sheet.loc[0, "psm_filter_expected_fdr"]) / 100
    except ValueError:
        params.ident_fdr_psm = sheet.loc[0, "psm_filter_expected_fdr"]
    params.min_peptide_length = find_min_pep_length(sheet.loc[0, "psm_filter_2"])

    # Parse the "Quant config" sheet for match between runs (MBR) information
    sheet_name = "Quant config"
    sheet = excel.parse(sheet_name, dtype="object", index_col=0)
    enable_match_between_runs = sheet.index.str.contains("cross assignment").any()
    params.enable_match_between_runs = bool(enable_match_between_runs)

    # Try to extract software version from "Dataset statistics and infos" sheet
    try:
        sheet_name = "Dataset statistics and infos"
        sheet = excel.parse(sheet_name, dtype="object", index_col=0, header=None).squeeze()
        params.software_version = sheet.loc["version"]
    except KeyError:
        pass
    except ValueError:
        pass

    params.fill_none()

    return params


if __name__ == "__main__":
    """
    Extract parameters from Proline Studio parameter files and write them to CSV files.
    """
    files = [
        "../../../test/params/Proline_example_w_Mascot_wo_proteinSets.xlsx",
        "../../../test/params/Proline_example_2.xlsx",
        "../../../test/params/ProlineStudio_withMBR.xlsx",
        "../../../test/params/ProlineStudio_241024.xlsx",
    ]

    for file in files:
        file = Path(file)

        # Extract parameters from the file
        params = extract_params(file)

        # Convert the extracted parameters to a dictionary and then to a pandas Series
        data_dict = params.__dict__
        series = pd.Series(data_dict)

        # Write the Series to a CSV file
        series.to_csv(file.with_suffix(".csv"))
