"""
Parameter parsing for the Casanovo-style YAML configs shared by several de novo tools
(AdaNovo, Casanovo, ContraNovo, Pi-HelixNovo, Pi-PrimeNovo).
"""

from __future__ import annotations

import yaml

from proteobench.io.params import ProteoBenchParameters


def extract_yaml_params(
    file_path: str, software_name: str, read_min_len: bool = True, decoding: str = "casanovo"
) -> ProteoBenchParameters:
    """
    Extract parameters from a Casanovo-style YAML config file.

    Parameters
    ----------
    file_path : str
        The path to (or an open handle on) the config file.
    software_name : str
        The software name stored in the parameters.
    read_min_len : bool
        Whether the config's ``min_peptide_len`` is read.
    decoding : str
        How the decoding strategy is derived: ``"casanovo"`` (greedy only when
        ``n_beams == 1``), ``"pihelixnovo"`` (also greedy when ``decoding == "greedy"``)
        or ``"piprimenovo"`` (beam when ``n_beams > 1``, plus the PMC tolerance when
        ``PMC_enable``; also reads the checkpoint).

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a ProteoBenchParameters object.
    """
    params = ProteoBenchParameters(json_path="denovo/denovo_lfq_DDA_HCD.json")

    try:
        file = yaml.safe_load(file_path)
    except Exception:
        with open(file_path) as f:
            file = yaml.load(f, yaml.SafeLoader)

    params.software_name = software_name
    if decoding == "piprimenovo":
        params.checkpoint = file["load_file_name"]
    params.n_beams = file["n_beams"]
    params.n_peaks = file["n_peaks"]
    params.precursor_mass_tolerance = file["precursor_mass_tol"]
    if read_min_len:
        params.min_peptide_length = file["min_peptide_len"]
    params.max_peptide_length = file["max_length"]
    params.min_mz = file["min_mz"]
    params.max_mz = file["max_mz"]
    params.min_intensity = file["min_intensity"]
    params.tokens = "; ".join(list(file["residues"].keys()))
    params.max_precursor_charge = file["max_charge"]
    params.remove_precursor_tol = file["remove_precursor_tol"]
    params.isotope_error_range = str(file["isotope_error_range"])

    if decoding == "casanovo":
        greedy = file["n_beams"] == 1
    elif decoding == "pihelixnovo":
        greedy = file["decoding"] == "greedy" or file["n_beams"] == 1
    else:
        pmc_enable = file["PMC_enable"]
        greedy = not file["n_beams"] > 1
    params.decoding_strategy = "greedy search" if greedy else "beam search"
    if decoding == "piprimenovo" and pmc_enable:
        params.decoding_strategy += f" + PMC [{file['mass_control_tol']} Da]"

    params.fill_none()
    return params
