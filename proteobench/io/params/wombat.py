"""Parser for WOMBAT-P yaml configuration files."""

import pathlib
from typing import Optional

import pandas as pd
import yaml

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname: pathlib.Path) -> ProteoBenchParameters:
    """
    Extracts parameters from a WOMBAT-P YAML configuration file.

    Args:
        fname (pathlib.Path): Path to the WOMBAT-P configuration file.

    Returns:
        ProteoBenchParameters: The extracted parameters as a ProteoBenchParameters object.
    """
    try:
        record = yaml.safe_load(fname)
    except AttributeError:
        print(f"Load locally: {fname}")
        with open(fname, "rb") as f:
            record = yaml.safe_load(f)

    # Extracting the summary data
    summary = record["params"]
    params = ProteoBenchParameters()

    # Set software details
    params.software_name = "Wombat"
    params.software_version = record["version"]
    params.search_engine = "various"
    # params.search_engine_version = params.software_version

    # Extract FASTA related details
    fasta = record["fastafile"]
    params.enzyme = summary["enzyme"]
    if params.enzyme == "trypsin":
        params.enzyme = "Trypsin"
    params.allowed_miscleavages = summary["miscleavages"]
    params.fixed_mods = summary["fixed_mods"]
    params.variable_mods = summary["variable_mods"]
    params.max_mods = summary["max_mods"]
    params.min_peptide_length = summary["min_peptide_length"]
    params.max_peptide_length = summary["max_peptide_length"]

    # Extract search parameters
    params.precursor_mass_tolerance = summary["precursor_mass_tolerance"]
    params.fragment_mass_tolerance = summary["fragment_mass_tolerance"]
    params.ident_fdr_protein = summary["ident_fdr_protein"]
    params.ident_fdr_peptide = summary["ident_fdr_peptide"]
    params.ident_fdr_psm = summary["ident_fdr_psm"]

    # Extract features and workflow details
    params.min_precursor_charge = summary["min_precursor_charge"]
    params.max_precursor_charge = summary["max_precursor_charge"]
    params.enable_match_between_runs = summary["enable_match_between_runs"]
    params.abundance_normalization_ions = summary["normalization_method"]
    params.fill_none()
    return params


if __name__ == "__main__":
    # Create test CSV files for each YAML configuration
    for fname in ["../../../test/params/wombat_params.yaml"]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".csv"))
