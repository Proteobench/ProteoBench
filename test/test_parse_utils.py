"""Tests for proteobench.io.parsing.utils.

Covers add_maxquant_fixed_modifications, which had no test coverage and silently
regressed when MaxQuant parameter parsing switched fixed_mods to ProForma-like
notation ("C[Carbamidomethyl]"), while this function still expected the old
"Carbamidomethyl (C)" format. The mismatch crashed every MaxQuant submission.
"""

import os
from types import SimpleNamespace

import pandas as pd
import pytest

from proteobench.io.parsing.utils import add_maxquant_fixed_modifications

MQPAR_FILE = os.path.join(os.path.dirname(__file__), "params", "mqpar_MQ1.6.3.3_MBR.xml")


def _result_perf(*precursor_ions):
    return pd.DataFrame({"precursor ion": list(precursor_ions)})


def test_single_fixed_modification_applied():
    """A single ProForma fixed mod is added to every matching residue."""
    params = SimpleNamespace(fixed_mods="C[Carbamidomethyl]")
    out = add_maxquant_fixed_modifications(params, _result_perf("PEPTIDEC/2", "ACDEFGHIK/3"))
    assert out["precursor ion"].tolist() == ["PEPTIDEC[Carbamidomethyl]/2", "AC[Carbamidomethyl]DEFGHIK/3"]


def test_multiple_fixed_modifications_applied():
    """Comma-separated ProForma fixed mods are each applied."""
    params = SimpleNamespace(fixed_mods="C[Carbamidomethyl], M[Oxidation]")
    out = add_maxquant_fixed_modifications(params, _result_perf("MASKMC/2"))
    assert out["precursor ion"].tolist() == ["M[Oxidation]ASKM[Oxidation]C[Carbamidomethyl]/2"]


def test_empty_fixed_modifications_is_noop():
    """No fixed modifications must not raise (regression guard for the crash)."""
    params = SimpleNamespace(fixed_mods="")
    out = add_maxquant_fixed_modifications(params, _result_perf("PEPTIDEC/2"))
    assert out["precursor ion"].tolist() == ["PEPTIDEC/2"]


def test_terminal_modification_is_skipped():
    """Terminal fixed modifications are skipped rather than crashing."""
    params = SimpleNamespace(fixed_mods="Protein N-term[Acetyl]")
    out = add_maxquant_fixed_modifications(params, _result_perf("PEPTIDEC/2"))
    assert out["precursor ion"].tolist() == ["PEPTIDEC/2"]


def test_unrecognised_token_is_skipped():
    """Tokens not in residue[mod] form are skipped, not raised."""
    params = SimpleNamespace(fixed_mods="not_a_mod")
    out = add_maxquant_fixed_modifications(params, _result_perf("PEPTIDEC/2"))
    assert out["precursor ion"].tolist() == ["PEPTIDEC/2"]


def test_missing_fixed_mods_attribute_is_noop():
    """Params without a fixed_mods attribute must not raise."""
    out = add_maxquant_fixed_modifications(SimpleNamespace(), _result_perf("AC/2"))
    assert out["precursor ion"].tolist() == ["AC/2"]


@pytest.mark.skipif(not os.path.exists(MQPAR_FILE), reason="MaxQuant parameter fixture not present")
def test_real_maxquant_params_do_not_crash():
    """End-to-end: parsing a real mqpar and applying its fixed mods must succeed."""
    from proteobench.io.params.maxquant import extract_params

    params = extract_params(MQPAR_FILE)
    out = add_maxquant_fixed_modifications(params, _result_perf("PEPTIDEC/2", "ACDEFGHIK/3"))
    # The fixture declares Carbamidomethyl (C) as a fixed modification.
    assert all("C[Carbamidomethyl]" in ion for ion in out["precursor ion"])
