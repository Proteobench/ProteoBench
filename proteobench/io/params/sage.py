"""
Sage parameter extraction.
"""

import json
import pathlib
from typing import Union

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


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

    params.allowed_miscleavages = data["database"]["enzyme"]["missed_cleavages"]
    params.fixed_mods = data["database"]["static_mods"]
    params.variable_mods = data["database"]["variable_mods"]

    try:
        _precursor_mass_tolerance = data["precursor_tol"]["ppm"]
        # add unit after each value in list
        _precursor_mass_tolerance = [str(val) + " ppm" for val in _precursor_mass_tolerance]
        params.precursor_mass_tolerance = "[" + ", ".join(_precursor_mass_tolerance) + "]"
    except KeyError:
        _precursor_mass_tolerance = data["precursor_tol"]["Da"]
        # add unit after each value in list
        _precursor_mass_tolerance = [str(val) + " Da" for val in params.precursor_mass_tolerance]
        params.precursor_mass_tolerance = "[" + ", ".join(_precursor_mass_tolerance) + "]"

    _fragment_mass_tolerance = data["fragment_tol"]["ppm"]
    # add unit after each value in list
    _fragment_mass_tolerance = [str(val) + " ppm" for val in _fragment_mass_tolerance]
    params.fragment_mass_tolerance = "[" + ", ".join(_fragment_mass_tolerance) + "]"

    params.min_peptide_length = int(data["database"]["enzyme"]["min_len"])
    params.max_peptide_length = int(data["database"]["enzyme"]["max_len"])
    params.max_mods = int(data["database"]["max_variable_mods"])
    params.min_precursor_charge = int(data["precursor_charge"][0])
    params.max_precursor_charge = int(data["precursor_charge"][1])
    params.enable_match_between_runs = True

    return params


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
