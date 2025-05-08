"""
Spectronaut parameter parsing.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

VENDOR_SYSTEM_MAP = {
    "Thermo": "Thermo Orbitrap",
    "Bruker": "TOF",
}
ms1_tolerance_static = re.compile(r"MS1 Tolerance \(Th\):\s*(\d*)")
ms2_tolerance_static = re.compile(r"MS2 Tolerance \(Th\):\s*(\d*)")
ms1_tolerance_relative = re.compile(r"MS1 Tolerance \(ppm\):\s*(\d*)")
ms2_tolerance_relative = re.compile(r"MS2 Tolerance \(ppm\):\s*(\d*)")
main_search_regex = re.compile(r"Main Search:\s*(.*)")


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


def extract_calibration_method(line: str) -> Optional[str]:
    """
    Extract the calibration method from the 'Main Search' line.
    """
    match = main_search_regex.search(line)
    if match:
        calibration_method = match.group(1).strip()
        return calibration_method
    return None


def extract_tolerances(line: str, calibration_method: str, MS1_tol: Optional[str], MS2_tol: Optional[str]) -> tuple:
    """
    Extract MS1 and MS2 tolerances based on the calibration method, without overwriting existing values.
    """

    # Only extract MS1 and MS2 tolerances if they haven't already been set
    if calibration_method == "Static":
        MS1_tol, MS2_tol = extract_tolerances_with_regex(
            line, MS1_tol, MS2_tol, ms1_tolerance_static, ms2_tolerance_static
        )
    elif calibration_method == "Relative":
        MS1_tol, MS2_tol = extract_tolerances_with_regex(
            line, MS1_tol, MS2_tol, ms1_tolerance_relative, ms2_tolerance_relative
        )

    return MS1_tol, MS2_tol


def extract_tolerances_with_regex(
    line: str,
    MS1_tol: Optional[str],
    MS2_tol: Optional[str],
    ms1_tolerance_regex: re.Pattern,
    ms2_tolerance_regex: re.Pattern,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract MS1 and MS2 tolerances from the line using the provided regular expressions,
    without overwriting existing values.

    Args:
        line: The line from which tolerances should be extracted.
        MS1_tol: Existing MS1 tolerance (retained if already set).
        MS2_tol: Existing MS2 tolerance (retained if already set).
        ms1_tolerance_regex: Regex pattern for MS1 tolerance.
        ms2_tolerance_regex: Regex pattern for MS2 tolerance.

    Returns:
        A tuple (MS1_tol, MS2_tol) with updated or retained values.
    """

    def extract_if_none(current: Optional[str], pattern: re.Pattern) -> Optional[str]:
        if current is None:
            match = pattern.search(line)
            return match.group(1) if match else None
        return current

    MS1_tol = extract_if_none(MS1_tol, ms1_tolerance_regex)
    MS2_tol = extract_if_none(MS2_tol, ms2_tolerance_regex)

    return MS1_tol, MS2_tol


def extract_mass_tolerance(lines: List[str], system="Thermo Orbitrap") -> Optional[str]:
    """
    Extract mass tolerances from the 'Main Search' section based on the system and calibration method.
    """
    tolerance_section = False
    system_section = False
    calibration_method = None
    MS1_tol = MS2_tol = None

    for line in lines:
        if line.startswith("Pulsar Search\\Tolerances"):
            tolerance_section = True
        elif tolerance_section:
            if line.startswith(system):
                system_section = True
            elif system_section:
                # Extract the calibration method from the 'Main Search' line
                if "Main Search:" in line and not calibration_method:
                    calibration_method = extract_calibration_method(line)

                if calibration_method:
                    if calibration_method == "Dynamic":
                        return "Dynamic", "Dynamic"
                    else:
                        unit = "Th" if calibration_method == "Static" else "ppm"
                        # Extract the tolerances for the identified calibration method
                        MS1_tol, MS2_tol = extract_tolerances(line, calibration_method, MS1_tol, MS2_tol)
                        if MS1_tol is not None and MS2_tol is not None:
                            return (
                                f"[-{MS1_tol} {unit}, {MS1_tol} {unit}]",
                                f"[-{MS2_tol} {unit}, {MS2_tol} {unit}]",
                            )

    return None


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


def read_spectronaut_settings(file_path: str, system="Thermo Orbitrap") -> ProteoBenchParameters:
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

    system = extract_value(lines, "Vendor:")
    if system in VENDOR_SYSTEM_MAP:
        system = VENDOR_SYSTEM_MAP[system]
    else:
        raise ValueError(
            f"Unknown system: {system}. Supported systems are: {', '.join(VENDOR_SYSTEM_MAP.keys())}. Did you upload the correct settings file?"
        )

    params = ProteoBenchParameters()
    params.software_name = "Spectronaut"
    params.software_version = lines[0].split()[1]
    params.search_engine = "Spectronaut"
    params.search_engine_version = params.software_version

    # Clean up the lines and extract the relevant parameters
    lines = [re.sub(r"^[\s│├─└]*", "", line).strip() for line in lines]

    params.ident_fdr_psm = float(extract_value(lines, "Precursor Qvalue Cutoff:").replace(",", "."))
    params.ident_fdr_peptide = None
    params.ident_fdr_protein = float(extract_value(lines, "Protein Qvalue Cutoff (Experiment):").replace(",", "."))
    params.enable_match_between_runs = False  # https://x.com/OliverMBernhar1/status/1656220095553601537
    params.precursor_mass_tolerance, params.fragment_mass_tolerance = extract_mass_tolerance(lines, system=system)
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
    params.protein_inference = extract_value(lines, "Inference Algorithm:")  # or Protein Inference Workflow:
    params.predictors_library = None
    params.abundance_normalization_ions = extract_value(lines, "Cross-Run Normalization:")
    return params


if __name__ == "__main__":
    """
    Reads Spectronaut settings files, extracts parameters, and writes them to CSV files.
    """
    fnames = [
        "../../../test/params/spectronaut_Experiment1_ExperimentSetupOverview_BGS_Factory_Settings.txt",
        "../../../test/params/Spectronaut_dynamic.txt",
        "../../../test/params/Spectronaut_static.txt",
        "../../../test/params/Spectronaut_relative.txt",
    ]

    for file in fnames:
        # Extract parameters from the settings file
        parameters = read_spectronaut_settings(file)

        # Convert parameters to pandas Series and save to CSV
        actual = pd.Series(parameters.__dict__)
        actual.to_csv(Path(file).with_suffix(".csv"))

        # Optionally, print the parameters to the console
        print(parameters)
