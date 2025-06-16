import os

import pandas as pd
import pytest

from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive
from proteobench.score.quant.quantscores import QuantScores
from proteobench.exceptions import DatapointGenerationError


TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/dda_quant")
TESTDATA_FILES = {
    # "WOMBAT": os.path.join(TESTDATA_DIR, "WOMBAT_stand_pep_quant_mergedproline.csv"),
    "MaxQuant": os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
    "MaxQuant_new": os.path.join(TESTDATA_DIR, "MaxQuant_2_5_1_evidence_sample.txt"),
    "FragPipe": os.path.join(TESTDATA_DIR, "FragPipe_MSFragger_combined_ion.tsv"),
    "AlphaPept": os.path.join(TESTDATA_DIR, "AlphaPept_subset.csv"),
    "Sage": os.path.join(TESTDATA_DIR, "sage_sample_input_lfq.tsv"),
    "ProlineStudio": os.path.join(TESTDATA_DIR, "Proline_DDA_quan_ions_subset.xlsx"),
    "MSAngel": os.path.join(TESTDATA_DIR, "MSAngel_DDA_quan_ions_subset.xlsx"),
    "i2MassChroQ": os.path.join(TESTDATA_DIR, "i2MassChroQ_DDA_quant_ions_test_new_random_subset.tsv"),
    "quantms": os.path.join(TESTDATA_DIR, "sample_dda_quantms.sdrf_openms_design_msstats_in.csv"),
    "WOMBAT": os.path.join(TESTDATA_DIR, "WOMBAT_stand_ion_quant_mergedproline.csv"),
}
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
TESTED_SOFTWARE_TOOLS = (
    "MaxQuant",
    "FragPipe",
    "AlphaPept",
    "Sage",
    "ProlineStudio",
    "MSAngel",
    "i2MassChroQ",
    "WOMBAT",
    "quantms",
)


def load_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df


class TestSoftwareToolOutputParsing:
    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_valid_and_supported_search_tool_settings_exists(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_DDA_ion_QExactive"
        )
        assert software_tool in parse_settings_builder.INPUT_FORMATS

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_loaded_software_tool_output_contains_data(self, software_tool):
        input_df = load_file(software_tool)
        assert not input_df.empty

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_settings_parser_created_successfully(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_DDA_ion_QExactive"
        )
        parse_settings = parse_settings_builder.build_parser(software_tool)
        assert parse_settings is not None

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_software_tool_output_converted_to_standard_format(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_DDA_ion_QExactive"
        )
        parse_settings = parse_settings_builder.build_parser(software_tool)

        input_df = load_file(software_tool)
        prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

        assert not prepared_df.empty
        assert replicate_to_raw != {}


class TestQuantScores:
    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_intermediate_generated_from_software_tool_output(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_DDA_ion_QExactive"
        )
        parse_settings = parse_settings_builder.build_parser(software_tool)

        input_df = load_file(software_tool)
        prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

        # Get quantification data
        quant_score = QuantScores(
            "precursor ion", parse_settings.species_expected_ratio(), parse_settings.species_dict()
        )
        intermediate = quant_score.generate_intermediate(prepared_df, replicate_to_raw)

        assert not intermediate.empty


class TestDDAQuantIonModule:
    @pytest.fixture(autouse=True)
    def _init(self):
        self.software_tool = "MaxQuant"
        self.user_input = {
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
        }

    def test_benchmarking_return_types_are_correct(self):
        intermediate_df, all_datapoints, input_df = DDAQuantIonModuleQExactive("").benchmarking(
            TESTDATA_FILES[self.software_tool], self.software_tool, self.user_input, None
        )
        assert isinstance(intermediate_df, pd.DataFrame)
        assert isinstance(all_datapoints, pd.DataFrame)
        assert isinstance(input_df, pd.DataFrame)

    def test_results_column_in_new_data_point_contains_correct_number_of_entries(self):
        _, all_datapoints, _ = DDAQuantIonModuleQExactive("").benchmarking(
            TESTDATA_FILES[self.software_tool], self.software_tool, self.user_input, None
        )
        results_entry_newest_datapoint = all_datapoints.results[len(all_datapoints.results) - 1]
        expected_number_of_entries_for_min_nr_observed_filter = 6
        assert len(results_entry_newest_datapoint) == expected_number_of_entries_for_min_nr_observed_filter

    def test_benchmarking_raises_error_when_user_input_missing_required_fields(self):
        input_file_location = TESTDATA_FILES[self.software_tool]
        input_format = self.software_tool
        empty_user_input = {}
        with pytest.raises(DatapointGenerationError):
            DDAQuantIonModuleQExactive("").benchmarking(input_file_location, input_format, empty_user_input, None)

    def test_new_datapoint_with_unique_hash_is_added_to_existing_ones(self, monkeypatch):
        def mock_clone_repo(*args, **kwargs):
            return None

        def mock_read_results_json_repo(*args, **kwargs):
            return pd.DataFrame()

        monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", mock_clone_repo)
        monkeypatch.setattr(
            "proteobench.github.gh.GithubProteobotRepo.read_results_json_repo", mock_read_results_json_repo
        )

        first_software_tool = "MaxQuant"
        second_software_tool = "FragPipe"

        _, previous_datapoints, _ = DDAQuantIonModuleQExactive("").benchmarking(
            TESTDATA_FILES[first_software_tool], first_software_tool, self.user_input, None
        )
        _, all_datapoints, _ = DDAQuantIonModuleQExactive("").benchmarking(
            TESTDATA_FILES[second_software_tool], second_software_tool, self.user_input, previous_datapoints
        )

        assert first_software_tool != second_software_tool
        assert len(all_datapoints) == 2

    def test_new_datapoint_already_present_in_all_datapoints_is_not_added(self, monkeypatch):
        # This test requires that exactly the same input data is used for the new datapoint
        # as for the 'previous_datapoints', so they can be identified as duplicates.
        def mock_clone_repo(*args, **kwargs):
            return None

        def mock_read_results_json_repo(*args, **kwargs):
            return pd.DataFrame()

        monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", mock_clone_repo)
        monkeypatch.setattr(
            "proteobench.github.gh.GithubProteobotRepo.read_results_json_repo", mock_read_results_json_repo
        )

        first_software_tool = "MaxQuant"
        second_software_tool = first_software_tool

        _, previous_datapoints, _ = DDAQuantIonModuleQExactive("").benchmarking(
            TESTDATA_FILES[first_software_tool], first_software_tool, self.user_input, None
        )
        _, all_datapoints, _ = DDAQuantIonModuleQExactive("").benchmarking(
            TESTDATA_FILES[second_software_tool], second_software_tool, self.user_input, previous_datapoints
        )

        assert first_software_tool == second_software_tool
        assert len(all_datapoints) == 1
