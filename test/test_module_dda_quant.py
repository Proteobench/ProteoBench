import datetime
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from proteobench.datapoint.quant_datapoint import QuantDatapoint
from proteobench.github.gh import GithubProteobotRepo
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.lfq.ion.DDA.quant_lfq_ion_DDA import DDAQuantIonModule
from proteobench.plotting.plot_quant import PlotDataPoint
from proteobench.score.quant.quantscores import QuantScores

# genereate_input_field


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
        "DDA",
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
    # "WOMBAT",
)


def load_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df


class TestSoftwareToolOutputParsing:
    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_valid_and_supported_search_tool_settings_exists(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_ion_DDA"
        )
        assert software_tool in parse_settings_builder.INPUT_FORMATS

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_loaded_software_tool_output_contains_data(self, software_tool):
        input_df = load_file(software_tool)
        assert not input_df.empty

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_settings_parser_created_successfully(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_ion_DDA"
        )
        parse_settings = parse_settings_builder.build_parser(software_tool)
        assert parse_settings is not None

    @pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)
    def test_software_tool_output_converted_to_standard_format(self, software_tool):
        parse_settings_builder = ParseSettingsBuilder(
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_ion_DDA"
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
            parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_ion_DDA"
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
    def test_benchmarking(self):
        user_input = {
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
        result_performance, all_datapoints, input_df = DDAQuantIonModule("").benchmarking(
            TESTDATA_FILES["MaxQuant"], "MaxQuant", user_input, None
        )
        assert isinstance(all_datapoints, pd.DataFrame)
        assert len(all_datapoints.results[len(all_datapoints.results) - 1]) == 6

    def test_benchmarking_raises_error_when_user_input_missing_required_fields(self):
        software_tool = "MaxQuant"
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[software_tool]
        user_input["input_format"] = software_tool
        with pytest.raises(KeyError):
            DDAQuantIonModule("").benchmarking(user_input["input_csv"], user_input["input_format"], {}, None)


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

        # Generate 1000 random values from a normal distribution with mean -1 and variance 1
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
        # fig.write_html("dummy.html")
        assert fig is not None


class TestQuantDatapoint:
    def test_Datapoint_constructor(self):
        input_format = "MaxQuant"
        user_input = {
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
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        result_datapoint = QuantDatapoint(
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
