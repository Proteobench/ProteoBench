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


def test_extract_params_legacy_flat_config():
    actual = instanovo_params.extract_params(TESTDATA_DIR / "data/denovo/configs/instanovo/config.yaml")

    assert actual.software_name == "InstaNovo"
    assert actual.n_beams == 5
    assert actual.n_peaks == 200
    assert actual.precursor_mass_tolerance == 50
    assert actual.max_peptide_length == 50
    assert actual.max_precursor_charge == 8
    assert "M(ox)" in actual.tokens
