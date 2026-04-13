"""
Tests for the parameter-file and FASTA validation module.
"""

import os

import pandas as pd
import pytest

from proteobench.io.params.validation import (
    check_charge_range,
    check_fasta_from_params,
    check_fasta_from_results,
    check_peptide_length_range,
    validate_all,
    _extract_charges_from_precursor_ions,
    _parse_charge_from_ion,
    _parse_sequence_from_ion,
    _to_int_or_none,
)

TEST_PARAMS_DIR = os.path.join(os.path.dirname(__file__), "params")
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "quant", "quant_lfq_ion_DDA_QExactive")


# ---------------------------------------------------------------------------
# Minimal stub for ProteoBenchParameters
# ---------------------------------------------------------------------------


class _Params:
    """Minimal stand-in for ProteoBenchParameters."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# Helper builders for a minimal intermediate_df
# ---------------------------------------------------------------------------


def _make_intermediate_df(
    precursor_ions=None,
    yeast=None,
    ecoli=None,
    human=None,
):
    """Build a small intermediate-style DataFrame for tests."""
    if precursor_ions is None:
        precursor_ions = ["PEPTIDE/2", "LONGPEPTIDER/3", "SHORTK/1", "AAAA/4"]
    n = len(precursor_ions)
    data = {
        "precursor ion": precursor_ions,
        "YEAST": yeast if yeast is not None else ([True] + [False] * (n - 1)),
        "ECOLI": ecoli if ecoli is not None else ([False, True] + [False] * (n - 2) if n > 1 else [False]),
        "HUMAN": human if human is not None else ([False, False] + [True] * (n - 2) if n > 1 else [True]),
    }
    return pd.DataFrame(data)


# ===========================================================================
# Internal helpers
# ===========================================================================


class TestParseChargeFromIon:
    def test_returns_int_for_valid_ion(self):
        assert _parse_charge_from_ion("PEPTIDE/2") == 2

    def test_returns_int_for_high_charge(self):
        assert _parse_charge_from_ion("LONGPEPTIDER/4") == 4

    def test_returns_none_for_missing_slash(self):
        assert _parse_charge_from_ion("PEPTIDE") is None

    def test_returns_none_for_non_numeric_charge(self):
        assert _parse_charge_from_ion("PEPTIDE/X") is None

    def test_returns_none_for_non_string(self):
        assert _parse_charge_from_ion(42) is None


class TestParseSequenceFromIon:
    def test_plain_sequence(self):
        assert _parse_sequence_from_ion("PEPTIDE/2") == "PEPTIDE"

    def test_removes_bracketed_modification(self):
        result = _parse_sequence_from_ion("PEPTM[Oxidation]IDE/2")
        assert result == "PEPTMIDE"

    def test_removes_parenthesised_modification(self):
        result = _parse_sequence_from_ion("PEPT(ox)IDE/2")
        assert result == "PEPTIDE"

    def test_returns_none_for_non_string(self):
        assert _parse_sequence_from_ion(None) is None


class TestExtractCharges:
    def test_returns_correct_charges(self):
        series = pd.Series(["PEPTIDE/2", "LONGPEPTIDER/3", "SHORTK/1"])
        charges = _extract_charges_from_precursor_ions(series)
        assert sorted(charges.tolist()) == [1, 2, 3]

    def test_skips_malformed_entries(self):
        series = pd.Series(["PEPTIDE/2", "INVALID", None])
        charges = _extract_charges_from_precursor_ions(series)
        assert charges.tolist() == [2]


class TestToIntOrNone:
    def test_int_input(self):
        assert _to_int_or_none(3) == 3

    def test_string_input(self):
        assert _to_int_or_none("3") == 3

    def test_none_input(self):
        assert _to_int_or_none(None) is None

    def test_float_input(self):
        assert _to_int_or_none(3.7) == 3

    def test_non_numeric_string(self):
        assert _to_int_or_none("nan") is None


# ===========================================================================
# check_charge_range
# ===========================================================================


class TestCheckChargeRange:
    def test_no_warnings_when_charges_within_range(self):
        params = _Params(min_precursor_charge=1, max_precursor_charge=4)
        df = _make_intermediate_df(precursor_ions=["PEPTIDE/2", "LONGPEPTIDER/3"])
        assert check_charge_range(params, df) == []

    def test_warning_when_charge_below_min(self):
        params = _Params(min_precursor_charge=2, max_precursor_charge=4)
        df = _make_intermediate_df(precursor_ions=["PEPTIDE/1"])
        warnings = check_charge_range(params, df)
        assert len(warnings) == 1
        assert "minimum charge" in warnings[0].lower()

    def test_warning_when_charge_above_max(self):
        params = _Params(min_precursor_charge=1, max_precursor_charge=3)
        df = _make_intermediate_df(precursor_ions=["PEPTIDE/5"])
        warnings = check_charge_range(params, df)
        assert len(warnings) == 1
        assert "maximum charge" in warnings[0].lower()

    def test_no_warnings_when_params_are_none(self):
        params = _Params(min_precursor_charge=None, max_precursor_charge=None)
        df = _make_intermediate_df()
        assert check_charge_range(params, df) == []

    def test_no_warnings_when_column_missing(self):
        params = _Params(min_precursor_charge=1, max_precursor_charge=3)
        df = pd.DataFrame({"peptidoform": ["PEPTIDE", "OTHER"]})
        assert check_charge_range(params, df) == []

    def test_both_warnings_returned(self):
        params = _Params(min_precursor_charge=2, max_precursor_charge=3)
        df = _make_intermediate_df(precursor_ions=["PEPTIDE/1", "LONGPEPTIDER/5"])
        warnings = check_charge_range(params, df)
        assert len(warnings) == 2


# ===========================================================================
# check_peptide_length_range
# ===========================================================================


class TestCheckPeptideLengthRange:
    def test_no_warnings_when_lengths_within_range(self):
        # "PEPTIDE" length=7, "LONGPEPTIDER" length=12
        params = _Params(min_peptide_length=5, max_peptide_length=20)
        df = _make_intermediate_df(precursor_ions=["PEPTIDE/2", "LONGPEPTIDER/3"])
        assert check_peptide_length_range(params, df) == []

    def test_warning_when_peptide_shorter_than_min(self):
        params = _Params(min_peptide_length=8, max_peptide_length=30)
        df = _make_intermediate_df(precursor_ions=["PEPTI/2"])  # length 5
        warnings = check_peptide_length_range(params, df)
        assert len(warnings) == 1
        assert "minimum peptide length" in warnings[0].lower()

    def test_warning_when_peptide_longer_than_max(self):
        params = _Params(min_peptide_length=5, max_peptide_length=8)
        df = _make_intermediate_df(precursor_ions=["VERYLONGPEPTIDE/2"])  # length 15
        warnings = check_peptide_length_range(params, df)
        assert len(warnings) == 1
        assert "maximum peptide length" in warnings[0].lower()

    def test_no_warnings_when_params_are_none(self):
        params = _Params(min_peptide_length=None, max_peptide_length=None)
        df = _make_intermediate_df()
        assert check_peptide_length_range(params, df) == []

    def test_uses_peptidoform_column_when_no_precursor_ion(self):
        params = _Params(min_peptide_length=10, max_peptide_length=30)
        df = pd.DataFrame({"peptidoform": ["SHORTPEP"]})  # length 8
        warnings = check_peptide_length_range(params, df)
        assert len(warnings) == 1
        assert "minimum peptide length" in warnings[0].lower()

    def test_no_warnings_when_columns_missing(self):
        params = _Params(min_peptide_length=5, max_peptide_length=30)
        df = pd.DataFrame({"other_col": [1, 2]})
        assert check_peptide_length_range(params, df) == []


# ===========================================================================
# check_fasta_from_params
# ===========================================================================


class TestCheckFastaFromParams:
    def test_no_warnings_for_approved_fasta(self):
        params = _Params(fasta_database="/some/path/ProteoBenchFASTA_DDAQuantification.fasta")
        assert check_fasta_from_params(params) == []

    def test_no_warnings_for_benchmark_fasta(self):
        params = _Params(fasta_database=r"C:\projects\BenchmarkFASTA_module2.fasta")
        assert check_fasta_from_params(params) == []

    def test_warning_for_unapproved_fasta(self):
        params = _Params(fasta_database="/some/path/uniprot_human.fasta")
        warnings = check_fasta_from_params(params)
        assert len(warnings) == 1
        assert "approved" in warnings[0].lower()

    def test_no_warnings_when_no_fasta_database(self):
        params = _Params()  # no fasta_database attribute
        assert check_fasta_from_params(params) == []

    def test_no_warnings_when_fasta_database_is_none(self):
        params = _Params(fasta_database=None)
        assert check_fasta_from_params(params) == []

    def test_windows_backslash_paths_handled(self):
        params = _Params(fasta_database=r"D:\data\ProteoBenchFASTA_DDA.fasta.fas")
        assert check_fasta_from_params(params) == []

    def test_custom_approved_patterns(self):
        params = _Params(fasta_database="/data/MyCustomFASTA.fasta")
        assert check_fasta_from_params(params, approved_patterns=["MyCustomFASTA"]) == []
        assert check_fasta_from_params(params, approved_patterns=["ProteoBenchFASTA"]) != []


# ===========================================================================
# check_fasta_from_results
# ===========================================================================


class TestCheckFastaFromResults:
    def test_no_warnings_when_all_species_present(self):
        df = _make_intermediate_df()  # YEAST, ECOLI, HUMAN all have True
        assert check_fasta_from_results(df) == []

    def test_warning_when_yeast_missing(self):
        df = _make_intermediate_df(
            yeast=[False, False, False, False],
            ecoli=[True, True, False, False],
            human=[False, False, True, True],
        )
        warnings = check_fasta_from_results(df)
        assert len(warnings) == 1
        assert "YEAST" in warnings[0]

    def test_warning_when_ecoli_missing(self):
        df = _make_intermediate_df(
            yeast=[True, True, False, False],
            ecoli=[False, False, False, False],
            human=[False, False, True, True],
        )
        warnings = check_fasta_from_results(df)
        assert len(warnings) == 1
        assert "ECOLI" in warnings[0]

    def test_no_warning_when_species_column_absent(self):
        # If the column is simply not present (e.g., non-mixed-species module)
        df = pd.DataFrame({"precursor ion": ["PEPTIDE/2"]})
        assert check_fasta_from_results(df) == []

    def test_custom_expected_species(self):
        df = pd.DataFrame(
            {
                "precursor ion": ["PEPTIDE/2"],
                "HUMAN": [True],
                "YEAST": [False],
            }
        )
        assert check_fasta_from_results(df, expected_species=["HUMAN"]) == []
        # YEAST column is present but has no True values → should warn
        assert check_fasta_from_results(df, expected_species=["YEAST"]) != []


# ===========================================================================
# validate_all (integration)
# ===========================================================================


class TestValidateAll:
    def test_no_warnings_for_consistent_params(self):
        params = _Params(
            min_precursor_charge=1,
            max_precursor_charge=4,
            min_peptide_length=5,
            max_peptide_length=30,
            fasta_database="/path/ProteoBenchFASTA_DDA.fasta",
        )
        df = _make_intermediate_df(
            precursor_ions=["PEPTIDE/2", "LONGPEPTIDER/3"],
            yeast=[True, False],
            ecoli=[False, True],
            human=[True, True],
        )
        assert validate_all(params, df) == []

    def test_collects_all_warnings(self):
        params = _Params(
            min_precursor_charge=2,
            max_precursor_charge=3,
            min_peptide_length=10,
            max_peptide_length=8,  # intentionally inconsistent (min>max to force both warnings)
            fasta_database="/path/uniprot_human.fasta",  # not approved
        )
        # charge 1 < min 2 → warning; length 7 < min 10 → warning; fasta → warning; no ECOLI → warning
        df = _make_intermediate_df(
            precursor_ions=["PEPTIDE/1"],  # charge 1, length 7
            yeast=[True],
            ecoli=[False],
            human=[True],
        )
        warnings = validate_all(params, df)
        assert len(warnings) >= 3  # charge, peptide length, fasta name, possibly ECOLI


# ===========================================================================
# Integration with real parameter parsers
# ===========================================================================


class TestFastaExtractionFragPipe:
    """Test that the FragPipe extractor populates fasta_database."""

    @pytest.mark.parametrize(
        "workflow_file",
        [
            "fragpipe.workflow",
            "fragpipe-version.workflow",
            "fragpipe_v22.workflow",
        ],
    )
    def test_fasta_database_extracted(self, workflow_file):
        from proteobench.io.params.fragger import extract_params

        path = os.path.join(TEST_PARAMS_DIR, workflow_file)
        if not os.path.isfile(path):
            pytest.skip(f"Test file not found: {path}")

        with open(path, "rb") as fh:
            params = extract_params(fh)

        assert hasattr(params, "fasta_database"), "fasta_database attribute missing"
        assert params.fasta_database is not None
        assert "ProteoBenchFASTA" in params.fasta_database or "BenchmarkFASTA" in params.fasta_database

    def test_fasta_passes_validation(self):
        from proteobench.io.params.fragger import extract_params

        path = os.path.join(TEST_PARAMS_DIR, "fragpipe.workflow")
        if not os.path.isfile(path):
            pytest.skip("Test file not found: fragpipe.workflow")

        with open(path, "rb") as fh:
            params = extract_params(fh)

        assert check_fasta_from_params(params) == []


class TestFastaExtractionMaxQuant:
    """Test that the MaxQuant extractor populates fasta_database."""

    @pytest.mark.parametrize(
        "xml_file",
        [
            "mqpar1.5.3.30_MBR.xml",
            "mqpar_MQ1.6.3.3_MBR.xml",
            "mqpar_MQ2.1.3.0_noMBR.xml",
        ],
    )
    def test_fasta_database_extracted(self, xml_file):
        from proteobench.io.params.maxquant import extract_params

        path = os.path.join(TEST_PARAMS_DIR, xml_file)
        if not os.path.isfile(path):
            pytest.skip(f"Test file not found: {path}")

        params = extract_params(path)

        assert hasattr(params, "fasta_database"), "fasta_database attribute missing"
        assert params.fasta_database is not None
