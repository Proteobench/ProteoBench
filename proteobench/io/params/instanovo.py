"""
InstaNovo parameter parsing.
"""

from __future__ import annotations

import yaml

from proteobench.io.params import ProteoBenchParameters


def extract_params(file_path: str) -> ProteoBenchParameters:

    params = ProteoBenchParameters(json_path="denovo/denovo_lfq_DDA_HCD.json")

    with open(file_path) as f:
        file = yaml.load(f, yaml.SafeLoader)

    params.software_name = "InstaNovo"
    params.n_beams = file["n_beams"]
    params.n_peaks = file["n_peaks"]
    params.precursor_mass_tolerance = file["precursor_mass_tol"]
    # params.min_peptide_length = file["min_peptide_len"]
    params.max_peptide_length = file["max_length"]
    params.min_mz = file["min_mz"]
    params.max_mz = file["max_mz"]
    params.min_intensity = file["min_intensity"]
    params.tokens = "; ".join(list(file["residues"].keys()))
    params.max_precursor_charge = file["max_charge"]
    params.remove_precursor_tol = file["remove_precursor_tol"]
    params.isotope_error_range = str(file["isotope_error_range"])

    if file["n_beams"] == 1:
        params.decoding_strategy = "greedy search"
    else:
        params.decoding_strategy = "beam search"

    params.fill_none()
    return params
