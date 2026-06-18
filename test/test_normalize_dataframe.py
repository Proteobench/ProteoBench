"""Tests for normalize_dataframe_columns() — DataFrame-level parameter coercion."""

import numpy as np
import pandas as pd
import pytest

from proteobench.io.params import normalize_dataframe_columns


def _make_df(data: dict) -> pd.DataFrame:
    """Build a single-row (or multi-row) DataFrame from *data*."""
    return pd.DataFrame(data)


class TestFloatCoercion:
    def test_fdr_string_to_float(self):
        df = _make_df({"ident_fdr_psm": ["0.05", "0.01"]})
        result = normalize_dataframe_columns(df)
        assert result["ident_fdr_psm"].tolist() == pytest.approx([0.05, 0.01])

    def test_fdr_percentage_divided(self):
        df = _make_df({"ident_fdr_psm": [1, 5]})
        result = normalize_dataframe_columns(df)
        assert result["ident_fdr_psm"].tolist() == pytest.approx([0.01, 0.05])

    def test_fdr_nan_preserved(self):
        df = _make_df({"ident_fdr_psm": [0.01, np.nan]})
        result = normalize_dataframe_columns(df)
        assert result["ident_fdr_psm"].iloc[0] == pytest.approx(0.01)
        assert pd.isna(result["ident_fdr_psm"].iloc[1])


class TestIntCoercion:
    def test_string_to_int(self):
        df = _make_df({"allowed_miscleavages": ["2", "3"]})
        result = normalize_dataframe_columns(df)
        assert result["allowed_miscleavages"].tolist() == [2, 3]

    def test_float_to_int(self):
        df = _make_df({"min_peptide_length": [7.0, 8.0]})
        result = normalize_dataframe_columns(df)
        assert result["min_peptide_length"].tolist() == [7, 8]

    def test_mixed_types(self):
        df = _make_df({"max_peptide_length": [30, "40", 50.0]})
        result = normalize_dataframe_columns(df)
        assert result["max_peptide_length"].tolist() == [30, 40, 50]

    def test_nan_preserved_as_nullable_int(self):
        df = _make_df({"min_precursor_charge": [2, np.nan, 4]})
        result = normalize_dataframe_columns(df)
        assert result["min_precursor_charge"].dtype == pd.Int64Dtype()
        assert pd.isna(result["min_precursor_charge"].iloc[1])
        assert result["min_precursor_charge"].iloc[0] == 2


class TestBoolCoercion:
    def test_string_true(self):
        df = _make_df({"enable_match_between_runs": ["true", "True", "1", "yes"]})
        result = normalize_dataframe_columns(df)
        assert all(result["enable_match_between_runs"])

    def test_string_false(self):
        df = _make_df({"enable_match_between_runs": ["false", "False", "0", "no"]})
        result = normalize_dataframe_columns(df)
        assert not any(result["enable_match_between_runs"])

    def test_bool_stays(self):
        df = _make_df({"enable_match_between_runs": [True, False]})
        result = normalize_dataframe_columns(df)
        assert result["enable_match_between_runs"].tolist() == [True, False]


class TestMissingSentinels:
    def test_sentinels_become_nan(self):
        df = _make_df({"enzyme": ["not specified", "N/A", "None", ""]})
        result = normalize_dataframe_columns(df)
        assert result["enzyme"].isna().all()

    def test_sentinel_on_int_field(self):
        df = _make_df({"allowed_miscleavages": ["not specified", "2"]})
        result = normalize_dataframe_columns(df)
        assert pd.isna(result["allowed_miscleavages"].iloc[0])
        assert result["allowed_miscleavages"].iloc[1] == 2


class TestEnzymeNormalization:
    def test_lowercase_mapped(self):
        df = _make_df({"enzyme": ["trypsin", "lys-c", "Trypsin/P"]})
        result = normalize_dataframe_columns(df)
        assert result["enzyme"].tolist() == ["Trypsin", "Lys-C", "Trypsin/P"]

    def test_unknown_kept(self):
        df = _make_df({"enzyme": ["CustomEnzyme"]})
        result = normalize_dataframe_columns(df)
        assert result["enzyme"].iloc[0] == "CustomEnzyme"


class TestToleranceNormalization:
    @pytest.mark.parametrize("val", ["Dynamic", "dynamic", "Auto Detected", "0", "0 ppm"])
    def test_auto_calibration_mapped(self, val):
        df = _make_df({"precursor_mass_tolerance": [val]})
        result = normalize_dataframe_columns(df)
        assert result["precursor_mass_tolerance"].iloc[0] == "Automatic calibration"

    def test_fragment_tolerance_mapped(self):
        df = _make_df({"fragment_mass_tolerance": ["Dynamic", "[-0.02 Da, 0.02 Da]"]})
        result = normalize_dataframe_columns(df)
        assert result["fragment_mass_tolerance"].iloc[0] == "Automatic calibration"
        assert result["fragment_mass_tolerance"].iloc[1] == "[-0.02 Da, 0.02 Da]"

    def test_integer_zero_mapped(self):
        df = _make_df({"precursor_mass_tolerance": [0, "[-10 ppm, 10 ppm]"]})
        result = normalize_dataframe_columns(df)
        assert result["precursor_mass_tolerance"].iloc[0] == "Automatic calibration"
        assert result["precursor_mass_tolerance"].iloc[1] == "[-10 ppm, 10 ppm]"

    def test_normal_value_kept(self):
        df = _make_df({"precursor_mass_tolerance": ["[-10 ppm, 10 ppm]"]})
        result = normalize_dataframe_columns(df)
        assert result["precursor_mass_tolerance"].iloc[0] == "[-10 ppm, 10 ppm]"


class TestMissingColumns:
    def test_columns_not_present_are_ignored(self):
        df = _make_df({"some_other_col": [1, 2, 3]})
        result = normalize_dataframe_columns(df)
        assert result["some_other_col"].tolist() == [1, 2, 3]


class TestFullRow:
    """Simulate a row similar to what comes from historical JSON data."""

    def test_mixed_historical_row(self):
        df = _make_df(
            {
                "ident_fdr_psm": ["1"],
                "allowed_miscleavages": ["2"],
                "min_peptide_length": ["7"],
                "max_peptide_length": ["50"],
                "enable_match_between_runs": ["true"],
                "enzyme": ["trypsin"],
                "search_engine": ["CHIMERYS"],
            }
        )
        result = normalize_dataframe_columns(df)
        assert result["ident_fdr_psm"].iloc[0] == pytest.approx(0.01)
        assert result["allowed_miscleavages"].iloc[0] == 2
        assert result["min_peptide_length"].iloc[0] == 7
        assert result["max_peptide_length"].iloc[0] == 50
        assert result["enable_match_between_runs"].iloc[0] == True
        assert result["enzyme"].iloc[0] == "Trypsin"
        assert result["search_engine"].iloc[0] == "CHIMERYS"
