import datetime

import pytest
import pandas as pd
import numpy as np

from proteobench.datapoint.quant_datapoint import QuantDatapoint, filter_df_numquant_epsilon, filter_df_numquant_nr_prec

DATAPOINT_USER_INPUT_TYPE = {
    "DDA_MaxQuant": {
        "software_name": "MaxQuant",
        "software_version": "1.0",
        "search_engine_version": "1.0",
        "search_engine": "MaxQuant",
        "ident_fdr_psm": 0.01,
        "ident_fdr_peptide": 0.05,
        "ident_fdr_protein": 0.1,
        "enable_match_between_runs": 1,
        "precursor_mass_tolerance": "0.02 Da",
        "fragment_mass_tolerance": "0.02 Da",
        "enzyme": "Trypsin",
        "allowed_miscleavages": 1,
        "min_peptide_length": 6,
        "max_peptide_length": 30,
    },
    "DIA_DIA-NN": {
        "software_name": "DIA-NN",
        "software_version": "1.9",
        "search_engine_version": "1.9",
        "search_engine": "DIA-NN",
        "ident_fdr_peptide": 0.01,
        "ident_fdr_psm": 0.01,
        "ident_fdr_protein": 0.01,
        "enable_match_between_runs": 1,
        "enzyme": "Trypsin",
        "allowed_miscleavages": 1,
        "min_peptide_length": 6,
        "max_peptide_length": 40,
        "precursor_mass_tolerance": None,
        "fragment_mass_tolerance": None,
    },
}


class TestQuantDatapoint:
    @pytest.mark.parametrize("input_type", DATAPOINT_USER_INPUT_TYPE.keys())
    def test_Datapoint_constructor(self, input_type):
        input_format = DATAPOINT_USER_INPUT_TYPE[input_type]["software_name"]
        user_input = DATAPOINT_USER_INPUT_TYPE[input_type]
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        QuantDatapoint(
            id=input_format + "_" + user_input["software_version"] + "_" + formatted_datetime,
            software_name=input_format,
            software_version=user_input["software_version"],
            search_engine=user_input["search_engine"],
            search_engine_version=user_input["search_engine_version"],
            ident_fdr_psm=user_input["ident_fdr_psm"],
            ident_fdr_peptide=user_input["ident_fdr_peptide"],
            ident_fdr_protein=user_input["ident_fdr_protein"],
            enable_match_between_runs=user_input["enable_match_between_runs"],
            precursor_mass_tolerance=user_input["precursor_mass_tolerance"],
            fragment_mass_tolerance=user_input["fragment_mass_tolerance"],
            enzyme=user_input["enzyme"],
            allowed_miscleavages=user_input["allowed_miscleavages"],
            min_peptide_length=user_input["min_peptide_length"],
            max_peptide_length=user_input["max_peptide_length"],
        )

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        data = {
            "nr_observed": [1, 2, 3, 4, 5],
            "epsilon": [0.1, -0.2, 0.3, -0.4, 0.5],
            "CV_A": [0.1, 0.2, 0.3, 0.4, 0.5],
            "CV_B": [0.15, 0.25, 0.35, 0.45, 0.55],
        }
        return pd.DataFrame(data)

    def test_get_metrics(self, sample_dataframe):
        """Test the get_metrics method."""
        # Test with min_nr_observed = 1
        result = QuantDatapoint.get_metrics(sample_dataframe, min_nr_observed=1)
        assert 1 in result
        metrics = result[1]

        # Check all expected metrics are present
        expected_metrics = [
            "median_abs_epsilon",
            "mean_abs_epsilon",
            "variance_epsilon",
            "nr_prec",
            "CV_median",
            "CV_q75",
            "CV_q90",
            "CV_q95",
        ]
        for metric in expected_metrics:
            assert metric in metrics

        # Test with min_nr_observed = 3
        result = QuantDatapoint.get_metrics(sample_dataframe, min_nr_observed=3)
        assert 3 in result
        assert result[3]["nr_prec"] == 3  # Only 3 rows have nr_observed >= 3

    def test_get_metrics_edge_cases(self):
        """Test the get_metrics method with edge cases."""
        # Test with empty DataFrame
        empty_df = pd.DataFrame(columns=["nr_observed", "epsilon", "CV_A", "CV_B"])
        result = QuantDatapoint.get_metrics(empty_df)
        assert 1 in result
        assert result[1]["nr_prec"] == 0

        # Test with single row
        single_row_df = pd.DataFrame({"nr_observed": [1], "epsilon": [0.1], "CV_A": [0.1], "CV_B": [0.1]})
        result = QuantDatapoint.get_metrics(single_row_df)
        assert 1 in result
        assert result[1]["nr_prec"] == 1
        assert result[1]["median_abs_epsilon"] == 0.1

    def test_filter_df_numquant_epsilon(self):
        """Test the filter_df_numquant_epsilon function."""
        sample_row = {"3": {"median_abs_epsilon": 0.25, "mean_abs_epsilon": 0.3, "nr_prec": 100}}

        # Test with default parameters
        result = filter_df_numquant_epsilon(sample_row)
        assert result == 0.25

        # Test with different metric
        result = filter_df_numquant_epsilon(sample_row, metric="mean")
        assert result == 0.3

        # Test with invalid input
        result = filter_df_numquant_epsilon({})
        assert result is None

        # Test with string keys
        row_with_string = {"3": {"median_abs_epsilon": 0.25}}
        assert filter_df_numquant_epsilon(row_with_string) == 0.25

        # Test with missing metric
        row_missing_metric = {"3": {"mean_abs_epsilon": 0.3}}
        assert filter_df_numquant_epsilon(row_missing_metric, metric="median") is None

        # Test with None values
        row_with_none = {"3": None}
        assert filter_df_numquant_epsilon(row_with_none) is None
