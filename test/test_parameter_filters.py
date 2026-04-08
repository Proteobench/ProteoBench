"""Tests for the parameter-based filtering logic in tab1_view_public_results."""

import importlib
import sys
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# The webinterface package has transitive imports (streamlit_utils, streamlit)
# that are not available in the test environment. Mock them before importing.
sys.modules.setdefault("streamlit", MagicMock())
sys.modules.setdefault("streamlit_utils", MagicMock())

# Now we can import the pure-logic helpers from the module.
from webinterface.pages.base_pages.utils.parameter_filters import (
    _NOT_SPECIFIED,
    _get_unique_values,
    apply_parameter_filters,
)


@pytest.fixture
def sample_datapoints():
    """Create a sample DataFrame mimicking benchmark datapoints."""
    return pd.DataFrame(
        {
            "id": ["dp1", "dp2", "dp3", "dp4"],
            "software_name": ["MaxQuant", "Sage", "MaxQuant", "DIA-NN"],
            "enable_match_between_runs": [True, False, True, False],
            "search_engine": ["Andromeda", "Sage", "Andromeda", "DIA-NN"],
            "enzyme": ["Trypsin", "Trypsin", "Lys-C", "Trypsin"],
            "allowed_miscleavages": [2, 1, 2, 1],
            "ident_fdr_psm": [0.01, 0.01, 0.05, 0.01],
            "quantification_method": ["LFQ", "LFQ", "LFQ", "LFQ"],
            "precursor_mass_tolerance": ["20 ppm", "10 ppm", "20 ppm", "10 ppm"],
            "fragment_mass_tolerance": ["20 ppm", "20 ppm", "20 ppm", np.nan],
            "min_peptide_length": [7, 7, 8, 9],
            "max_peptide_length": [30, 40, 50, 50],
        }
    )


class TestGetUniqueValues:
    def test_sorts_values(self):
        s = pd.Series(["B", "A", "C", "A"])
        assert _get_unique_values(s) == ["A", "B", "C"]

    def test_nan_mapped_to_not_specified(self):
        s = pd.Series(["A", np.nan, "B"])
        vals = _get_unique_values(s)
        assert _NOT_SPECIFIED in vals
        assert "A" in vals
        assert "B" in vals

    def test_not_specified_sorted_last(self):
        s = pd.Series(["B", np.nan, "A"])
        vals = _get_unique_values(s)
        assert vals[-1] == _NOT_SPECIFIED

    def test_numeric_converted_to_str(self):
        s = pd.Series([0.01, 0.05, 0.01])
        vals = _get_unique_values(s)
        assert all(isinstance(v, str) for v in vals)
        assert len(vals) == 2


class TestApplyParameterFilters:
    def test_multiselect_filter(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"software_name": ["MaxQuant"]},
        )
        assert len(result) == 2
        assert set(result["software_name"]) == {"MaxQuant"}

    def test_multiselect_multiple_values(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"software_name": ["MaxQuant", "Sage"]},
        )
        assert len(result) == 3

    def test_radio_bool_enabled(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"enable_match_between_runs": "Enabled"},
        )
        assert len(result) == 2
        assert all(result["enable_match_between_runs"])

    def test_radio_bool_disabled(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"enable_match_between_runs": "Disabled"},
        )
        assert len(result) == 2
        assert not any(result["enable_match_between_runs"])

    def test_radio_bool_all(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"enable_match_between_runs": "All"},
        )
        assert len(result) == 4

    def test_multiple_filters_combined(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {
                "software_name": ["MaxQuant"],
                "enable_match_between_runs": "Enabled",
            },
        )
        assert len(result) == 2
        assert all(result["software_name"] == "MaxQuant")
        assert all(result["enable_match_between_runs"])

    def test_tolerance_range_filter(self, sample_datapoints):
        """Tolerance range slider restricts both min and max of each row."""
        # "20 ppm" → (-20, 20), "10 ppm" → (-10, 10)
        # Slider set to [-15, 15]: min=-20 < -15 fails, min=-10 >= -15 passes
        result = apply_parameter_filters(
            sample_datapoints,
            {"fragment_mass_tolerance__ppm": (-15.0, 15.0)},
        )
        # dp1-dp3 have "20 ppm" → min=-20 < -15 → excluded. dp4 has NaN → kept
        assert len(result) == 1
        assert result.iloc[0]["id"] == "dp4"

    def test_tolerance_range_auto_excluded(self, sample_datapoints):
        """Auto-calibration checkbox excludes those rows when False."""
        df = sample_datapoints.copy()
        df.loc[3, "fragment_mass_tolerance"] = "Automatic calibration"
        result = apply_parameter_filters(
            df,
            {"fragment_mass_tolerance__auto": False},
        )
        assert len(result) == 3
        assert "dp4" not in result["id"].values

    def test_tolerance_range_asymmetric(self):
        """Asymmetric tolerance windows: both min and max must fit in the slider range."""
        df = pd.DataFrame(
            {
                "id": ["a", "b", "c"],
                "precursor_mass_tolerance": [
                    "[-15 ppm, 10 ppm]",
                    "[-10 ppm, 10 ppm]",
                    "[-5 ppm, 20 ppm]",
                ],
            }
        )
        # Slider range [-12, 12]: a's min=-15 is out, c's max=20 is out
        result = apply_parameter_filters(
            df,
            {"precursor_mass_tolerance__ppm": (-12.0, 12.0)},
        )
        assert len(result) == 1
        assert result.iloc[0]["id"] == "b"

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["software_name", "enzyme"])
        result = apply_parameter_filters(empty_df, {"software_name": ["MaxQuant"]})
        assert result.empty

    def test_unknown_column_ignored(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"nonexistent_column": ["value"]},
        )
        assert len(result) == 4

    def test_no_selections_returns_all(self, sample_datapoints):
        result = apply_parameter_filters(sample_datapoints, {})
        assert len(result) == 4

    def test_filter_to_zero_rows(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"software_name": ["NonExistent"]},
        )
        assert len(result) == 0

    def test_combined_range_full(self, sample_datapoints):
        """Full range includes all datapoints."""
        result = apply_parameter_filters(
            sample_datapoints,
            {"min_peptide_length__max_peptide_length": (7, 50)},
        )
        assert len(result) == 4

    def test_combined_range_narrow(self, sample_datapoints):
        """Narrowing the range excludes datapoints outside it."""
        # dp1: min=7, max=30 -> included (7>=7, 30<=40)
        # dp2: min=7, max=40 -> included (7>=7, 40<=40)
        # dp3: min=8, max=50 -> excluded (50 > 40)
        # dp4: min=9, max=50 -> excluded (50 > 40)
        result = apply_parameter_filters(
            sample_datapoints,
            {"min_peptide_length__max_peptide_length": (7, 40)},
        )
        assert len(result) == 2
        assert set(result["id"]) == {"dp1", "dp2"}

    def test_combined_range_raise_lower_bound(self, sample_datapoints):
        """Raising the lower bound excludes datapoints with small min values."""
        # dp1: min=7 -> excluded (7 < 8)
        # dp2: min=7 -> excluded (7 < 8)
        # dp3: min=8, max=50 -> included
        # dp4: min=9, max=50 -> included
        result = apply_parameter_filters(
            sample_datapoints,
            {"min_peptide_length__max_peptide_length": (8, 50)},
        )
        assert len(result) == 2
        assert set(result["id"]) == {"dp3", "dp4"}

    def test_select_slider_range(self, sample_datapoints):
        """select_slider with range tuple works."""
        sample_datapoints["max_mods"] = [2, 3, 4, 5]
        result = apply_parameter_filters(
            sample_datapoints,
            {"max_mods": (2, 3)},
        )
        assert len(result) == 2
        assert set(result["id"]) == {"dp1", "dp2"}
