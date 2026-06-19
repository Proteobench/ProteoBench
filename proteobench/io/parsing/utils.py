"""Utilities for parsing modifications."""

import re

import pandas as pd
import psm_utils as pu

from proteobench.io.params import ProteoBenchParameters

# MaxQuant fixed modifications are exposed in the ProForma-like notation produced by
# ``io.params.maxquant._homogenize_mod`` (e.g. ``"C[Carbamidomethyl]"`` or
# ``"Protein N-term[Acetyl]"``), comma-separated. Match a residue specifier followed
# by a bracketed modification name.
_PROFORMA_FIXED_MOD = re.compile(r"^(?P<residues>[^\[]+)\[(?P<name>[^\]]+)\]$")


def add_fixed_mod(proforma: str, mod_name: str, aas: str) -> str:
    """
    Add a single fixed modification to a peptide in ProForma format.

    Parameters
    ----------
    proforma : str
        Peptide in ProForma format.
    mod_name : str
        Name of the modification to add as a fixed modification.
    aas : str
        The amino acid whereon the fixed modifications should be registered.

    Returns
    -------
    str
        The modified peptide in ProForma format.
    """
    proforma, charge = proforma.split("/")
    peptidoform = pu.Peptidoform(proforma)
    peptidoform.add_fixed_modifications([(mod_name, aas)])
    peptidoform.apply_fixed_modifications()
    return peptidoform.proforma + "/" + charge


def add_maxquant_fixed_modifications(params: ProteoBenchParameters, result_perf: pd.DataFrame) -> pd.DataFrame:
    """
    Format MaxQuant modifications.

    Parameters
    ----------
    params : ProteoBenchParameters
        ProteoBenchParameters object from MaxQuant results. Contains modifications in `fixed_mods` attribute.
    result_perf : pd.DataFrame
        The benchmarking results.

    Returns
    -------
    pd.DataFrame
        Results of benchmarking with parsed modifications.

    Notes
    -----
    ``params.fixed_mods`` uses ProForma-like notation (``"C[Carbamidomethyl]"``,
    comma-separated). Empty values (no fixed modifications), terminal modifications
    (e.g. ``"Protein N-term[Acetyl]"``), and unrecognised tokens are skipped rather
    than raised, so a submission is never blocked by modification formatting.
    """
    fixed_mods = getattr(params, "fixed_mods", None)
    if not isinstance(fixed_mods, str) or not fixed_mods.strip():
        return result_perf

    for token in fixed_mods.split(","):
        token = token.strip()
        if not token:
            continue
        match = _PROFORMA_FIXED_MOD.match(token)
        if match is None:
            # Unrecognised format; skip rather than crash the whole submission.
            continue
        residues = match.group("residues").strip()
        mod_name = match.group("name").strip()
        # Terminal fixed modifications are not applied at the residue level here.
        if "-term" in residues.lower():
            continue
        aas_list = list(residues)
        result_perf["precursor ion"] = result_perf["precursor ion"].apply(add_fixed_mod, args=(mod_name, aas_list))

    return result_perf
