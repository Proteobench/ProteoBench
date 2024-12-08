import datetime
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from proteobench.datapoint.quant_datapoint import Datapoint
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


def load_file(format_name: str):
    """Method used to load the input file."""
    input_df = load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df


def process_file(format_name: str):
    """Method used to process the input file."""
    input_df = load_file(format_name)
    parse_settings = ParseSettingsBuilder(acquisition_method="dia").build_parser(format_name)
    prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
    intermediate = DIAQuantIonModule("").generate_intermediate(prepared_df, replicate_to_raw, parse_settings)

    return intermediate


class TestOutputFileReading(unittest.TestCase):
    supported_formats = (
        "DIA-NN",
        "AlphaDIA",
        "MaxQuant",
        "FragPipe (DIA-NN quant)",
        "Spectronaut",
        "FragPipe",
        "MSAID",
    )
    """Simple tests for reading csv input files."""

    def test_search_engines_supported(self):
        """Test whether the supported formats are supported."""
        parse_settings = ParseSettingsBuilder(parse_settings_dir=PARSE_SETTINGS_DIR, module_id="quant_lfq_ion_DIA_AIF")

        for format_name in self.supported_formats:
            self.assertTrue(format_name in parse_settings.INPUT_FORMATS)

    def test_input_file_loading(self):
        """Test whether the inputs input are loaded successfully."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            self.assertFalse(input_df.empty)

    def test_local_parsing_configuration_file(self):
        """Test whether the input files are loaded successfully."""

        parse_settings_builder = ParseSettingsBuilder(
            module_id="quant_lfq_ion_DIA_AIF", parse_settings_dir=PARSE_SETTINGS_DIR
        )
        for format_name in self.supported_formats:
            parse_settings = parse_settings_builder.build_parser(format_name)
            self.assertFalse(parse_settings is None)

    def test_input_file_initial_parsing(self):
        """Test the initial parsing of the input file."""

        parse_settings_builder = ParseSettingsBuilder(
            module_id="quant_lfq_ion_DIA_AIF", parse_settings_dir=PARSE_SETTINGS_DIR
        )

        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = parse_settings_builder.build_parser(format_name)
            prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

            self.assertFalse(prepared_df.empty)
            self.assertFalse(replicate_to_raw == {})

    def test_input_file_processing(self):
        """Test the processing of the input file."""

        parse_settings_builder = ParseSettingsBuilder(
            module_id="quant_lfq_ion_DIA_AIF", parse_settings_dir=PARSE_SETTINGS_DIR
        )
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = parse_settings_builder.build_parser(format_name)
            prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

            # Get quantification data
            quant_score = QuantScores(
                "precursor ion", parse_settings.species_expected_ratio(), parse_settings.species_dict()
            )
            intermediate = quant_score.generate_intermediate(prepared_df, replicate_to_raw)

            self.assertFalse(intermediate.empty)

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

        self.assertTrue(isinstance(all_datapoints, pd.DataFrame))
        self.assertEqual(len(all_datapoints.results[len(all_datapoints.results) - 1]), 6)


class TestWrongFormatting(unittest.TestCase):
    """Simple tests that should break if the input file is not formatted correctly."""

    def test_DIANN_file(self):
        """Test whether the DIANN input will throw an error on missing user inputs."""

        format_name = "DIA-NN"
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[format_name]
        user_input["input_format"] = format_name

        with self.assertRaises(DatapointGenerationError) as context:
            DIAQuantIonModule("").benchmarking(user_input["input_csv"], user_input["input_format"], {}, None)


class TestPlot(unittest.TestCase):
    """Test if the plots return a figure."""

    def test_plot_metric(self):
        tmpdir = tempfile.TemporaryDirectory().name
        gpr = GithubProteobotRepo(clone_dir=tmpdir)
        gpr.clone_repo_anonymous()
        all_datapoints = gpr.read_results_json_repo()
        all_datapoints["old_new"] = "old"
        fig = PlotDataPoint().plot_metric(all_datapoints)
        self.assertIsNotNone(fig)

    def test_plot_bench(self):
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
        self.assertIsNotNone(fig)


class TestDatapoint(unittest.TestCase):
    """Test the Datapoint class."""

    def test_Datapoint_constructor(self):
        """Test the Datapoint class."""
        input_format = "DIA-NN"
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
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        result_datapoint = Datapoint(
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


if __name__ == "__main__":
    unittest.main()
