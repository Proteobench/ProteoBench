"""Parser for Alphapept yaml configuration files."""

import pathlib
from typing import Optional

import pandas as pd
import yaml

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname: pathlib.Path) -> ProteoBenchParameters:
    """
    Extract parameters from an AlphaPept YAML configuration file.

    Parameters
    ----------
    fname : pathlib.Path
        Path to the AlphaPept configuration file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a ProteoBenchParameters object.
    """
    try:
        record = yaml.safe_load(fname)
    except AttributeError:
        print(f"Load locally: {fname}")
        with open(fname, "rb") as f:
            record = yaml.safe_load(f)

    # Extracting the summary data
    summary = record["summary"]
    params = ProteoBenchParameters()

    # Set software details
    params.software_name = "AlphaPept"
    params.software_version = summary["version"]
    params.search_engine = params.software_name
    params.search_engine_version = params.software_version

    # Extract FASTA related details
    fasta = record["fasta"]
    params.enzyme = fasta["protease"]
    if params.enzyme == "trypsin":
        params.enzyme = "Trypsin"
    params.allowed_miscleavages = fasta["n_missed_cleavages"]

    mods_fixed = fasta["mods_fixed"]
    mods_fixed.extend(fasta["mods_fixed_terminal"])
    mods_fixed.extend(fasta["mods_fixed_terminal_prot"])
    params.fixed_mods = ",".join(mods_fixed)

    mods_variable = fasta["mods_variable"]
    mods_variable.extend(fasta["mods_variable_terminal"])
    mods_variable.extend(fasta["mods_variable_terminal_prot"])
    params.variable_mods = ",".join(mods_variable)

    params.max_mods = fasta["n_modifications_max"]
    params.min_peptide_length = fasta["pep_length_min"]
    params.max_peptide_length = fasta["pep_length_max"]

    # Extract search parameters
    search = record["search"]
    _tolerance_unit = "Da"  # Default unit is Da
    if search["ppm"]:
        _tolerance_unit = "ppm"
    params.precursor_mass_tolerance = (
        f'[-{search["prec_tol"]} {_tolerance_unit}, {search["prec_tol"]} {_tolerance_unit}]'
    )
    params.fragment_mass_tolerance = (
        f'[-{search["frag_tol"]} {_tolerance_unit}, {search["frag_tol"]} {_tolerance_unit}]'
    )
    params.ident_fdr_protein = search["protein_fdr"]
    params.ident_fdr_psm = search["peptide_fdr"]

    # Extract features and workflow details
    params.min_precursor_charge = record["features"]["iso_charge_min"]
    params.max_precursor_charge = record["features"]["iso_charge_max"]
    params.enable_match_between_runs = record["workflow"]["match"]  # Check if matching is enabled
    params.abundance_normalization_ions = None  # No normalization in AlphaPept
    params.fill_none()
    return params


if __name__ == "__main__":
    # Create test CSV files for each YAML configuration
    for fname in [
        "../../../test/params/alphapept_0.4.9.yaml",
        "../../../test/params/alphapept_0.4.9_unnormalized.yaml",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        print(series)
        series.to_csv(file.with_suffix(".csv"))
