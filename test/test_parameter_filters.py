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
from webinterface.pages.base_pages.tabs.tab1_view_public_results import (
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

    def test_nan_values_filterable(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"fragment_mass_tolerance": [_NOT_SPECIFIED]},
        )
        assert len(result) == 1
        assert result.iloc[0]["id"] == "dp4"

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

    def test_select_slider_full_range(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"min_peptide_length": (7, 9)},
        )
        assert len(result) == 4

    def test_select_slider_partial_range(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"min_peptide_length": (8, 9)},
        )
        assert len(result) == 2
        assert set(result["id"]) == {"dp3", "dp4"}

    def test_select_slider_single_value_range(self, sample_datapoints):
        result = apply_parameter_filters(
            sample_datapoints,
            {"max_peptide_length": (50, 50)},
        )
        assert len(result) == 2
        assert set(result["id"]) == {"dp3", "dp4"}
