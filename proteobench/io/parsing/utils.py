"""Utilities for parsing modifications."""

import pandas as pd
import psm_utils as pu

from proteobench.io.params import ProteoBenchParameters


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
    proforma, charge = proforma.split("|")
    peptidoform = pu.Peptidoform(proforma)
    peptidoform.add_fixed_modifications([(mod_name, aas)])
    peptidoform.apply_fixed_modifications()
    return peptidoform.proforma + "|" + charge


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
    """
    if hasattr(params, "fixed_mods"):
        fixed_mods = params.fixed_mods.split(",")

        for mod in fixed_mods:
            mod_name, aas = mod.split(" ")
            aas_list = list(aas[1:-1])
            result_perf["precursor ion"] = result_perf["precursor ion"].apply(add_fixed_mod, args=(mod_name, aas_list))

    return result_perf
