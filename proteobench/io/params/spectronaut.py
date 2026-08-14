"""
Spectronaut parameter parsing.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from proteobench.io.params import ProteoBenchParameters
from proteobench.io.params.maxquant import _homogenize_mods

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


def extract_mass_tolerance_v2(lines: List[str]) -> Optional[Tuple[str, str]]:
    """
    Extract mass tolerances from the 'Main Search Tolerances' section used by newer Spectronaut
    versions (schema >= 21), which report MS1/MS2 strategy and tolerance directly instead of
    breaking them down per vendor/system.
    """
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("Main Search Tolerances:"))
    except StopIteration:
        return None

    ms1_strategy = ms2_strategy = None
    ms1_tol = ms2_tol = None
    current = None

    for line in lines[start + 1 :]:
        if line.startswith("MS1 Mass Tolerance Strategy:"):
            ms1_strategy = clean_text(line.split(":", 1)[1])
            current = "MS1"
        elif line.startswith("MS2 Mass Tolerance Strategy:"):
            ms2_strategy = clean_text(line.split(":", 1)[1])
            current = "MS2"
        elif line.startswith("Tolerance (Th):") or line.startswith("Tolerance (ppm):"):
            unit = "Th" if line.startswith("Tolerance (Th):") else "ppm"
            value = clean_text(line.split(":", 1)[1])
            if current == "MS1":
                ms1_tol = (value, unit)
            elif current == "MS2":
                ms2_tol = (value, unit)
        else:
            continue

        if ms1_strategy and ms2_strategy and (ms1_strategy != "Dynamic" and ms2_strategy != "Dynamic"):
            if ms1_tol and ms2_tol:
                break

    if ms1_strategy == "Dynamic" or ms2_strategy == "Dynamic":
        return "Dynamic", "Dynamic"

    if ms1_tol and ms2_tol:
        ms1_val, ms1_unit = ms1_tol
        ms2_val, ms2_unit = ms2_tol
        return (
            f"[-{ms1_val} {ms1_unit}, {ms1_val} {ms1_unit}]",
            f"[-{ms2_val} {ms2_unit}, {ms2_val} {ms2_unit}]",
        )

    return None


def extract_fragment_mz_range(lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract the fragment ion m/z filter range (Min/Max) from the 'Fragment Ions' result-filter
    block, if the filter is enabled ('m/z :' is True).
    """
    try:
        idx = next(i for i, line in enumerate(lines) if line.startswith("m/z :"))
    except StopIteration:
        return None, None

    if clean_text(lines[idx].split(":", 1)[1]) != "True":
        return None, None

    min_mz = max_mz = None
    for line in lines[idx + 1 : idx + 3]:
        if line.startswith("Max:"):
            max_mz = clean_text(line.split(":", 1)[1])
        elif line.startswith("Min:"):
            min_mz = clean_text(line.split(":", 1)[1])

    return min_mz, max_mz


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


def read_spectronaut_settings(
    file_path: str,
    system="Thermo Orbitrap",
    json_file=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DIA_ion.json"),
) -> ProteoBenchParameters:
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

    params = ProteoBenchParameters(filename=json_file)
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
    tolerances = extract_mass_tolerance(lines, system=system) or extract_mass_tolerance_v2(lines)
    if tolerances is None:
        raise ValueError("Could not determine mass tolerances from the Spectronaut settings file.")
    params.precursor_mass_tolerance, params.fragment_mass_tolerance = tolerances
    params.enzyme = extract_value(lines, "Enzymes / Cleavage Rules:")
    params.semi_enzymatic = extract_value(lines, "Digest Type:") != "Specific"
    params.allowed_miscleavages = int(extract_value(lines, "Missed Cleavages:"))
    params.max_peptide_length = int(extract_value(lines, "Max Peptide Length:"))
    params.min_peptide_length = int(extract_value(lines, "Min Peptide Length:"))
    params.fixed_mods = _homogenize_mods(extract_value(lines, "Fixed Modifications:"))
    params.variable_mods = _homogenize_mods(extract_value_regex(lines, "^Variable Modifications:"))
    params.max_mods = int(extract_value(lines, "Max Variable Modifications:"))
    if extract_value(lines, "Peptide Charge:") == "True":
        params.min_precursor_charge = int(extract_value(lines, "Min Charge:"))
        params.max_precursor_charge = int(extract_value(lines, "Max Charge:"))
    else:
        params.min_precursor_charge = None
        params.max_precursor_charge = None

    _min_fragment_mz, _max_fragment_mz = extract_fragment_mz_range(lines)
    params.min_fragment_mz = int(_min_fragment_mz) if _min_fragment_mz is not None else None
    params.max_fragment_mz = int(_max_fragment_mz) if _max_fragment_mz is not None else None
    params.max_precursor_mz = None  # Spectronaut does not provide this information
    params.min_precursor_mz = None  # Spectronaut does not provide this information

    params.scan_window = extract_value(lines, "XIC IM Extraction Window:")
    params.quantification_method = extract_value(
        lines, "Quantity MS Level:"
    )  # "Quantity MS Level:" or "Protein LFQ Method:" or "Quantity Type:"
    params.protein_inference = extract_value(lines, "Inference Algorithm:")  # or Protein Inference Workflow:
    params.predictors_library = None
    params.abundance_normalization_ions = extract_value(lines, "Cross-Run Normalization:")
    params.fill_none()
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
