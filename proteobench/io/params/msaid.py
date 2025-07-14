"""
MSAID parameter parsing.
"""

import pathlib
from typing import Dict

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname: str) -> ProteoBenchParameters:
    """
    Parse the MSAID parameter file and extract relevant parameters.

    Parameters
    ----------
    fname : str
        The path to the MSAID parameter file (CSV format).

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    # Default and flag settings
    parameters = {
        "software_name": "MSAID",
        "software_version": None,
        "search_engine": "Chimerys",
        "quantification_method": "MS2 Area",
        "ident_fdr_psm": 0.01,
        "ident_fdr_peptide": 0.01,
        "ident_fdr_protein": 0.01,
        "enable_match_between_runs": False,
    }

    # Read the parameter CSV file into a pandas DataFrame
    file = pd.read_csv(fname)

    # Convert the DataFrame to a dictionary
    params_dict: Dict[str, str] = dict(file.itertuples(False, None))

    # Extract relevant parameters from the file's dictionary
    parameters["search_engine"] = params_dict["Algorithm"].split(" ")[0]
    parameters["search_engine_version"] = params_dict["Algorithm"].split(" ")[1]
    parameters["fragment_mass_tolerance"] = (
        "[-" + params_dict["Fragment Mass Tolerance"] + ", " + params_dict["Fragment Mass Tolerance"] + "]"
    )
    parameters["enzyme"] = params_dict["Enzyme"]
    parameters["allowed_miscleavages"] = int(params_dict["Max. Missed Cleavage Sites"])
    parameters["min_peptide_length"] = int(params_dict["Min. Peptide Length"])
    parameters["max_peptide_length"] = int(params_dict["Max. Peptide Length"])
    parameters["fixed_mods"] = params_dict["Static Modifications"]
    parameters["variable_mods"] = params_dict["Variable Modifications"]
    parameters["max_mods"] = int(params_dict["Maximum Number of Modifications"])
    parameters["min_precursor_charge"] = int(params_dict["Min. Peptide Charge"])
    parameters["max_precursor_charge"] = int(params_dict["Max. Peptide Charge"])
    parameters["quantification_method"] = params_dict["Quantification Type"]

    # Set flag for enabling match between runs based on quantification method
    if "Quan in all file" in parameters["quantification_method"] or "MBR" in parameters["quantification_method"]:
        parameters["enable_match_between_runs"] = True
    else:
        parameters["enable_match_between_runs"] = False

    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    """
    Extract parameters from MSAID parameter files and write them to a CSV file.
    """
    for fname in [
        "../../../test/params/MSAID_default_params.csv",
    ]:
        file = pathlib.Path(fname)

        # Extract parameters from the file
        params = extract_params(file)

        # Convert the extracted parameters to a dictionary and then to a pandas Series
        data_dict = params.__dict__
        series = pd.Series(data_dict)

        # Write the Series to a CSV file
        series.to_csv(file.with_suffix(".tsv"), sep="\t")
