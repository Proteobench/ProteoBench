"""MSAngel creates modular pipelines that allows several search engines to identify 
peptides, which are then quantified with Proline.
The parameters are provided in a .json file.
MSAngel allows for multiple search engines to be used in the same pipeline. So it 
requires a list of search engines and their respective parameters, which are then 
concatenated.

Relevant information in file:

"""

import json
import pathlib
from typing import Union

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def extract_search_engine(search_params: list) -> dict:
    """
    Extract search engine parameters from the JSON data.
    The parameter format depends on the search engine used, so this functino needs to be
    updated for each search engine. Currently, it is set up for:
    . Mascot
    """

    all_search_engines = []
    for each_search_params in search_params["operations"]:
        print("1")
        if "searchEnginesWithForms" in each_search_params:
            all_search_engines.append(each_search_params["searchEnginesWithForms"][0][0])

    return all_search_engines


def extract_params(fname: Union[str, pathlib.Path]) -> ProteoBenchParameters:
    """
    Parse MSAangel quantification tool JSON parameter file and extract relevant parameters.

    Args:
        fname (str or pathlib.Path): The path to the Sage JSON parameter file.

    Returns:
        ProteoBenchParameters: The extracted parameters as a `ProteoBenchParameters` object.
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
    params.software_name = "MSAngel"
    params.software_version = data["msAngelVersion"]

    ## Extract the search engine(s) parameters before concatenating them:
    all_search_engines = extract_search_engine(data)
    params.search_engines = all_search_engines.join(",")
    all_search_engines = []
    all_enzyme = []
    all_allowed_miscleavages = []
    all_fixed_mods = []
    all_variable_mods = []

    # TODO needs to have actual values
    all_search_params = {}

    for key, value in all_search_params.items():
        all_search_engines.append(value["format"])
        all_enzyme.append(value["enzyme"]["cleave_at"])
        all_allowed_miscleavages.append(value["enzyme"]["missed_cleavages"])
        all_fixed_mods.append(value["static_mods"])
        all_variable_mods.append(value["variable_mods"])

    # TODO need to have an actual value
    params.search_engine = ""
    params.search_engine_version = data["version"]
    params.enzyme = data["database"]["enzyme"]["cleave_at"]
    params.allowed_miscleavages = data["database"]["enzyme"]["missed_cleavages"]
    params.fixed_mods = data["database"]["static_mods"]
    params.variable_mods = data["database"]["variable_mods"]

    try:
        params.precursor_mass_tolerance = data["precursor_tol"]["ppm"]
    except KeyError:
        params.precursor_mass_tolerance = data["precursor_tol"]["Da"]

    params.fragment_mass_tolerance = data["fragment_tol"]["ppm"]
    params.min_peptide_length = data["database"]["enzyme"]["min_len"]
    params.max_peptide_length = data["database"]["enzyme"]["max_len"]
    params.max_mods = data["database"]["max_variable_mods"]
    params.min_precursor_charge = data["precursor_charge"][0]
    params.max_precursor_charge = data["precursor_charge"][1]
    params.enable_match_between_runs = True

    return params


if __name__ == "__main__":
    """
    Extract parameters from MSAngel JSON files and save them as CSV.
    """
    from pathlib import Path

    file = Path("../../../test/params/msangel_results.json")

    # Extract parameters from the file
    params = extract_params(file)

    # Convert the extracted parameters to a dictionary and then to a pandas Series
    data_dict = params.__dict__
    series = pd.Series(data_dict)

    # Write the Series to a CSV file
    series.to_csv(file.with_suffix(".csv"))
