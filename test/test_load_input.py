"""Tests for proteobench.io.parsing.load_input — vendor file loading."""

import os

import pandas as pd
import pytest

from proteobench.io.parsing.load_input import _LOAD_FUNCTIONS, load_input_file

TESTDATA_DIR_DDA = os.path.join(os.path.dirname(__file__), "data/quant/quant_lfq_ion_DDA_QExactive")
TESTDATA_DIR_DIA = os.path.join(os.path.dirname(__file__), "data/quant/quant_lfq_ion_DIA_AIF")


# Map format names to test data files that exist
TESTDATA_FILES = {
    "MaxQuant": os.path.join(TESTDATA_DIR_DDA, "MaxQuant_evidence_sample.txt"),
    "FragPipe": os.path.join(TESTDATA_DIR_DDA, "FragPipe_MSFragger_combined_ion.tsv"),
    "Sage": os.path.join(TESTDATA_DIR_DDA, "sage_sample_input_lfq.tsv"),
    "WOMBAT": os.path.join(TESTDATA_DIR_DDA, "WOMBAT_stand_ion_quant_mergedproline.csv"),
    "quantms": os.path.join(TESTDATA_DIR_DDA, "sample_dda_quantms.sdrf_openms_design_msstats_in.csv"),
}


class TestLoadInputFile:
    """Tests for the load_input_file dispatcher."""

    @pytest.mark.parametrize("format_name", list(TESTDATA_FILES.keys()))
    def test_returns_nonempty_dataframe(self, format_name):
        """Each supported format should load into a non-empty DataFrame."""
        df = load_input_file(TESTDATA_FILES[format_name], format_name)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_invalid_format_raises_valueerror(self):
        """An unknown format string should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid input format"):
            load_input_file("dummy.txt", "NonExistentTool")


class TestLoadFunctionsRegistry:
    """Tests for the _LOAD_FUNCTIONS registry."""

    def test_all_expected_formats_registered(self):
        """All known tool formats should be in the registry."""
        expected = {
            "MaxQuant",
            "AlphaPept",
            "Sage",
            "FragPipe",
            "WOMBAT",
            "ProlineStudio",
            "MSAngel",
            "i2MassChroQ",
            "Custom",
            "DIA-NN",
            "AlphaDIA",
            "FragPipe (DIA-NN quant)",
            "Spectronaut",
            "MSAID",
            "PEAKS",
            "quantms",
            "MetaMorpheus",
            "Proteome Discoverer",
        }
        assert expected.issubset(set(_LOAD_FUNCTIONS.keys()))

    def test_proteome_discoverer_registered(self):
        """Proteome Discoverer loader (merged from parse_peptidoform.py) should be registered."""
        assert "Proteome Discoverer" in _LOAD_FUNCTIONS
        assert callable(_LOAD_FUNCTIONS["Proteome Discoverer"])
