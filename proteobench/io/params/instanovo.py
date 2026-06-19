"""
InstaNovo parameter parsing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from proteobench.io.params import ProteoBenchParameters


PARAMS_JSON = Path(__file__).resolve().parent / "json" / "denovo" / "denovo_DDA_HCD.json"


def _load_yaml(file_path: Any) -> dict[str, Any]:
    if hasattr(file_path, "read"):
        contents = file_path.read()
        if hasattr(file_path, "seek"):
            file_path.seek(0)
        if isinstance(contents, bytes):
            contents = contents.decode("utf-8")
        loaded = yaml.safe_load(contents)
    elif isinstance(file_path, (str, os.PathLike)) and Path(file_path).is_file():
        with open(file_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
    else:
        loaded = yaml.safe_load(file_path)

    if not isinstance(loaded, dict):
        raise ValueError("InstaNovo parameter file must be a YAML mapping.")
    return loaded


def _get_first(config: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = config.get(key)
        if value is not None:
            return value
    return None


def _set_if_present(params: ProteoBenchParameters, attr: str, value: Any) -> None:
    if value is not None:
        setattr(params, attr, value)


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
    params = ProteoBenchParameters(filename=PARAMS_JSON)
    file = _load_yaml(file_path)

    params.software_name = "InstaNovo"
    params.software_version = str(_get_first(file, "software_version", "instanovo_version") or "1.2.2")

    instanovo_model = _get_first(file, "instanovo_model", "model_path", "model")
    instanovo_plus_model = _get_first(file, "instanovo_plus_model")
    if instanovo_model and instanovo_plus_model and file.get("refine", file.get("with_refinement", False)):
        params.checkpoint = f"{instanovo_model}; {instanovo_plus_model}"
    else:
        _set_if_present(params, "checkpoint", instanovo_model or instanovo_plus_model)

    n_beams = _get_first(file, "num_beams", "n_beams")
    _set_if_present(params, "n_beams", n_beams)
    _set_if_present(params, "n_peaks", _get_first(file, "n_peaks"))
    _set_if_present(
        params, "precursor_mass_tolerance", _get_first(file, "precursor_mass_tol", "precursor_mass_tolerance")
    )
    _set_if_present(params, "min_peptide_length", _get_first(file, "min_peptide_len", "min_length"))
    _set_if_present(params, "max_peptide_length", _get_first(file, "max_length"))
    _set_if_present(params, "min_mz", _get_first(file, "min_mz"))
    _set_if_present(params, "max_mz", _get_first(file, "max_mz"))
    _set_if_present(params, "min_intensity", _get_first(file, "min_intensity"))
    _set_if_present(params, "max_precursor_charge", _get_first(file, "max_charge"))
    _set_if_present(params, "remove_precursor_tol", _get_first(file, "remove_precursor_tol"))

    isotope_error_range = _get_first(file, "isotope_error_range")
    if isotope_error_range is not None:
        params.isotope_error_range = str(isotope_error_range)

    residues = _get_first(file, "residues", "residue_remapping")
    if isinstance(residues, dict):
        params.tokens = "; ".join(list(residues.keys()))

    if file.get("use_knapsack"):
        params.decoding_strategy = "knapsack beam search"
    elif n_beams == 1:
        params.decoding_strategy = "greedy search"
    elif n_beams is not None:
        params.decoding_strategy = "beam search"
    elif file.get("decoding") == "greedy":
        params.decoding_strategy = "greedy search"
    elif file.get("decoding") == "beam":
        params.decoding_strategy = "beam search"

    params.fill_none()
    return params
