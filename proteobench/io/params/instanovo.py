"""
InstaNovo parameter parsing.
"""

from __future__ import annotations

import yaml

from proteobench.io.params import ProteoBenchParameters


def extract_params(file_path: str) -> ProteoBenchParameters:
    """
    Extract parameters from the config file.

    Parameters
    ----------
    file_path : str
        The path to the InstaNovo config file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a ProteoBenchParameters object.
    """
    params = ProteoBenchParameters(json_path="denovo/denovo_lfq_DDA_HCD.json")

    try:
        file = yaml.safe_load(file_path)
    except:
        with open(file_path) as f:
            file = yaml.load(f, yaml.SafeLoader)

    params.software_name = "InstaNovo"
    params.checkpoint = file.get("instanovo_model")
    params.n_beams = file["num_beams"]
    params.max_peptide_length = file["max_length"]
    params.max_precursor_charge = file["max_charge"]
    params.isotope_error_range = str(file["isotope_error_range"])
    params.remove_precursor_tol = None  # not in config
    params.tokens = "; ".join(list(file["residue_remapping"].keys()))

    if file["num_beams"] == 1:
        params.decoding_strategy = "greedy search"
    else:
        params.decoding_strategy = "beam search"

    params.fill_none()
    return params
