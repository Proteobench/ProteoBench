"""Tests for ProteoBenchParameters.normalize() — centralized parameter coercion."""

import math

import numpy as np
import pytest

from proteobench.io.params import ProteoBenchParameters


def _make_params(**overrides):
    """Create a ProteoBenchParameters instance and set *overrides* on it."""
    params = ProteoBenchParameters()
    for key, val in overrides.items():
        setattr(params, key, val)
    # Run normalization (would normally happen via fill_none)
    params.normalize()
    return params


# ── FDR coercion ──────────────────────────────────────────────────────────


class TestFDRNormalization:
    def test_float_stays(self):
        p = _make_params(ident_fdr_psm=0.01)
        assert p.ident_fdr_psm == pytest.approx(0.01)

    def test_string_decimal(self):
        p = _make_params(ident_fdr_psm="0.05")
        assert p.ident_fdr_psm == pytest.approx(0.05)

    def test_percentage_int(self):
        """A value of 1 means 1% and should become 0.01."""
        p = _make_params(ident_fdr_psm=1)
        assert p.ident_fdr_psm == pytest.approx(0.01)

    def test_percentage_string(self):
        p = _make_params(ident_fdr_protein="5")
        assert p.ident_fdr_protein == pytest.approx(0.05)

    def test_nan_untouched(self):
        p = _make_params(ident_fdr_psm=np.nan)
        assert math.isnan(p.ident_fdr_psm)

    def test_none_becomes_nan(self):
        p = _make_params(ident_fdr_peptide=None)
        assert isinstance(p.ident_fdr_peptide, float) and math.isnan(p.ident_fdr_peptide)

    def test_invalid_string_becomes_nan(self):
        p = _make_params(ident_fdr_psm="abc")
        assert isinstance(p.ident_fdr_psm, float) and math.isnan(p.ident_fdr_psm)

    def test_all_three_fields(self):
        p = _make_params(ident_fdr_psm=0.01, ident_fdr_peptide="0.05", ident_fdr_protein=5)
        assert p.ident_fdr_psm == pytest.approx(0.01)
        assert p.ident_fdr_peptide == pytest.approx(0.05)
        assert p.ident_fdr_protein == pytest.approx(0.05)


# ── Integer coercion ──────────────────────────────────────────────────────


class TestIntNormalization:
    def test_string_to_int(self):
        p = _make_params(allowed_miscleavages="2")
        assert p.allowed_miscleavages == 2
        assert isinstance(p.allowed_miscleavages, int)

    def test_float_to_int(self):
        p = _make_params(min_peptide_length=7.0)
        assert p.min_peptide_length == 7
        assert isinstance(p.min_peptide_length, int)

    def test_int_stays(self):
        p = _make_params(max_precursor_charge=4)
        assert p.max_precursor_charge == 4

    def test_nan_untouched(self):
        p = _make_params(max_mods=np.nan)
        assert isinstance(p.max_mods, float) and math.isnan(p.max_mods)

    def test_invalid_string_becomes_nan(self):
        p = _make_params(allowed_miscleavages="abc")
        assert isinstance(p.allowed_miscleavages, float) and math.isnan(p.allowed_miscleavages)

    def test_all_int_fields(self):
        p = _make_params(
            allowed_miscleavages="1",
            min_peptide_length="6",
            max_peptide_length="50",
            min_precursor_charge="2",
            max_precursor_charge="4",
            max_mods="3",
        )
        assert p.allowed_miscleavages == 1
        assert p.min_peptide_length == 6
        assert p.max_peptide_length == 50
        assert p.min_precursor_charge == 2
        assert p.max_precursor_charge == 4
        assert p.max_mods == 3


# ── Boolean coercion ─────────────────────────────────────────────────────


class TestBoolNormalization:
    @pytest.mark.parametrize("val", ["True", "true", "TRUE", "1", "yes"])
    def test_truthy_strings(self, val):
        p = _make_params(enable_match_between_runs=val)
        assert p.enable_match_between_runs is True

    @pytest.mark.parametrize("val", ["False", "false", "0", "no"])
    def test_falsy_strings(self, val):
        p = _make_params(enable_match_between_runs=val)
        assert p.enable_match_between_runs is False

    def test_bool_true_stays(self):
        p = _make_params(enable_match_between_runs=True)
        assert p.enable_match_between_runs is True

    def test_bool_false_stays(self):
        p = _make_params(enable_match_between_runs=False)
        assert p.enable_match_between_runs is False

    def test_int_1(self):
        p = _make_params(enable_match_between_runs=1)
        assert p.enable_match_between_runs is True

    def test_int_0(self):
        p = _make_params(enable_match_between_runs=0)
        assert p.enable_match_between_runs is False


# ── Missing sentinel handling ─────────────────────────────────────────────


class TestMissingSentinels:
    @pytest.mark.parametrize("val", ["not specified", "N/A", "None", "none", "unknown", "placeholder", "", "NA", "nan"])
    def test_sentinels_become_nan(self, val):
        p = _make_params(enzyme=val)
        assert isinstance(p.enzyme, float) and math.isnan(p.enzyme)

    def test_sentinel_on_int_field(self):
        p = _make_params(allowed_miscleavages="not specified")
        assert isinstance(p.allowed_miscleavages, float) and math.isnan(p.allowed_miscleavages)

    def test_sentinel_on_fdr_field(self):
        p = _make_params(ident_fdr_psm="N/A")
        assert isinstance(p.ident_fdr_psm, float) and math.isnan(p.ident_fdr_psm)


# ── Enzyme normalization ─────────────────────────────────────────────────


class TestEnzymeNormalization:
    def test_lowercase_trypsin(self):
        p = _make_params(enzyme="trypsin")
        assert p.enzyme == "Trypsin"

    def test_trypsin_p(self):
        p = _make_params(enzyme="trypsin/p")
        assert p.enzyme == "Trypsin/P"

    def test_trypsin_p_already_canonical(self):
        p = _make_params(enzyme="Trypsin/P")
        assert p.enzyme == "Trypsin/P"

    def test_stricttrypsin(self):
        p = _make_params(enzyme="stricttrypsin")
        assert p.enzyme == "Trypsin"

    def test_lysc_variants(self):
        assert _make_params(enzyme="lys-c").enzyme == "Lys-C"
        assert _make_params(enzyme="lysc").enzyme == "Lys-C"
        assert _make_params(enzyme="Lys-C").enzyme == "Lys-C"

    def test_unknown_enzyme_kept_as_is(self):
        p = _make_params(enzyme="CustomEnzyme")
        assert p.enzyme == "CustomEnzyme"

    def test_nan_enzyme(self):
        p = _make_params(enzyme=np.nan)
        assert isinstance(p.enzyme, float) and math.isnan(p.enzyme)
