from pathlib import Path

import pandas as pd
import yaml

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
    actual = instanovo_params.extract_params(TESTDATA_DIR / "params/denovo/instanovo/config.yaml")

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


def test_extract_params_diffusion_only_is_not_reported_as_beam_search():
    """InstaNovo+ run alone is diffusion sampling, whatever `num_beams` the config carries.

    `instanovo diffusion predict --no-refinement` starts the reverse process from a uniform
    sample; no transformer beam search runs. Such a config names only the InstaNovo+
    checkpoint, which is what distinguishes it.
    """
    actual = instanovo_params.extract_params(
        TESTDATA_DIR / "params/denovo/instanovo/config_v1_2_2_diffusion_only.yaml"
    )

    assert actual.decoding_strategy == "diffusion sampling"
    assert actual.checkpoint == "instanovoplus-v1.1.0"
    assert pd.isna(actual.n_beams)


def test_diffusion_is_detected_before_the_beam_branches():
    """A stray default `num_beams` must not turn a diffusion run into a beam search."""
    config = yaml.dump({"instanovo_plus_model": "instanovoplus-v1.1.0", "num_beams": 5})
    assert instanovo_params.extract_params(config).decoding_strategy == "diffusion sampling"


def test_explicit_diffusion_only_flag_is_honoured():
    """`diffusion_only: true` is respected even when a transformer checkpoint is named."""
    config = yaml.dump(
        {
            "diffusion_only": True,
            "instanovo_model": "instanovo-v1.2.0",
            "instanovo_plus_model": "instanovoplus-v1.1.0",
            "num_beams": 10,
        }
    )
    assert instanovo_params.extract_params(config).decoding_strategy == "diffusion sampling"


def test_combined_transformer_and_refinement_is_still_a_beam_search():
    """Naming both checkpoints is refinement, not diffusion-only."""
    config = yaml.dump(
        {
            "instanovo_model": "instanovo-v1.2.0",
            "instanovo_plus_model": "instanovoplus-v1.1.0",
            "refine": True,
            "num_beams": 10,
        }
    )
    actual = instanovo_params.extract_params(config)
    assert actual.decoding_strategy == "beam search"
    assert actual.checkpoint == "instanovo-v1.2.0; instanovoplus-v1.1.0"


def test_tokens_come_from_residues_not_the_remapping():
    """`residue_remapping` keys are input spellings that get rewritten, not model tokens."""
    remapping_only = yaml.dump({"residue_remapping": {"M(ox)": "M[UNIMOD:35]", "(+42.01)": "[UNIMOD:1]"}})
    assert pd.isna(instanovo_params.extract_params(remapping_only).tokens)

    with_residues = yaml.dump(
        {
            "residues": {"G": 57.021464, "M[UNIMOD:35]": 147.0354},
            "residue_remapping": {"M(ox)": "M[UNIMOD:35]"},
        }
    )
    tokens = instanovo_params.extract_params(with_residues).tokens
    assert tokens == "G; M[UNIMOD:35]"
    assert "M(ox)" not in tokens
