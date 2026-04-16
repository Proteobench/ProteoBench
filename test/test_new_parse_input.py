"""Tests for proteobench.io.parsing.new_parse_input."""

import os

import pandas as pd
import pytest

from proteobench.io.parsing.new_parse_input import (
    ModuleSettings,
    ParsedInput,
    SampleAnnotation,
    load_module_settings,
    parse_input,
    process_species,
)

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/quant/quant_lfq_ion_DDA_QExactive")
PARSE_SETTINGS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/QExactive"
    )
)


class TestLoadModuleSettings:
    def test_loads_qexactive_settings(self):
        ms = load_module_settings(PARSE_SETTINGS_DIR)
        assert isinstance(ms, ModuleSettings)
        assert ms.analysis_level == "ion"
        assert ms.min_count_multispec == 1
        assert "_YEAST" in ms.species_dict
        assert ms.species_dict["_YEAST"] == "YEAST"
        assert "YEAST" in ms.species_expected_ratio

    def test_loads_samples(self):
        ms = load_module_settings(PARSE_SETTINGS_DIR)
        assert len(ms.samples) == 6
        assert all(isinstance(s, SampleAnnotation) for s in ms.samples)
        assert ms.samples[0].raw_file == "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01"
        assert ms.samples[0].sample_name == "Condition_A_Sample_Alpha_01"
        assert ms.samples[0].condition == "A"

    def test_condition_mapper_property(self):
        ms = load_module_settings(PARSE_SETTINGS_DIR)
        cm = ms.condition_mapper
        assert isinstance(cm, dict)
        assert len(cm) == 6
        assert cm["LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01"] == "A"
        assert cm["LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01"] == "B"

    def test_run_mapper_property(self):
        ms = load_module_settings(PARSE_SETTINGS_DIR)
        rm = ms.run_mapper
        assert isinstance(rm, dict)
        assert rm["LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01"] == "Condition_A_Sample_Alpha_01"

    def test_replicate_to_raw_property(self):
        ms = load_module_settings(PARSE_SETTINGS_DIR)
        r2r = ms.replicate_to_raw
        assert "A" in r2r
        assert "B" in r2r
        assert len(r2r["A"]) == 3
        assert len(r2r["B"]) == 3

    def test_loads_singlecell_settings(self):
        singlecell_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/singlecell",
            )
        )
        ms = load_module_settings(singlecell_dir)
        assert "_YEAST" in ms.species_dict
        assert "_HUMAN" in ms.species_dict
        assert "_ECOLI" not in ms.species_dict

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_module_settings("/nonexistent/path")


class TestProcessSpecies:
    @pytest.fixture
    def module_settings_hye(self):
        return ModuleSettings(
            species_dict={"_YEAST": "YEAST", "_ECOLI": "ECOLI", "_HUMAN": "HUMAN"},
            species_expected_ratio={},
            min_count_multispec=1,
            analysis_level="ion",
        )

    def test_adds_species_columns(self, module_settings_hye):
        df = pd.DataFrame({"Proteins": ["sp|P12345|PROT_YEAST", "sp|P67890|PROT_HUMAN", "sp|P11111|PROT_ECOLI"]})
        result = process_species(df, module_settings_hye)
        assert "YEAST" in result.columns
        assert "ECOLI" in result.columns
        assert "HUMAN" in result.columns
        assert "MULTI_SPEC" in result.columns

    def test_filters_multi_species(self, module_settings_hye):
        df = pd.DataFrame(
            {
                "Proteins": [
                    "sp|P1|PROT_YEAST",
                    "sp|P2|PROT_HUMAN",
                    "sp|P3|PROT_YEAST_HUMAN",  # matches both YEAST and HUMAN
                ]
            }
        )
        result = process_species(df, module_settings_hye)
        # Row with 2 species matches should be filtered (min_count_multispec=1)
        assert len(result) == 2

    def test_keeps_all_with_high_threshold(self):
        ms = ModuleSettings(
            species_dict={"_YEAST": "YEAST", "_HUMAN": "HUMAN"},
            species_expected_ratio={},
            min_count_multispec=5,
            analysis_level="ion",
        )
        df = pd.DataFrame({"Proteins": ["PROT_YEAST_HUMAN", "PROT_YEAST"]})
        result = process_species(df, ms)
        assert len(result) == 2


class TestParseInput:
    def test_returns_parsed_input(self):
        input_file = os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt")
        result = parse_input(
            input_file=input_file,
            input_format="MaxQuant",
            module_id="quant_lfq_DDA_ion_QExactive",
            parse_settings_dir=PARSE_SETTINGS_DIR,
        )
        assert isinstance(result, ParsedInput)
        assert isinstance(result.standard_format, pd.DataFrame)
        assert isinstance(result.replicate_to_raw, dict)
        assert not result.standard_format.empty
        assert result.replicate_to_raw != {}

    def test_invalid_format_raises(self):
        input_file = os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt")
        with pytest.raises(ValueError):
            parse_input(
                input_file=input_file,
                input_format="NonExistentTool",
                module_id="quant_lfq_DDA_ion_QExactive",
                parse_settings_dir=PARSE_SETTINGS_DIR,
            )
