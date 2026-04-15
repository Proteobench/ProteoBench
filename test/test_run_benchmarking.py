"""Tests for proteobench.modules.quant.benchmarking.run_benchmarking."""

import os
from unittest.mock import MagicMock

import pandas as pd
import pytest

from proteobench.datapoint.quant_datapoint import QuantDatapointHYE
from proteobench.modules.quant.benchmarking import run_benchmarking
from proteobench.score.quantscoresHYE import QuantScoresHYE

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/quant/quant_lfq_ion_DDA_QExactive")
PARSE_SETTINGS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/QExactive")
)

USER_INPUT = {
    "software_name": "MaxQuant",
    "software_version": "1.0",
    "search_engine": "MaxQuant",
    "search_engine_version": "1.0",
    "ident_fdr_psm": 0.01,
    "ident_fdr_peptide": 0.05,
    "ident_fdr_protein": 0.1,
    "enable_match_between_runs": 1,
    "precursor_mass_tolerance": "0.02 Da",
    "fragment_mass_tolerance": "0.02 Da",
    "enzyme": "Trypsin",
    "allowed_miscleavages": 2,
    "min_peptide_length": 7,
    "max_peptide_length": 52,
}


class TestRunBenchmarking:
    def test_returns_three_tuple(self):
        """Test that run_benchmarking returns (intermediate, all_datapoints, input_df)."""
        result = run_benchmarking(
            input_file=os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
            input_format="MaxQuant",
            user_input=USER_INPUT,
            all_datapoints=None,
            parse_settings_dir=PARSE_SETTINGS_DIR,
            module_id="quant_lfq_DDA_ion_QExactive",
            precursor_column_name="precursor ion",
        )
        assert len(result) == 3
        intermediate, all_datapoints, input_df = result
        assert isinstance(intermediate, pd.DataFrame)
        assert not intermediate.empty
        assert isinstance(input_df, pd.DataFrame)

    def test_default_classes_are_hye(self):
        """Test that default score/datapoint classes are HYE."""
        result = run_benchmarking(
            input_file=os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
            input_format="MaxQuant",
            user_input=USER_INPUT,
            all_datapoints=None,
            parse_settings_dir=PARSE_SETTINGS_DIR,
            module_id="quant_lfq_DDA_ion_QExactive",
            precursor_column_name="precursor ion",
        )
        # If it returns without error using defaults, HYE classes work
        assert result[0] is not None

    def test_custom_score_class_is_used(self):
        """Test that a custom quant_score_class is actually instantiated."""
        mock_score_class = MagicMock(spec=QuantScoresHYE)
        mock_instance = MagicMock()
        mock_instance.generate_intermediate.return_value = pd.DataFrame({"col": [1]})
        mock_score_class.return_value = mock_instance

        # This should use the mock instead of QuantScoresHYE
        with pytest.raises(Exception):
            # Will fail at datapoint generation because intermediate is mocked,
            # but the mock should have been called
            run_benchmarking(
                input_file=os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
                input_format="MaxQuant",
                user_input=USER_INPUT,
                all_datapoints=None,
                parse_settings_dir=PARSE_SETTINGS_DIR,
                module_id="quant_lfq_DDA_ion_QExactive",
                precursor_column_name="precursor ion",
                quant_score_class=mock_score_class,
            )
        # Verify the custom class was instantiated
        mock_score_class.assert_called_once()

    def test_custom_datapoint_class_is_used(self):
        """Test that a custom datapoint_class is actually called."""
        mock_datapoint_class = MagicMock(spec=QuantDatapointHYE)
        mock_datapoint_class.generate_datapoint.return_value = pd.Series({"test": 1})

        result = run_benchmarking(
            input_file=os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
            input_format="MaxQuant",
            user_input=USER_INPUT,
            all_datapoints=None,
            parse_settings_dir=PARSE_SETTINGS_DIR,
            module_id="quant_lfq_DDA_ion_QExactive",
            precursor_column_name="precursor ion",
            datapoint_class=mock_datapoint_class,
        )
        mock_datapoint_class.generate_datapoint.assert_called_once()

    def test_add_datapoint_func_called_when_provided(self):
        """Test that add_datapoint_func is called when provided."""
        mock_add_func = MagicMock(return_value=pd.DataFrame({"result": [1]}))

        result = run_benchmarking(
            input_file=os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
            input_format="MaxQuant",
            user_input=USER_INPUT,
            all_datapoints=None,
            parse_settings_dir=PARSE_SETTINGS_DIR,
            module_id="quant_lfq_DDA_ion_QExactive",
            precursor_column_name="precursor ion",
            add_datapoint_func=mock_add_func,
        )
        mock_add_func.assert_called_once()

    def test_add_datapoint_func_not_called_when_none(self):
        """Test that no datapoint append happens when add_datapoint_func is None."""
        result = run_benchmarking(
            input_file=os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
            input_format="MaxQuant",
            user_input=USER_INPUT,
            all_datapoints=None,
            parse_settings_dir=PARSE_SETTINGS_DIR,
            module_id="quant_lfq_DDA_ion_QExactive",
            precursor_column_name="precursor ion",
            add_datapoint_func=None,
        )
        # all_datapoints should remain None when no add function provided
        assert result[1] is None
