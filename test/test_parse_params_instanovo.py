from pathlib import Path

import pandas as pd

import proteobench.io.params.instanovo as instanovo_params

TESTDATA_DIR = Path(__file__).parent


def test_extract_params_v1_2_2_config():
    actual = instanovo_params.extract_params(TESTDATA_DIR / "params/denovo/instanovo/config_v1_2_2.yaml")

    assert actual.software_name == "InstaNovo"
    assert actual.software_version == "1.2.2"
    assert actual.checkpoint == "instanovo-v1.2.0; instanovoplus-v1.1.0"
    assert actual.n_beams == 5
    assert actual.max_peptide_length == 40
    assert actual.max_precursor_charge == 10
    assert actual.isotope_error_range == "[0, 1]"
    assert actual.decoding_strategy == "beam search"
    assert pd.isna(actual.n_peaks)
    # `filter_precursor_ppm: 20` is the v1.2.2 spelling; the unit is kept because the key
    # names it, so the submitted value is not an ambiguous bare number.
    assert actual.precursor_mass_tolerance == "20 ppm"


def test_extract_params_legacy_flat_config():
    actual = instanovo_params.extract_params(TESTDATA_DIR / "data/denovo/configs/instanovo/config.yaml")

    assert actual.software_name == "InstaNovo"
    assert actual.n_beams == 5
    assert actual.n_peaks == 200
    assert actual.precursor_mass_tolerance == 50
    assert actual.max_peptide_length == 50
    assert actual.max_precursor_charge == 8
    assert "M(ox)" in actual.tokens


def test_precursor_mass_tolerance_prefers_explicit_keys_over_filter_precursor_ppm():
    """A config carrying both keys reports the explicitly named one, unit-less as before."""
    assert (
        instanovo_params._extract_precursor_mass_tolerance({"precursor_mass_tol": 50, "filter_precursor_ppm": 20}) == 50
    )


def test_precursor_mass_tolerance_from_filter_precursor_ppm_carries_the_unit():
    """`filter_precursor_ppm` names its unit, so it is preserved in the value."""
    assert instanovo_params._extract_precursor_mass_tolerance({"filter_precursor_ppm": 20}) == "20 ppm"
    assert instanovo_params._extract_precursor_mass_tolerance({"filter_precursor_ppm": 12.5}) == "12.5 ppm"


def test_precursor_mass_tolerance_absent():
    """Neither key present leaves the field unset rather than guessing a unit."""
    assert instanovo_params._extract_precursor_mass_tolerance({}) is None
    assert instanovo_params._extract_precursor_mass_tolerance({"max_charge": 10}) is None
