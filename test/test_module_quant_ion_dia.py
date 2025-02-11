import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from proteobench.exceptions import DatapointGenerationError
from proteobench.github.gh import GithubProteobotRepo
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.lfq.ion.DIA.quant_lfq_ion_DIA_AIF import (
    DIAQuantIonModule,
)
from proteobench.plotting.plot_quant import PlotDataPoint
from proteobench.score.quant.quantscores import QuantScores

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/dia_quant")
TESTDATA_FILES = {
    "DIA-NN": os.path.join(TESTDATA_DIR, "DIANN_1.9_beta_sample_report.tsv"),
    "AlphaDIA": os.path.join(TESTDATA_DIR, "AlphaDIA_1.7.2_sample.tsv"),
    "MaxQuant": os.path.join(TESTDATA_DIR, "MaxDIA_sample_test.txt"),
    "FragPipe (DIA-NN quant)": os.path.join(TESTDATA_DIR, "MSFraggerDIA_sample_test.tsv"),
    "Spectronaut": os.path.join(TESTDATA_DIR, "Spectronaut_test_sample_default_PG.tsv"),
    "FragPipe": os.path.join(TESTDATA_DIR, "Fragpipe_combined_ion.tsv"),
    "MSAID": os.path.join(TESTDATA_DIR, "MSAID_sample.tsv"),
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
        "ion",
        "DIA",
        "AIF",
    )
)
TESTED_SOFTWARE_TOOLS = (
    "DIA-NN",
    "AlphaDIA",
    "MaxQuant",
    "FragPipe (DIA-NN quant)",
    "Spectronaut",
    "FragPipe",
    "MSAID",
)


def load_file(format_name: str):
    """Method used to load the input file."""
    input_df = load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df


class TestSoftwareToolOutputParsing:
    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_valid_and_supported_search_tool_settings_exists(self, software_tool):
        parse_settings = ParseSettingsBuilder(parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_ion_DIA_AIF")
        assert software_tool in parse_settings.INPUT_FORMATS

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_loaded_software_tool_output_contains_data(self, software_tool):
        input_df = load_file(software_tool)
        assert not input_df.empty

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_settings_parser_created_successfully(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            module_id="quant_lfq_ion_DIA_AIF", parse_settings_dir=PARSE_SETTINGS_DIR
        )
        parse_settings = parse_settings_builder.build_parser(software_tool)
        assert parse_settings is not None

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_software_tool_output_converted_to_standard_format(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            module_id="quant_lfq_ion_DIA_AIF", parse_settings_dir=PARSE_SETTINGS_DIR
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
            module_id="quant_lfq_ion_DIA_AIF", parse_settings_dir=PARSE_SETTINGS_DIR
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


class TestDIAQuantIonModule:
    def test_benchmarking(self):
        user_input = {
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
        }

        result_performance, all_datapoints, input_df = DIAQuantIonModule("").benchmarking(
            TESTDATA_FILES["DIA-NN"], "DIA-NN", user_input, None
        )

        assert isinstance(all_datapoints, pd.DataFrame)
        assert len(all_datapoints.results[len(all_datapoints.results) - 1]) == 6

    def test_benchmarking_raises_error_when_user_input_missing_required_fields(self):
        software_tool = "DIA-NN"
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[software_tool]
        user_input["input_format"] = software_tool
        with pytest.raises(DatapointGenerationError):
            DIAQuantIonModule("").benchmarking(user_input["input_csv"], user_input["input_format"], {}, None)


class TestPlotDataPoint:
    def test_plot_metric_returns_a_figure(self):
        tmpdir = tempfile.TemporaryDirectory().name
        gpr = GithubProteobotRepo(clone_dir=tmpdir)
        gpr.clone_repo_anonymous()
        all_datapoints = gpr.read_results_json_repo()
        all_datapoints["old_new"] = "old"
        fig = PlotDataPoint().plot_metric(all_datapoints)
        assert fig is not None

    def test_plot_fold_change_histogram_returns_a_figure(self):
        np.random.seed(0)

        # Generate 1000 random values from a normal distribution
        Nyeast = 1000
        Necoli = 500
        Nhuman = 2000

        yeastRatio = np.random.normal(loc=-1, scale=1, size=Nyeast)
        humanRatio = np.random.normal(loc=0, scale=1, size=Nhuman)
        ecoliRatio = np.random.normal(loc=2, scale=1, size=Necoli)
        combined_ratios = np.concatenate([yeastRatio, humanRatio, ecoliRatio])

        human_strings = ["HUMAN"] * Nhuman
        ecoli_strings = ["ECOLI"] * Necoli
        yeast_strings = ["YEAST"] * Nyeast

        # Concatenate the lists to create a single list
        combined_list = human_strings + ecoli_strings + yeast_strings

        combineddf = pd.DataFrame({"SPECIES": combined_list, "log2_A_vs_B": combined_ratios})
        combineddf["HUMAN"] = combineddf["SPECIES"] == "HUMAN"
        combineddf["ECOLI"] = combineddf["SPECIES"] == "ECOLI"
        combineddf["YEAST"] = combineddf["SPECIES"] == "YEAST"
        species_dict = {
            "YEAST": {"A_vs_B": 2.0, "color": "red"},
            "ECOLI": {"A_vs_B": 0.25, "color": "blue"},
            "HUMAN": {"A_vs_B": 1.0, "color": "green"},
        }
        fig = PlotDataPoint().plot_fold_change_histogram(combineddf, species_dict)
        assert fig is not None
