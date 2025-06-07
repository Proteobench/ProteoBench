import os
import pytest
import pandas as pd
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder, ParseSettingsQuant

# Test data
TEST_DATA = {
    "long_format": pd.DataFrame(
        {
            "Sequence": ["PEPTIDE", "PEPTIDEK", "PEPTIDE"],
            "Raw file": ["file1", "file2", "file1"],
            "Proteins": ["PROTEIN1_YEAST", "PROTEIN2_ECOLI", "PROTEIN3_HUMAN"],
            "Modified sequence": ["PEPTIDE", "PEPTIDEK", "PEPTIDE"],
            "Charge": [2, 3, 2],
            "Intensity": [100.0, 200.0, 0.0],
            "Reverse": [False, True, False],
            "Contaminant": [False, False, True],
        }
    ),
    "short_format": pd.DataFrame(
        {
            "Sequence": ["PEPTIDE", "PEPTIDEK"],
            "Proteins": ["PROTEIN1_YEAST", "PROTEIN2_ECOLI"],
            "Modified sequence": ["PEPTIDE", "PEPTIDEK"],
            "Charge": [2, 3],
            "file1": [100.0, 150.0],
            "file2": [200.0, 250.0],
            "Reverse": [False, True],
            "Contaminant": [False, False],
        }
    ),
    "short_format_2": pd.DataFrame(
        {
            "Sequence": ["PEPTIDE", "PEPTIDEK"],
            "Proteins": ["PROTEIN1_YEAST", "PROTEIN2_ECOLI"],
            "Modified sequence": ["PEPTIDE", "PEPTIDEK"],
            "Charge": [2, 3],
            "file1": [100.0, 150.0],
            "file2": [200.0, 250.0],
            "Reverse": [False, False],
            "Contaminant": [False, False],
        }
    ),
}

# Expected output structure
EXPECTED_COLUMNS = {
    "required": ["Sequence", "Raw file", "Proteins", "Charge", "Intensity", "replicate"],
    "species": ["YEAST", "ECOLI", "HUMAN"],
    "dummy": ["file1", "file2"],
    "analysis": {"ion": ["precursor ion"], "peptidoform": ["peptidoform"]},
}

# Mock parse settings for long format
MOCK_PARSE_SETTINGS_LONG = {
    "mapper": {
        "Sequence": "Sequence",
        "Raw file": "Raw file",  # Required for long format
        "Proteins": "Proteins",
        "Modified sequence": "Modified sequence",
        "Charge": "Charge",
        "Intensity": "Intensity",  # Required for long format
        "Reverse": "Reverse",
        "Contaminant": "Contaminant",
    },
    "condition_mapper": {"file1": "A", "file2": "B"},
    "run_mapper": {"file1": "run1", "file2": "run2"},
    "species_mapper": {"_YEAST": "YEAST", "_ECOLI": "ECOLI", "_HUMAN": "HUMAN"},
    "general": {"decoy_flag": True, "contaminant_flag": "Cont_"},
}

# Mock parse settings for short format
MOCK_PARSE_SETTINGS_SHORT = {
    "mapper": {
        "Sequence": "Sequence",
        "Proteins": "Proteins",
        "Modified sequence": "Modified sequence",
        "Charge": "Charge",
        "Reverse": "Reverse",
        "Contaminant": "Contaminant",
        "file1": "file1",  # Add these to ensure they're recognized
        "file2": "file2",  # Add these to ensure they're recognized
    },
    "condition_mapper": {"file1": "A", "file2": "B"},
    "run_mapper": {"file1": "run1", "file2": "run2"},
    "species_mapper": {"_YEAST": "YEAST", "_ECOLI": "ECOLI", "_HUMAN": "HUMAN"},
    "general": {"decoy_flag": True, "contaminant_flag": "Cont_"},
}

MOCK_MODULE_SETTINGS = {"general": {"min_count_multispec": 1, "level": "ion"}, "species_expected_ratio": 1.0}


class TestParseSettingsQuant:
    @pytest.fixture
    def parse_settings_long(self):
        return ParseSettingsQuant(MOCK_PARSE_SETTINGS_LONG, MOCK_MODULE_SETTINGS)

    @pytest.fixture
    def parse_settings_short(self):
        return ParseSettingsQuant(MOCK_PARSE_SETTINGS_SHORT, MOCK_MODULE_SETTINGS)

    def test_validate_and_rename_columns(self, parse_settings_long, parse_settings_short):
        # Test with valid columns
        df = TEST_DATA["long_format"].copy()
        result = parse_settings_long._validate_and_rename_columns(df)
        assert all(col in result.columns for col in MOCK_PARSE_SETTINGS_LONG["mapper"].values())

        # Test with missing columns
        df_missing = df.drop(columns=["Sequence"])
        with pytest.raises(ValueError):
            parse_settings_long._validate_and_rename_columns(df_missing)

    def test_create_replicate_mapping(self, parse_settings_long, parse_settings_short):
        replicate_to_raw = parse_settings_long._create_replicate_mapping()
        assert replicate_to_raw == {"A": ["file1"], "B": ["file2"]}

    def test_filter_decoys(self, parse_settings_long, parse_settings_short):
        df = TEST_DATA["long_format"].copy()
        result = parse_settings_long._filter_decoys(df)
        # Should remove row where Reverse is True
        assert len(result) == 2
        assert not any(result["Reverse"])

    def test_fix_colnames(self, parse_settings_long, parse_settings_short):
        df = TEST_DATA["long_format"].copy()
        df.columns = [f"{col}.mzML.gz" for col in df.columns]
        result = parse_settings_long._fix_colnames(df)
        assert all(".mzML.gz" not in col for col in result.columns)
        assert all(".mzML" in col for col in result.columns)

    def test_mark_contaminants(self, parse_settings_long, parse_settings_short):
        df = TEST_DATA["long_format"].copy()
        result = parse_settings_long._mark_contaminants(df)
        assert "contaminant" in result.columns
        assert result["contaminant"].dtype == bool

    def test_process_species_information(self, parse_settings_long, parse_settings_short):
        df = TEST_DATA["long_format"].copy()
        result = parse_settings_long._process_species_information(df)
        # Should add species columns and filter multi-species
        assert all(species in result.columns for species in EXPECTED_COLUMNS["species"])
        assert "MULTI_SPEC" in result.columns

    def test_handle_data_format(self, parse_settings_long, parse_settings_short):
        # Test long format (no change needed)
        df_long = TEST_DATA["long_format"].copy()
        result_long = parse_settings_long._handle_data_format(df_long)
        assert "Raw file" in result_long.columns
        assert "Intensity" in result_long.columns
        assert "replicate" in result_long.columns
        assert all(dummy in result_long.columns for dummy in EXPECTED_COLUMNS["dummy"])
        assert set(result_long["replicate"]) == {"A", "B"}

        # Test short format (needs melting)
        df_short = TEST_DATA["short_format"].copy()
        result_short = parse_settings_short._handle_data_format(df_short)
        assert "Raw file" in result_short.columns
        assert "Intensity" in result_short.columns
        assert "replicate" in result_short.columns
        assert all(dummy in result_short.columns for dummy in EXPECTED_COLUMNS["dummy"])
        assert set(result_short["replicate"]) == {"A", "B"}

        # Verify melting worked correctly
        assert len(result_short) == 4  # 2 sequences * 2 files
        assert set(result_short["Raw file"]) == {"file1", "file2"}
        assert set(result_short["Intensity"]) == {100.0, 150.0, 200.0, 250.0}

    def test_filter_zero_intensities(self, parse_settings_long, parse_settings_short):
        # Need to handle data format first to get Intensity column
        df = TEST_DATA["long_format"].copy()
        df = parse_settings_long._handle_data_format(df)
        result = parse_settings_long._filter_zero_intensities(df)
        # Should remove rows with zero intensity
        assert len(result) == 2
        assert all(result["Intensity"] > 0)

    def test_format_by_analysis_level(self, parse_settings_long, parse_settings_short):
        df = TEST_DATA["long_format"].copy()
        df["proforma"] = df["Sequence"]
        df["Charge"] = df["Charge"].astype(str)
        result = parse_settings_long._format_by_analysis_level(df)
        # Should add precursor ion column for ion level
        assert "precursor ion" in result.columns
        assert all("|Z=" in ion for ion in result["precursor ion"])

    def test_convert_to_standard_format_integration(self, parse_settings_long, parse_settings_short):
        # Test with long format
        df_long = TEST_DATA["long_format"].copy()
        result_df_long, replicate_to_raw = parse_settings_long.convert_to_standard_format(df_long)

        # Test final output structure
        assert isinstance(result_df_long, pd.DataFrame)
        assert isinstance(replicate_to_raw, dict)
        assert not result_df_long.empty
        assert replicate_to_raw != {}

        # Test required columns
        assert all(col in result_df_long.columns for col in EXPECTED_COLUMNS["required"])

        # Test species columns
        assert all(species in result_df_long.columns for species in EXPECTED_COLUMNS["species"])

        # Test analysis level columns - only if we have the required columns
        if "proforma" in result_df_long.columns and "Charge" in result_df_long.columns:
            level = MOCK_MODULE_SETTINGS["general"]["level"]
            assert all(col in result_df_long.columns for col in EXPECTED_COLUMNS["analysis"][level])

        # Test data filtering
        assert not any(result_df_long["Reverse"])  # decoys filtered
        assert all(result_df_long["Intensity"] > 0)  # zero intensities filtered

        # Test with short format
        df_short = TEST_DATA["short_format"].copy()
        result_df_short, _ = parse_settings_short.convert_to_standard_format(df_short)

        # Verify both formats produce the same structure (excluding analysis-specific columns)
        analysis_cols = EXPECTED_COLUMNS["analysis"][MOCK_MODULE_SETTINGS["general"]["level"]]
        dummy_cols = EXPECTED_COLUMNS["dummy"]
        cols_to_exclude = set(analysis_cols + dummy_cols)
        long_cols = set(col for col in result_df_long.columns if col not in cols_to_exclude)
        short_cols = set(col for col in result_df_short.columns if col not in cols_to_exclude)
        assert long_cols == short_cols
        assert len(result_df_short) == 2
        assert set(result_df_short["replicate"]) == {"A", "B"}
