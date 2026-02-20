import datetime

import numpy as np
import pandas as pd
import pytest

from proteobench.datapoint.quant_datapoint import (
    QuantDatapointHYE,
    _detect_unchanged_species,
    compute_roc_auc,
    filter_df_numquant_epsilon,
    filter_df_numquant_nr_feature,
)
from proteobench.score.quantscores import QuantScoresHYE

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

        QuantDatapointHYE(
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
        # HUMAN log2_A_vs_B: [0.1, -0.1, 0.05] -> median=0.05, mean=0.0167
        # YEAST log2_A_vs_B: [1.0, 0.9] -> median=0.95, mean=0.95
        human_median, human_mean = 0.05, (0.1 + -0.1 + 0.05) / 3
        yeast_median, yeast_mean = 0.95, 0.95
        data = {
            "nr_observed": [1, 2, 3, 4, 5],
            "epsilon": [0.1, -0.2, 0.3, -0.4, 0.5],
            "CV_A": [0.1, 0.2, 0.3, 0.4, 0.5],
            "CV_B": [0.15, 0.25, 0.35, 0.45, 0.55],
            "species": ["HUMAN", "YEAST", "HUMAN", "YEAST", "HUMAN"],
            "log2_A_vs_B": [0.1, 1.0, -0.1, 0.9, 0.05],  # HUMAN ~0, YEAST ~1
            "log2_expectedRatio": [0.0, 1.0, 0.0, 1.0, 0.0],  # HUMAN=1:1, YEAST=2:1
            # epsilon_precision: deviation from per-species empirical center
            "epsilon_precision_median": [
                0.1 - human_median,  # HUMAN
                1.0 - yeast_median,  # YEAST
                -0.1 - human_median,  # HUMAN
                0.9 - yeast_median,  # YEAST
                0.05 - human_median,  # HUMAN
            ],
            "epsilon_precision_mean": [
                0.1 - human_mean,  # HUMAN
                1.0 - yeast_mean,  # YEAST
                -0.1 - human_mean,  # HUMAN
                0.9 - yeast_mean,  # YEAST
                0.05 - human_mean,  # HUMAN
            ],
        }
        return pd.DataFrame(data)

    def test_get_metrics(self, sample_dataframe):
        """Test the get_metrics method."""
        # Test with min_nr_observed = 1
        result = QuantDatapointHYE.get_metrics(sample_dataframe, min_nr_observed=1)
        assert 1 in result
        metrics = result[1]

        # Check all expected metrics are present (with new naming convention)
        expected_metrics = [
            "median_abs_epsilon_global",
            "mean_abs_epsilon_global",
            "median_abs_epsilon_eq_species",
            "mean_abs_epsilon_eq_species",
            "median_abs_epsilon_precision_global",
            "mean_abs_epsilon_precision_global",
            "median_abs_epsilon_precision_eq_species",
            "mean_abs_epsilon_precision_eq_species",
            "variance_epsilon_global",
            "nr_feature",
            "CV_median",
            "CV_q75",
            "CV_q90",
            "CV_q95",
            "roc_auc",
        ]
        for metric in expected_metrics:
            assert metric in metrics

        # Test with min_nr_observed = 3
        result = QuantDatapointHYE.get_metrics(sample_dataframe, min_nr_observed=3)
        assert 3 in result
        assert result[3]["nr_feature"] == 3  # Only 3 rows have nr_observed >= 3

    def test_get_metrics_edge_cases(self):
        """Test the get_metrics method with edge cases."""
        # Test with empty DataFrame
        empty_df = pd.DataFrame(
            columns=[
                "nr_observed",
                "epsilon",
                "CV_A",
                "CV_B",
                "species",
                "log2_A_vs_B",
                "log2_expectedRatio",
                "epsilon_precision_median",
                "epsilon_precision_mean",
            ]
        )
        result = QuantDatapointHYE.get_metrics(empty_df)
        assert 1 in result
        assert result[1]["nr_feature"] == 0

        # Test with single row - epsilon_precision is 0 when there's only one value per species
        single_row_df = pd.DataFrame(
            {
                "nr_observed": [1],
                "epsilon": [0.1],
                "CV_A": [0.1],
                "CV_B": [0.1],
                "species": ["HUMAN"],
                "log2_A_vs_B": [0.1],
                "log2_expectedRatio": [0.0],
                "epsilon_precision_median": [0.0],  # Single value = 0 deviation from median
                "epsilon_precision_mean": [0.0],  # Single value = 0 deviation from mean
            }
        )
        result = QuantDatapointHYE.get_metrics(single_row_df)
        assert 1 in result
        assert result[1]["nr_feature"] == 1
        assert result[1]["median_abs_epsilon_global"] == 0.1
        assert result[1]["median_abs_epsilon_precision_global"] == 0.0  # No deviation from self

    def test_filter_df_numquant_epsilon(self):
        """Test the filter_df_numquant_epsilon function."""
        sample_row = {"3": {"median_abs_epsilon": 0.25, "mean_abs_epsilon": 0.3, "nr_feature": 100}}

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

    def test_compute_roc_auc(self):
        """Test the compute_roc_auc function."""
        # Test with well-separated species (HUMAN ~0, YEAST ~1, ECOLI ~-2)
        data = {
            "log2_A_vs_B": [0.1, -0.1, 1.1, 0.9, -1.8, -2.2],
            "species": ["HUMAN", "HUMAN", "YEAST", "YEAST", "ECOLI", "ECOLI"],
            "log2_expectedRatio": [0.0, 0.0, 1.0, 1.0, -2.0, -2.0],  # HUMAN=1:1, YEAST=2:1, ECOLI=0.25:1
        }
        df = pd.DataFrame(data)
        # Test with explicit unchanged_species
        auc = compute_roc_auc(df, unchanged_species="HUMAN")
        assert auc > 0.8  # Should separate well since HUMAN has low |log2| and others have high

        # Test auto-detection of unchanged species
        auc_auto = compute_roc_auc(df)  # Should auto-detect HUMAN as unchanged
        assert auc_auto > 0.8
        assert auc == auc_auto  # Same result

    def test_compute_roc_auc_edge_cases(self):
        """Test compute_roc_auc with edge cases."""
        # Test with missing columns
        df_no_species = pd.DataFrame({"log2_A_vs_B": [0.1, 0.2]})
        assert np.isnan(compute_roc_auc(df_no_species))

        df_no_log2 = pd.DataFrame({"species": ["HUMAN", "YEAST"]})
        assert np.isnan(compute_roc_auc(df_no_log2))

        # Test with empty DataFrame
        empty_df = pd.DataFrame(columns=["log2_A_vs_B", "species"])
        assert np.isnan(compute_roc_auc(empty_df))

        # Test with single class (only HUMAN)
        single_class_df = pd.DataFrame(
            {
                "log2_A_vs_B": [0.1, 0.2, 0.3],
                "species": ["HUMAN", "HUMAN", "HUMAN"],
            }
        )
        assert np.isnan(compute_roc_auc(single_class_df))

    def test_compute_roc_auc_two_species(self):
        """Test compute_roc_auc with two species (like singlecell module)."""
        # Simulate 2-species scenario (singlecell: HUMAN=1.2, YEAST=0.2)
        data = {
            "log2_A_vs_B": [0.1, -0.05, 0.15, -1.5, -1.8, -1.2],
            "species": ["HUMAN", "HUMAN", "HUMAN", "YEAST", "YEAST", "YEAST"],
            "log2_expectedRatio": [0.263, 0.263, 0.263, -2.322, -2.322, -2.322],  # log2(1.2), log2(0.2)
        }
        df = pd.DataFrame(data)
        # HUMAN has smaller |log2_expectedRatio|, so it's the "unchanged" species
        auc = compute_roc_auc(df)  # Auto-detect HUMAN as unchanged
        assert auc > 0.9  # Should separate very well

    def test_compute_roc_auc_bounds(self):
        """Test that ROC-AUC is always between 0 and 1."""
        # Test with random data - ROC-AUC should always be in [0, 1]
        np.random.seed(42)
        for _ in range(10):
            n = 100
            data = {
                "log2_A_vs_B": np.random.normal(0, 1, n),
                "species": np.random.choice(["HUMAN", "YEAST", "ECOLI"], n),
            }
            df = pd.DataFrame(data)
            auc = compute_roc_auc(df, unchanged_species="HUMAN")
            if not np.isnan(auc):
                assert 0.0 <= auc <= 1.0, f"ROC-AUC {auc} out of bounds [0, 1]"

    def test_detect_unchanged_species(self):
        """Test the _detect_unchanged_species function."""
        # Standard 3-species: HUMAN=1:1, YEAST=2:1, ECOLI=0.25:1
        data = {
            "species": ["HUMAN", "YEAST", "ECOLI"],
            "log2_expectedRatio": [0.0, 1.0, -2.0],
        }
        df = pd.DataFrame(data)
        assert _detect_unchanged_species(df) == "HUMAN"

        # Singlecell 2-species: HUMAN=1.2, YEAST=0.2
        data_sc = {
            "species": ["HUMAN", "YEAST"],
            "log2_expectedRatio": [0.263, -2.322],  # log2(1.2), log2(0.2)
        }
        df_sc = pd.DataFrame(data_sc)
        assert _detect_unchanged_species(df_sc) == "HUMAN"

        # Edge case: missing columns
        df_no_cols = pd.DataFrame({"species": ["HUMAN"]})
        assert _detect_unchanged_species(df_no_cols) is None

        # Edge case: empty DataFrame
        df_empty = pd.DataFrame(columns=["species", "log2_expectedRatio"])
        assert _detect_unchanged_species(df_empty) is None


class TestEpsilonPrecision:
    """Tests for epsilon precision computation (deviation from empirical center)."""

    def test_epsilon_precision_reduces_when_bias_exists(self):
        """Test that precision metrics are smaller than accuracy metrics when bias exists.

        When the empirical center differs from the expected ratio (bias),
        precision metrics (deviation from empirical center) should be smaller
        than accuracy metrics (deviation from expected ratio).
        """
        # Scenario: HUMAN expected=0, but observed values centered at 0.3 (bias=0.3)
        # Accuracy: measures deviation from 0 -> larger values
        # Precision: measures deviation from 0.3 -> smaller values
        np.random.seed(42)
        n = 50

        human_values = np.random.normal(0.3, 0.1, n)  # Centered at 0.3, expected 0
        yeast_values = np.random.normal(0.7, 0.1, n)  # Centered at 0.7, expected 1

        human_prec_median = human_values - np.median(human_values)
        yeast_prec_median = yeast_values - np.median(yeast_values)
        human_prec_mean = human_values - np.mean(human_values)
        yeast_prec_mean = yeast_values - np.mean(yeast_values)

        data = {
            "nr_observed": [3] * (2 * n),
            "epsilon": list(human_values - 0.0) + list(yeast_values - 1.0),  # Deviation from expected
            "CV_A": [0.1] * (2 * n),
            "CV_B": [0.1] * (2 * n),
            "species": ["HUMAN"] * n + ["YEAST"] * n,
            "log2_A_vs_B": list(human_values) + list(yeast_values),
            "log2_expectedRatio": [0.0] * n + [1.0] * n,
            "epsilon_precision_median": list(human_prec_median) + list(yeast_prec_median),
            "epsilon_precision_mean": list(human_prec_mean) + list(yeast_prec_mean),
        }
        df = pd.DataFrame(data)

        result = QuantDatapointHYE.get_metrics(df, min_nr_observed=1)
        metrics = result[1]

        # Precision should be smaller than accuracy due to bias
        assert metrics["median_abs_epsilon_precision_global"] < metrics["median_abs_epsilon_global"]
        assert metrics["mean_abs_epsilon_precision_global"] < metrics["mean_abs_epsilon_global"]

        # Verify significant reduction (at least 50% since we have bias=0.3 with std=0.1)
        reduction = 1 - metrics["median_abs_epsilon_precision_global"] / metrics["median_abs_epsilon_global"]
        assert reduction > 0.5, f"Expected >50% reduction, got {reduction*100:.1f}%"

    def test_epsilon_precision_equals_accuracy_when_no_bias(self):
        """Test that precision equals accuracy when empirical center equals expected ratio."""
        # Scenario: observed values are centered exactly at expected ratio (no bias)
        np.random.seed(42)
        n = 50

        # Values centered exactly at expected ratios
        human_values = np.random.normal(0.0, 0.1, n)  # Centered at 0 (expected=0)
        yeast_values = np.random.normal(1.0, 0.1, n)  # Centered at 1 (expected=1)

        human_prec_median = human_values - np.median(human_values)
        yeast_prec_median = yeast_values - np.median(yeast_values)
        human_prec_mean = human_values - np.mean(human_values)
        yeast_prec_mean = yeast_values - np.mean(yeast_values)

        data = {
            "nr_observed": [3] * (2 * n),
            "epsilon": list(human_values - 0.0) + list(yeast_values - 1.0),
            "CV_A": [0.1] * (2 * n),
            "CV_B": [0.1] * (2 * n),
            "species": ["HUMAN"] * n + ["YEAST"] * n,
            "log2_A_vs_B": list(human_values) + list(yeast_values),
            "log2_expectedRatio": [0.0] * n + [1.0] * n,
            "epsilon_precision_median": list(human_prec_median) + list(yeast_prec_median),
            "epsilon_precision_mean": list(human_prec_mean) + list(yeast_prec_mean),
        }
        df = pd.DataFrame(data)

        result = QuantDatapointHYE.get_metrics(df, min_nr_observed=1)
        metrics = result[1]

        # With no bias, precision and accuracy should be approximately equal
        # (small difference due to median vs mean of small sample)
        ratio = metrics["mean_abs_epsilon_precision_global"] / metrics["mean_abs_epsilon_global"]
        assert 0.8 < ratio < 1.2, f"Expected ratio ~1.0, got {ratio:.2f}"

    def test_epsilon_precision_per_species_calculation(self):
        """Test that epsilon precision is computed per-species, not globally."""
        # Two species with very different centers
        # If computed globally, precision would be wrong
        data = {
            "nr_observed": [3, 3, 3, 3],
            "epsilon": [0.1, 0.1, -0.9, -0.9],  # HUMAN: 0.1-0=0.1, YEAST: 0.1-1=-0.9
            "CV_A": [0.1, 0.1, 0.1, 0.1],
            "CV_B": [0.1, 0.1, 0.1, 0.1],
            "species": ["HUMAN", "HUMAN", "YEAST", "YEAST"],
            "log2_A_vs_B": [0.1, 0.2, 0.1, 0.2],  # HUMAN: 0.1, 0.2; YEAST: 0.1, 0.2
            "log2_expectedRatio": [0.0, 0.0, 1.0, 1.0],
            # Per-species epsilon precision:
            # HUMAN median=0.15: 0.1-0.15=-0.05, 0.2-0.15=0.05
            # YEAST median=0.15: 0.1-0.15=-0.05, 0.2-0.15=0.05
            "epsilon_precision_median": [-0.05, 0.05, -0.05, 0.05],
            "epsilon_precision_mean": [-0.05, 0.05, -0.05, 0.05],
        }
        df = pd.DataFrame(data)

        result = QuantDatapointHYE.get_metrics(df, min_nr_observed=1)
        metrics = result[1]

        # All precision values are 0.05 (abs), so median/mean should be 0.05
        assert np.isclose(metrics["median_abs_epsilon_precision_global"], 0.05)
        assert np.isclose(metrics["mean_abs_epsilon_precision_global"], 0.05)

        # Accuracy: HUMAN eps=[0.1, 0.2], YEAST eps=[-0.9, -0.8]
        # Absolute values: [0.1, 0.2, 0.9, 0.8] -> median=0.5, mean=0.5
        assert np.isclose(metrics["median_abs_epsilon_global"], 0.5)
        assert np.isclose(metrics["mean_abs_epsilon_global"], 0.5)

    def test_epsilon_precision_eq_species_weighting(self):
        """Test that eq_species metrics weight each species equally."""
        # HUMAN: 100 precursors with small epsilon
        # YEAST: 10 precursors with large epsilon
        # Global: dominated by HUMAN (90% of data)
        # Eq_species: HUMAN and YEAST contribute equally
        np.random.seed(42)

        n_human = 100
        n_yeast = 10

        human_values = np.random.normal(0.0, 0.05, n_human)  # Small spread
        yeast_values = np.random.normal(1.0, 0.3, n_yeast)  # Large spread

        human_prec = human_values - np.median(human_values)
        yeast_prec = yeast_values - np.median(yeast_values)

        data = {
            "nr_observed": [3] * (n_human + n_yeast),
            "epsilon": list(human_values) + list(yeast_values - 1.0),
            "CV_A": [0.1] * (n_human + n_yeast),
            "CV_B": [0.1] * (n_human + n_yeast),
            "species": ["HUMAN"] * n_human + ["YEAST"] * n_yeast,
            "log2_A_vs_B": list(human_values) + list(yeast_values),
            "log2_expectedRatio": [0.0] * n_human + [1.0] * n_yeast,
            "epsilon_precision_median": list(human_prec) + list(yeast_prec),
            "epsilon_precision_mean": list(human_values - np.mean(human_values))
            + list(yeast_values - np.mean(yeast_values)),
        }
        df = pd.DataFrame(data)

        result = QuantDatapointHYE.get_metrics(df, min_nr_observed=1)
        metrics = result[1]

        # eq_species should be larger than global because YEAST has high spread
        # and gets equal weight (50%) instead of proportional (10%)
        assert metrics["median_abs_epsilon_precision_eq_species"] > metrics["median_abs_epsilon_precision_global"]


class TestQuantScoresComputeEpsilon:
    """Tests for QuantScores.compute_epsilon - the source of epsilon precision computation."""

    def test_compute_epsilon_creates_precision_columns(self):
        """Test that compute_epsilon creates epsilon_precision_median and epsilon_precision_mean columns."""
        species_expected_ratio = {
            "HUMAN": {"A_vs_B": 1.0},  # log2 = 0
            "YEAST": {"A_vs_B": 2.0},  # log2 = 1
        }

        df = pd.DataFrame(
            {
                "log2_A_vs_B": [0.1, 0.2, 0.9, 1.1],
                "HUMAN": [True, True, False, False],
                "YEAST": [False, False, True, True],
            }
        )

        result = QuantScoresHYE.compute_epsilon(df, species_expected_ratio)

        assert "epsilon_precision_median" in result.columns
        assert "epsilon_precision_mean" in result.columns
        assert "log2_empirical_median" in result.columns
        assert "log2_empirical_mean" in result.columns

    def test_compute_epsilon_precision_is_per_species(self):
        """Test that epsilon precision is computed per-species, not globally."""
        species_expected_ratio = {
            "HUMAN": {"A_vs_B": 1.0},  # log2 = 0
            "YEAST": {"A_vs_B": 2.0},  # log2 = 1
        }

        # HUMAN: values [0.1, 0.2, 0.3] -> median=0.2, mean=0.2
        # YEAST: values [0.8, 1.0, 1.2] -> median=1.0, mean=1.0
        df = pd.DataFrame(
            {
                "log2_A_vs_B": [0.1, 0.2, 0.3, 0.8, 1.0, 1.2],
                "HUMAN": [True, True, True, False, False, False],
                "YEAST": [False, False, False, True, True, True],
            }
        )

        result = QuantScoresHYE.compute_epsilon(df, species_expected_ratio)

        # Check per-species empirical centers
        human_rows = result[result["species"] == "HUMAN"]
        yeast_rows = result[result["species"] == "YEAST"]

        assert np.allclose(human_rows["log2_empirical_median"].values, 0.2)
        assert np.allclose(human_rows["log2_empirical_mean"].values, 0.2)
        assert np.allclose(yeast_rows["log2_empirical_median"].values, 1.0)
        assert np.allclose(yeast_rows["log2_empirical_mean"].values, 1.0)

        # Check epsilon precision values
        # HUMAN: 0.1-0.2=-0.1, 0.2-0.2=0, 0.3-0.2=0.1
        expected_human_prec = [-0.1, 0.0, 0.1]
        assert np.allclose(human_rows["epsilon_precision_median"].values, expected_human_prec)

        # YEAST: 0.8-1.0=-0.2, 1.0-1.0=0, 1.2-1.0=0.2
        expected_yeast_prec = [-0.2, 0.0, 0.2]
        assert np.allclose(yeast_rows["epsilon_precision_median"].values, expected_yeast_prec)

    def test_compute_epsilon_vs_epsilon_precision_with_bias(self):
        """Test that epsilon and epsilon_precision differ when there's bias."""
        species_expected_ratio = {
            "HUMAN": {"A_vs_B": 1.0},  # log2 = 0 (expected)
        }

        # HUMAN values centered at 0.5 instead of expected 0 (bias = 0.5)
        df = pd.DataFrame(
            {
                "log2_A_vs_B": [0.4, 0.5, 0.6],  # Centered at 0.5
                "HUMAN": [True, True, True],
            }
        )

        result = QuantScoresHYE.compute_epsilon(df, species_expected_ratio)

        # Epsilon (accuracy): deviation from expected (0)
        # Values: 0.4-0=0.4, 0.5-0=0.5, 0.6-0=0.6
        expected_epsilon = [0.4, 0.5, 0.6]
        assert np.allclose(result["epsilon"].values, expected_epsilon)

        # Epsilon precision: deviation from empirical median (0.5)
        # Values: 0.4-0.5=-0.1, 0.5-0.5=0, 0.6-0.5=0.1
        expected_precision = [-0.1, 0.0, 0.1]
        assert np.allclose(result["epsilon_precision_median"].values, expected_precision)

        # Precision abs values should be much smaller than accuracy abs values
        assert np.abs(result["epsilon_precision_median"]).mean() < np.abs(result["epsilon"]).mean()

    def test_compute_epsilon_three_species(self):
        """Test epsilon precision with three species (standard benchmark scenario)."""
        species_expected_ratio = {
            "HUMAN": {"A_vs_B": 1.0},  # log2 = 0
            "YEAST": {"A_vs_B": 2.0},  # log2 = 1
            "ECOLI": {"A_vs_B": 0.25},  # log2 = -2
        }

        np.random.seed(42)
        n = 20

        # Each species has some bias from expected ratio
        human_values = np.random.normal(0.1, 0.05, n)  # Bias +0.1
        yeast_values = np.random.normal(1.1, 0.08, n)  # Bias +0.1
        ecoli_values = np.random.normal(-1.9, 0.06, n)  # Bias +0.1

        df = pd.DataFrame(
            {
                "log2_A_vs_B": list(human_values) + list(yeast_values) + list(ecoli_values),
                "HUMAN": [True] * n + [False] * n + [False] * n,
                "YEAST": [False] * n + [True] * n + [False] * n,
                "ECOLI": [False] * n + [False] * n + [True] * n,
            }
        )

        result = QuantScoresHYE.compute_epsilon(df, species_expected_ratio)

        # Each species should have precision values centered around 0
        for species in ["HUMAN", "YEAST", "ECOLI"]:
            sp_data = result[result["species"] == species]
            prec_mean = sp_data["epsilon_precision_median"].abs().mean()
            acc_mean = sp_data["epsilon"].abs().mean()
            # Precision should be smaller than accuracy due to bias
            assert prec_mean < acc_mean, f"{species}: precision {prec_mean:.3f} not < accuracy {acc_mean:.3f}"
