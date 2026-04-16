"""Tests for proteobench.io.parsing.convert_to_intermediate."""

import os

import pandas as pd
import pytest

from proteobench.io.parsing.convert_to_intermediate import (
    ConverterBuilder,
    IntermediateFormatConverter,
    ModificationConverter,
)
from proteobench.io.parsing.new_parse_input import ModuleSettings, process_species

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


class TestIntermediateFormatConverter:
    """Tests for IntermediateFormatConverter (was ParseSettingsQuant)."""

    @pytest.fixture
    def converter_long(self):
        """Create converter for long format data."""
        return IntermediateFormatConverter(MOCK_PARSE_SETTINGS_LONG, MOCK_MODULE_SETTINGS)

    @pytest.fixture
    def converter_short(self):
        """Create converter for short format data."""
        return IntermediateFormatConverter(MOCK_PARSE_SETTINGS_SHORT, MOCK_MODULE_SETTINGS)

    def test_validate_and_rename_columns(self, converter_long, converter_short):
        """Test column validation and renaming."""
        df = TEST_DATA["long_format"].copy()
        result = converter_long._validate_and_rename_columns(df)
        assert all(col in result.columns for col in MOCK_PARSE_SETTINGS_LONG["mapper"].values())

        # Test with missing columns
        df_missing = df.drop(columns=["Sequence"])
        with pytest.raises(ValueError):
            converter_long._validate_and_rename_columns(df_missing)

    def test_create_replicate_mapping(self, converter_long, converter_short):
        """Test replicate mapping creation."""
        replicate_to_raw = converter_long.create_replicate_mapping()
        assert replicate_to_raw == {"A": ["file1"], "B": ["file2"]}

    def test_filter_decoys(self, converter_long, converter_short):
        """Test decoy filtering."""
        df = TEST_DATA["long_format"].copy()
        result = converter_long._filter_decoys(df)
        assert len(result) == 2
        assert not any(result["Reverse"])

    def test_fix_colnames(self, converter_long, converter_short):
        """Test column name cleanup (extension stripping)."""
        df = TEST_DATA["long_format"].copy()
        original_cols = list(df.columns)
        df.columns = [f"{col}.mzML.gz" for col in df.columns]
        result = converter_long._fix_colnames(df)
        assert all(".mzML.gz" not in col for col in result.columns)
        assert all(".mzML" not in col for col in result.columns)
        assert list(result.columns) == original_cols

    def test_mark_contaminants(self, converter_long, converter_short):
        """Test contaminant marking."""
        df = TEST_DATA["long_format"].copy()
        result = converter_long._mark_contaminants(df)
        assert "contaminant" in result.columns
        assert result["contaminant"].dtype == bool

    def test_process_species_information(self, converter_long, converter_short):
        """Test species processing (via standalone function)."""
        df = TEST_DATA["long_format"].copy()
        module_settings = ModuleSettings(
            species_dict={"_YEAST": "YEAST", "_ECOLI": "ECOLI", "_HUMAN": "HUMAN"},
            species_expected_ratio={},
            min_count_multispec=1,
            analysis_level="ion",
        )
        result = process_species(df, module_settings)
        assert all(species in result.columns for species in EXPECTED_COLUMNS["species"])
        assert "MULTI_SPEC" in result.columns

    def test_handle_data_format(self, converter_long, converter_short):
        """Test long and short format handling."""
        # Test long format (no melting)
        df_long = TEST_DATA["long_format"].copy()
        result_long = converter_long._handle_data_format(df_long)
        assert "Raw file" in result_long.columns
        assert "Intensity" in result_long.columns
        assert "replicate" in result_long.columns
        assert all(dummy in result_long.columns for dummy in EXPECTED_COLUMNS["dummy"])
        assert set(result_long["replicate"]) == {"A", "B"}

        # Test short format (needs melting)
        df_short = TEST_DATA["short_format"].copy()
        result_short = converter_short._handle_data_format(df_short)
        assert "Raw file" in result_short.columns
        assert "Intensity" in result_short.columns
        assert "replicate" in result_short.columns
        assert all(dummy in result_short.columns for dummy in EXPECTED_COLUMNS["dummy"])
        assert set(result_short["replicate"]) == {"A", "B"}
        assert len(result_short) == 4  # 2 sequences * 2 files
        assert set(result_short["Raw file"]) == {"file1", "file2"}
        assert set(result_short["Intensity"]) == {100.0, 150.0, 200.0, 250.0}

    def test_filter_zero_intensities(self, converter_long, converter_short):
        """Test zero intensity filtering."""
        df = TEST_DATA["long_format"].copy()
        df = converter_long._handle_data_format(df)
        result = converter_long._filter_zero_intensities(df)
        assert len(result) == 2
        assert all(result["Intensity"] > 0)

    def test_format_by_analysis_level(self, converter_long, converter_short):
        """Test analysis level formatting (ion vs peptidoform)."""
        df = TEST_DATA["long_format"].copy()
        df["proforma"] = df["Sequence"]
        df["Charge"] = df["Charge"].astype(str)
        result = converter_long._format_by_analysis_level(df)
        assert "precursor ion" in result.columns
        assert all("/" in ion for ion in result["precursor ion"])

    def test_convert_to_standard_format_integration(self, converter_long, converter_short):
        """Test full conversion pipeline end-to-end."""
        # Test with long format
        df_long = TEST_DATA["long_format"].copy()
        result_df_long = converter_long.convert_to_standard_format(df_long)
        replicate_to_raw = converter_long.create_replicate_mapping()

        assert isinstance(result_df_long, pd.DataFrame)
        assert isinstance(replicate_to_raw, dict)
        assert not result_df_long.empty
        assert replicate_to_raw != {}
        assert all(col in result_df_long.columns for col in EXPECTED_COLUMNS["required"])
        assert not any(result_df_long["Reverse"])
        assert all(result_df_long["Intensity"] > 0)

        # Test with short format
        df_short = TEST_DATA["short_format"].copy()
        result_df_short = converter_short.convert_to_standard_format(df_short)

        # Verify both formats produce the same column structure
        analysis_cols = EXPECTED_COLUMNS["analysis"][MOCK_MODULE_SETTINGS["general"]["level"]]
        dummy_cols = EXPECTED_COLUMNS["dummy"]
        cols_to_exclude = set(analysis_cols + dummy_cols)
        long_cols = set(col for col in result_df_long.columns if col not in cols_to_exclude)
        short_cols = set(col for col in result_df_short.columns if col not in cols_to_exclude)
        assert long_cols == short_cols
        assert len(result_df_short) == 2
        assert set(result_df_short["replicate"]) == {"A", "B"}


class TestModificationConverter:
    """Tests for ModificationConverter (was ParseModificationSettings)."""

    @pytest.fixture
    def mock_parse_settings(self):
        """Sage-style modification parser config."""
        return {
            "modifications_parser": {
                "parse_column": "Sequence",
                "before_aa": False,
                "isalpha": True,
                "isupper": True,
                "pattern": r"(?<=\[).+?(?=\])",
                "modification_dict": {
                    "+57.0215": "Carbamidomethyl",
                    "+15.9949": "Oxidation",
                },
            }
        }

    @pytest.fixture
    def converter(self, mock_parse_settings):
        """Create a ModificationConverter."""
        return ModificationConverter(mock_parse_settings)

    def test_init_stores_config(self, converter):
        """Initialization stores modification config correctly."""
        assert converter.modifications_mapper == {"+57.0215": "Carbamidomethyl", "+15.9949": "Oxidation"}
        assert converter.modifications_parse_column == "Sequence"
        assert converter.modifications_before_aa is False
        assert converter.modifications_isalpha is True
        assert converter.modifications_isupper is True

    def test_convert_to_proforma_ion_level(self, converter):
        """convert_to_proforma adds proforma and precursor ion columns at ion level."""
        df = pd.DataFrame(
            {
                "Sequence": ["PEPTIDE", "PEPTIDEK"],
                "Charge": [2, 3],
            }
        )
        result = converter.convert_to_proforma(df, analysis_level="ion")
        assert "proforma" in result.columns
        assert "precursor ion" in result.columns
        assert all("/" in pi for pi in result["precursor ion"])

    def test_convert_to_proforma_peptidoform_level(self, converter):
        """convert_to_proforma adds proforma and peptidoform columns at peptidoform level."""
        df = pd.DataFrame(
            {
                "Sequence": ["PEPTIDE", "PEPTIDEK"],
            }
        )
        result = converter.convert_to_proforma(df, analysis_level="peptidoform")
        assert "proforma" in result.columns
        assert "peptidoform" in result.columns

    def test_convert_to_proforma_missing_charge_raises(self, converter):
        """Missing Charge column raises KeyError at ion level."""
        df = pd.DataFrame({"Sequence": ["PEPTIDE"]})
        with pytest.raises(KeyError, match="precursor ion"):
            converter.convert_to_proforma(df, analysis_level="ion")

    def test_unmodified_peptide_passes_through(self, converter):
        """Unmodified peptide passes through as-is."""
        df = pd.DataFrame({"Sequence": ["PEPTIDE"], "Charge": [2]})
        result = converter.convert_to_proforma(df, analysis_level="ion")
        assert result["proforma"].iloc[0] == "PEPTIDE"


class TestConverterBuilder:
    """Tests for ConverterBuilder (was ParseSettingsBuilder)."""

    PARSE_SETTINGS_DIR = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "proteobench",
            "io",
            "parsing",
            "io_parse_settings",
            "Quant",
            "lfq",
            "DDA",
            "ion",
            "QExactive",
        )
    )

    def test_build_parser_returns_converter(self):
        """build_parser returns an IntermediateFormatConverter."""
        builder = ConverterBuilder(parse_settings_dir=self.PARSE_SETTINGS_DIR, module_id="quant_lfq_DDA_ion_QExactive")
        converter = builder.build_parser("MaxQuant")
        assert isinstance(converter, IntermediateFormatConverter)

    def test_invalid_module_id_raises(self):
        """Invalid module_id raises KeyError."""
        with pytest.raises(KeyError, match="Invalid module ID"):
            ConverterBuilder(parse_settings_dir=self.PARSE_SETTINGS_DIR, module_id="nonexistent_module")

    def test_input_formats_populated(self):
        """INPUT_FORMATS lists all tools for the module."""
        builder = ConverterBuilder(parse_settings_dir=self.PARSE_SETTINGS_DIR, module_id="quant_lfq_DDA_ion_QExactive")
        assert "MaxQuant" in builder.INPUT_FORMATS
        assert "Sage" in builder.INPUT_FORMATS


class TestCleanRunNameExtended:
    """Tests for extended _clean_run_name() regex."""

    @pytest.fixture
    def converter(self):
        """Converter using default regex (no per-tool override)."""
        settings = {
            "mapper": {},
            "condition_mapper": {"file1": "A"},
            "general": {"decoy_flag": False, "contaminant_flag": "Cont_"},
        }
        module = {"general": {"level": "ion"}}
        return IntermediateFormatConverter(settings, module)

    def test_strips_intensity_suffix(self, converter):
        """Default regex strips ' Intensity' suffix (FragPipe columns)."""
        assert (
            converter._clean_run_name("LFQ_Orbitrap_DDA_Condition_A_01 Intensity") == "LFQ_Orbitrap_DDA_Condition_A_01"
        )

    def test_strips_normalized_area_suffix(self, converter):
        """Default regex strips ' Normalized Area' suffix (PEAKS columns)."""
        assert (
            converter._clean_run_name("LFQ_Orbitrap_DDA_Condition_A_01 Normalized Area")
            == "LFQ_Orbitrap_DDA_Condition_A_01"
        )

    def test_strips_mgf_suffix(self, converter):
        """Default regex strips '.mgf' suffix (ProlineStudio columns)."""
        assert converter._clean_run_name("LFQ_Orbitrap_DDA_Condition_A_01.mgf") == "LFQ_Orbitrap_DDA_Condition_A_01"

    def test_strips_mzml_suffix(self, converter):
        """Default regex still strips '.mzML' suffix (Sage columns)."""
        assert converter._clean_run_name("LFQ_Orbitrap_DDA_Condition_A_01.mzML") == "LFQ_Orbitrap_DDA_Condition_A_01"

    def test_no_strip_on_plain_name(self, converter):
        """Plain file names are not changed."""
        assert converter._clean_run_name("LFQ_Orbitrap_DDA_Condition_A_01") == "LFQ_Orbitrap_DDA_Condition_A_01"


class TestTier3ConditionMapper:
    """Tests for run_mapper + [[samples]] two-step condition_mapper resolution (Tier 3)."""

    MOCK_MODULE_WITH_SAMPLES = {
        "general": {"level": "ion"},
        "samples": [
            {"raw_file": "LFQ_file_A_01", "sample_name": "Condition_A_Sample_01", "condition": "A"},
            {"raw_file": "LFQ_file_A_02", "sample_name": "Condition_A_Sample_02", "condition": "A"},
            {"raw_file": "LFQ_file_B_01", "sample_name": "Condition_B_Sample_01", "condition": "B"},
        ],
    }

    def test_wombat_style_run_mapper_builds_condition_mapper(self):
        """When condition_mapper absent but run_mapper present, two-step lookup builds it."""
        settings = {
            "mapper": {"protein_group": "Proteins", "modified_peptide": "Sequence"},
            "run_mapper": {
                "abundance_A_1": "Condition_A_Sample_01",
                "abundance_A_2": "Condition_A_Sample_02",
                "abundance_B_1": "Condition_B_Sample_01",
            },
            "general": {"decoy_flag": True, "contaminant_flag": "Cont_"},
        }
        converter = IntermediateFormatConverter(settings, self.MOCK_MODULE_WITH_SAMPLES)
        assert converter.condition_mapper["abundance_A_1"] == "A"
        assert converter.condition_mapper["abundance_A_2"] == "A"
        assert converter.condition_mapper["abundance_B_1"] == "B"

    def test_proteome_discoverer_style_run_mapper(self):
        """Proteome Discoverer long column names map to conditions via run_mapper."""
        settings = {
            "mapper": {"Protein Accessions": "Proteins"},
            "run_mapper": {
                "Abundances (Normalized): F1: Sample, ConditionA": "Condition_A_Sample_01",
                "Abundances (Normalized): F4: Sample, ConditionB": "Condition_B_Sample_01",
            },
            "general": {"decoy_flag": True, "contaminant_flag": "Cont_"},
        }
        converter = IntermediateFormatConverter(settings, self.MOCK_MODULE_WITH_SAMPLES)
        assert converter.condition_mapper["Abundances (Normalized): F1: Sample, ConditionA"] == "A"
        assert converter.condition_mapper["Abundances (Normalized): F4: Sample, ConditionB"] == "B"

    def test_condition_mapper_in_toml_takes_priority_over_run_mapper(self):
        """If both condition_mapper and run_mapper are present, condition_mapper wins."""
        settings = {
            "mapper": {},
            "condition_mapper": {"col_A": "A", "col_B": "B"},
            "run_mapper": {"col_A": "WrongSample", "col_B": "WrongSample"},
            "general": {"decoy_flag": False, "contaminant_flag": "Cont_"},
        }
        converter = IntermediateFormatConverter(settings, self.MOCK_MODULE_WITH_SAMPLES)
        assert converter.condition_mapper["col_A"] == "A"
        assert converter.condition_mapper["col_B"] == "B"

    def test_samples_fallback_when_no_run_mapper(self):
        """[[samples]] is used directly when neither condition_mapper nor run_mapper present."""
        settings = {
            "mapper": {},
            "general": {"decoy_flag": False, "contaminant_flag": "Cont_"},
        }
        converter = IntermediateFormatConverter(settings, self.MOCK_MODULE_WITH_SAMPLES)
        assert converter.condition_mapper["LFQ_file_A_01"] == "A"
        assert converter.condition_mapper["LFQ_file_B_01"] == "B"
