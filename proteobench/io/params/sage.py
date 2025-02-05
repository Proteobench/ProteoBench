"""
Sage parameter extraction.
"""

import json
import pathlib
from typing import Union

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

default_params = {  # Default parameters for Sage
    "allowed_miscleavages": 1,
    "min_peptide_length": 5,
    "max_peptide_length": 50,
    "max_mods": 2,
    "min_precursor_charge": 2,
    "max_precursor_charge": 4,
}


def extract_params(fname: Union[str, pathlib.Path]) -> ProteoBenchParameters:
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
    params = ProteoBenchParameters()

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
            params.enyzme = "Trypsin/P"
    params.fixed_mods = data["database"]["static_mods"]
    params.variable_mods = data["database"]["variable_mods"]

    params.precursor_mass_tolerance = _format_mass_tolerance(data, "precursor_tol")
    params.fragment_mass_tolerance = _format_mass_tolerance(data, "fragment_tol")

    params.allowed_miscleavages = data["database"]["enzyme"]["missed_cleavages"]
    params.min_peptide_length = data["database"]["enzyme"]["min_len"]
    params.max_peptide_length = data["database"]["enzyme"]["max_len"]
    params.max_mods = data["database"]["max_variable_mods"]
    params.min_precursor_charge = data["precursor_charge"][0]
    params.max_precursor_charge = data["precursor_charge"][1]
    params.enable_match_between_runs = True

    for param in [
        "allowed_miscleavages",
        "min_peptide_length",
        "max_peptide_length",
        "max_mods",
        "min_precursor_charge",
        "max_precursor_charge",
    ]:
        if params.__dict__[param] is None:
            # add default values for parameters not defined by user
            params.__dict__[param] = default_params[param]

        else:
            # cast parsed param to int
            params.__dict__[param] = int(params.__dict__[param])

    return params


def _format_mass_tolerance(data, tol_type):
    try:
        tolerance = data[tol_type]["ppm"]
        tolerance = [f"{val} ppm" for val in tolerance]
    except KeyError:
        tolerance = data[tol_type]["da"]
        tolerance = [f"{val} Da" for val in tolerance]
    return "[" + ", ".join(tolerance) + "]"


if __name__ == "__main__":
    """
    Extract parameters from Sage JSON files and save them as CSV.
    """
    from pathlib import Path
    from pprint import pprint

    file = Path("../../../test/params/sage_results.json")

    # Extract parameters from the file
    params = extract_params(file)

    # Convert the extracted parameters to a dictionary and then to a pandas Series
    data_dict = params.__dict__
    pprint(params.__dict__)
    series = pd.Series(data_dict)

    # Write the Series to a CSV file
    series.to_csv(file.with_suffix(".csv"))
