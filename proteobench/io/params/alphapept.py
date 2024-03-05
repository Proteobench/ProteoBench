"""Alphapept uses the yaml format to save configuration."""

import pathlib

import pandas as pd
import yaml

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname) -> ProteoBenchParameters:
    with open(fname) as f:
        record = yaml.safe_load(f)
    summary = record["summary"]
    params = ProteoBenchParameters()
    params.software_name = "AlphaPept"
    params.software_version = summary["version"]
    params.search_engine = params.software_name
    params.search_engine_version = params.software_version
    fasta = record["fasta"]
    params.enzyme = fasta["protease"]
    params.allowed_miscleavages = fasta["n_missed_cleavages"]
    params.fixed_mods = ",".join(fasta["mods_fixed"])
    params.variable_mods = ",".join(fasta["mods_variable"])
    params.max_mods = fasta["n_modifications_max"]
    params.min_peptide_length = fasta["pep_length_min"]
    params.max_peptide_length = fasta["pep_length_max"]
    search = record["search"]
    _tolerance_unit = "Da"  # default
    if search["ppm"]:
        _tolerance_unit = "ppm"
    params.precursor_mass_tolerance = f'{search["prec_tol"]} {_tolerance_unit}'
    params.fragment_mass_tolerance = f'{search["frag_tol"]} {_tolerance_unit}'
    params.ident_fdr_protein = search["protein_fdr"]
    params.ident_fdr_peptide = search["peptide_fdr"]
    # params.ident_fdr_psm = search
    params.min_precursor_charge = record["features"]["iso_charge_min"]
    params.max_precursor_charge = record["features"]["iso_charge_max"]
    params.enable_match_between_runs = record["workflow"]["match"]  # ! check

    return params


if __name__ == "__main__":
    for fname in [
        "../../../test/params/alphapept_0.4.9.yaml",
        "../../../test/params/alphapept_0.4.9_unnormalized.yaml",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".csv"))
