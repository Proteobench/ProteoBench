"""
Spectronaut parameter parsing.
"""

import re
from pathlib import Path
from typing import List, Optional

import pandas as pd

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
    return next((clean_text(line.split(search_term)[1]) for line in lines if search_term in line), None)


def extract_mass_tolerance(lines: List[str], search_term: str, mass_analyzer="Orbitrap") -> Optional[str]:
    """
    Extract the mass tolerance value associated with a search term, with special handling for "System Default".

    Parameters
    ----------
    lines : List[str]
        The list of lines to search through.
    search_term : str
        The term to search for in the lines.
    mass_analyzer : str, optional
        The type of mass analyzer, by default "Orbitrap".

    Returns
    -------
    Optional[str]
        The extracted mass tolerance value, or None if the search term is not found.
    """
    value = next((clean_text(line.split(search_term)[1]) for line in lines if search_term in line), None)
    if value == "System Default":
        if mass_analyzer in (["Orbitrap", "TOF", "BrukerTOF"]):
            value = "40 ppm"
        elif mass_analyzer == "WatersTOF":
            value = "80 ppm"
        elif mass_analyzer == "IonTrap":
            value = "0.5 th"
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


def read_spectronaut_settings(file_path: str) -> ProteoBenchParameters:
    """
    Read a Spectronaut settings file, extract parameters, and return them as a `ProteoBenchParameters` object.

    Parameters
    ----------
    file_path : str
        The path to the Spectronaut settings file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    # Try to read the file contents
    if hasattr(file_path, "read"):
        # Assume it behaves like a file object
        lines = file_path.read().decode("utf-8").splitlines()
    else:
        try:
            # Attempt to open and read the file
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise IOError(f"Failed to open or read the file at {file_path}. Error: {e}")

    # Remove any trailing newline characters from each line
    lines = [line.strip() for line in lines]

    params = ProteoBenchParameters()
    params.software_name = "Spectronaut"
    params.software_version = lines[0].split()[1]
    params.search_engine = "Spectronaut"
    params.search_engine_version = params.software_version

    # Clean up the lines and extract the relevant parameters
    lines = [re.sub(r"^[\s│├─└]*", "", line).strip() for line in lines]

    params.ident_fdr_psm = float(extract_value(lines, "Precursor Qvalue Cutoff:"))
    params.ident_fdr_peptide = None
    params.ident_fdr_protein = float(extract_value(lines, "Protein Qvalue Cutoff (Experiment):"))
    params.enable_match_between_runs = False
    _precursor_mass_tolerance = extract_mass_tolerance(lines, "MS1 Mass Tolerance Strategy:")
    params.precursor_mass_tolerance = f"[-{_precursor_mass_tolerance}, {_precursor_mass_tolerance}]"
    _fragment_mass_tolerance = extract_mass_tolerance(lines, "MS2 Mass Tolerance Strategy:")
    params.fragment_mass_tolerance = f"[-{_fragment_mass_tolerance}, {_fragment_mass_tolerance}]"
    params.enzyme = extract_value(lines, "Enzymes / Cleavage Rules:")
    params.allowed_miscleavages = int(extract_value(lines, "Missed Cleavages:"))
    params.max_peptide_length = int(extract_value(lines, "Max Peptide Length:"))
    params.min_peptide_length = int(extract_value(lines, "Min Peptide Length:"))
    params.fixed_mods = extract_value(lines, "Fixed Modifications:")
    params.variable_mods = extract_value_regex(lines, "^Variable Modifications:")
    params.max_mods = int(extract_value(lines, "Max Variable Modifications:"))
    _min_precursor_charge = extract_value(lines, "Peptide Charge:")
    if _min_precursor_charge == "False":
        params.min_precursor_charge = None
    else:
        params.min_precursor_charge = int(_min_precursor_charge)

    _max_precursor_charge = extract_value(lines, "Peptide Charge:")
    if _max_precursor_charge == "False":
        params.max_precursor_charge = None
    else:
        params.max_precursor_charge = int(_max_precursor_charge)

    params.scan_window = extract_value(lines, "XIC IM Extraction Window:")
    params.quantification_method = extract_value(
        lines, "Quantity MS Level:"
    )  # "Quantity MS Level:" or "Protein LFQ Method:" or "Quantity Type:"
    params.second_pass = extract_value(lines, "directDIA Workflow:")
    params.protein_inference = extract_value(lines, "Inference Algorithm:")  # or Protein Inference Workflow:
    params.predictors_library = extract_value(lines, "Hybrid (DDA + DIA) Library").replace(":", "").strip()
    params.abundance_normalization_ions = extract_value(lines, "Cross-Run Normalization:")
    return params


if __name__ == "__main__":
    """
    Reads Spectronaut settings files, extracts parameters, and writes them to CSV files.
    """
    fnames = [
        "../../../test/params/spectronaut_Experiment1_ExperimentSetupOverview_BGS_Factory_Settings.txt",
        "../../../test/params/Spectronaut_dynamic.txt",
    ]

    for file in fnames:
        # Extract parameters from the settings file
        parameters = read_spectronaut_settings(file)

        # Convert parameters to pandas Series and save to CSV
        actual = pd.Series(parameters.__dict__)
        actual.to_csv(Path(file).with_suffix(".csv"))

        # Optionally, print the parameters to the console
        print(parameters)
