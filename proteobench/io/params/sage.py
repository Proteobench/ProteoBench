"""
Sage parameter extraction.
"""

import json
import os
import pathlib
from typing import Union

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

MASS_TO_MOD_MAPPING = {
    57.021464: "Carbamidomethyl",
    15.9949: "Oxidation",
    42.0106: "Acetyl",
}
MASS_TOLERANCE = 0.001

# Sage uses "[" for N-terminal and "]" for C-terminal modifications
RESIDUE_MAP = {"[": "Protein N-term", "]": "Protein C-term", "^": "N-term", "$": "C-term"}


def _lookup_mod_name(mass: float) -> str:
    """Look up a modification name by mass shift within tolerance."""
    for ref_mass, name in MASS_TO_MOD_MAPPING.items():
        if abs(mass - ref_mass) < MASS_TOLERANCE:
            return name
    return str(mass)


def _parse_static_mods(mods: dict) -> str:
    """Parse Sage static_mods dict into ProForma-like format."""
    if not mods:
        return ""
    results = []
    for residue, mass in mods.items():
        mod_name = _lookup_mod_name(mass)
        res = RESIDUE_MAP.get(residue, residue)
        results.append(f"{res}[{mod_name}]")
    return ", ".join(results)


def _parse_variable_mods(mods: dict) -> str:
    """Parse Sage variable_mods dict into ProForma-like format."""
    if not mods:
        return ""
    results = []
    for residue, masses in mods.items():
        res = RESIDUE_MAP.get(residue, residue)
        for mass in masses:
            mod_name = _lookup_mod_name(mass)
            results.append(f"{res}[{mod_name}]")
    return ", ".join(results)


def _format_tolerance_range(tolerance_data: dict) -> str:
    """Format tolerance range from Sage JSON, supporting legacy and newer key casings."""
    if not isinstance(tolerance_data, dict):
        raise ValueError(f"Tolerance entry should be a dictionary, got: {type(tolerance_data)}")

    unit_lookup = {
        "ppm": "ppm",
        "da": "Da",
    }

    for key, values in tolerance_data.items():
        normalized_key = str(key).lower()
        if normalized_key in unit_lookup:
            unit = unit_lookup[normalized_key]
            return "[" + ", ".join(f"{val} {unit}" for val in values) + "]"

    raise KeyError(f"Unsupported tolerance unit(s): {list(tolerance_data.keys())}")


def extract_params(
    fname: Union[str, pathlib.Path],
    json_file=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DDA_ion.json"),
) -> ProteoBenchParameters:
    """
    Parse Sage quantification tool JSON parameter file and extract relevant parameters.

    Parameters
    ----------
    fname : str or pathlib.Path
        The path to the Sage JSON parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a `ProteoBenchParameters` object.
    """
    params = ProteoBenchParameters(json_file=json_file)

    try:
        # If the input is a file-like object (e.g., StringIO), decode it
        file_contents = fname.getvalue().decode("utf-8")
        data = json.loads(file_contents)
    except AttributeError:
        # Otherwise, treat it as a file path
        with open(fname, "r") as file_contents:
            data = json.load(file_contents)

    # Extract parameters from the JSON data
    params.software_name = "Sage"
    params.software_version = data["version"]
    params.search_engine = "Sage"
    params.search_engine_version = data["version"]
    params.enzyme = data["database"]["enzyme"]["cleave_at"]
    if params.enzyme == "KR" or params.enzyme == "RK":
        try:
            if data["database"]["enzyme"]["restrict"] == "P":
                params.enzyme = "Trypsin"
        except KeyError:
            params.enzyme = "Trypsin/P"

    params.allowed_miscleavages = data["database"]["enzyme"]["missed_cleavages"]

    if data["database"]["enzyme"]["semi_enzymatic"] is None:
        params.semi_enzymatic = False
    elif data["database"]["enzyme"]["semi_enzymatic"] is True:
        params.semi_enzymatic = True
    elif data["database"]["enzyme"]["semi_enzymatic"] is False:
        params.semi_enzymatic = False
    else:
        raise ValueError(f"Unknown value for semi_enzymatic: {data['database']['enzyme']['semi_enzymatic']}")

    params.fixed_mods = _parse_static_mods(data["database"]["static_mods"])
    params.variable_mods = _parse_variable_mods(data["database"]["variable_mods"])

    params.precursor_mass_tolerance = _format_tolerance_range(data["precursor_tol"])
    params.fragment_mass_tolerance = _format_tolerance_range(data["fragment_tol"])

    params.min_peptide_length = int(data["database"]["enzyme"]["min_len"])
    max_len = data["database"]["enzyme"]["max_len"]
    params.max_peptide_length = int(max_len) if max_len is not None else None
    params.max_mods = int(data["database"]["max_variable_mods"])
    params.min_precursor_charge = int(data["precursor_charge"][0])
    params.max_precursor_charge = int(data["precursor_charge"][1])
    params.enable_match_between_runs = True

    params.fill_none()
    return params


if __name__ == "__main__":
    """
    Extract parameters from Sage JSON files and save them as CSV.
    """
    from pathlib import Path
    from pprint import pprint

    files = [
        Path("../../../test/params/sage_results.json"),
        Path("../../../test/params/sage_parameterfile.json"),
    ]

    for file in files:
        # Extract parameters from the file
        print(f"Extracting parameters from {file}")
        params = extract_params(file)

        # Convert the extracted parameters to a dictionary and then to a pandas Series
        data_dict = params.__dict__
        pprint(params.__dict__)
        series = pd.Series(data_dict)

        # Write the Series to a CSV file
        series.to_csv(file.with_suffix(".csv"))
