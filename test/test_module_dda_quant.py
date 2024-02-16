import datetime
import os
import unittest

import numpy as np
import pandas as pd

from proteobench.github.gh import read_results_json_repo
from proteobench.modules.dda_quant_base.module import Datapoint, Module
from proteobench.modules.dda_quant_base.parse import ParseInputs
from proteobench.modules.dda_quant_base.parse_settings import (
    DDA_QUANT_RESULTS_REPO,
    INPUT_FORMATS,
    ParseSettings,
)
from proteobench.modules.dda_quant_base.plot import PlotDataPoint

# genereate_input_field


TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TESTDATA_FILES = {
    # "WOMBAT": os.path.join(TESTDATA_DIR, "WOMBAT_stand_pep_quant_mergedproline.csv"),
    "MaxQuant": os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
    "FragPipe": os.path.join(TESTDATA_DIR, "MSFragger_combined_ion.tsv"),
    "AlphaPept": os.path.join(TESTDATA_DIR, "AlphaPept_subset.csv"),
    "Sage": os.path.join(TESTDATA_DIR, "lfq.tsv"),
}


def load_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = Module().load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df


def load__local_parsing_configuration_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_file(format_name)
    parse_settings = ParseSettings(format_name)
    prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(input_df, parse_settings)
    intermediate = Module().generate_intermediate(prepared_df, replicate_to_raw, parse_settings)

    return intermediate


def process_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_file(format_name)
    parse_settings = ParseSettings(format_name)
    prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(input_df, parse_settings)
    intermediate = Module().generate_intermediate(prepared_df, replicate_to_raw, parse_settings)

    return intermediate


class TestOutputFileReading(unittest.TestCase):
    supported_formats = ("MaxQuant", "FragPipe", "AlphaPept", "Sage")  # "WOMBAT",
    """ Simple tests for reading csv input files."""

    def test_search_engines_supported(self):
        """Test whether the expected formats are supported."""
        for format_name in (
            "MaxQuant",
            "AlphaPept",
            "FragPipe",
            "Proline",
            "Sage",
        ):  # , "WOMBAT"
            self.assertTrue(format_name in INPUT_FORMATS)

    def test_input_file_loading(self):
        """Test whether the inputs input are loaded successfully."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            self.assertFalse(input_df.empty)

    def test_local_parsing_configuration_file(self):
        """Test parsing of the local parsing configuration files."""
        for format_name in self.supported_formats:
            parse_settings = ParseSettings(format_name)

            self.assertFalse(parse_settings is None)

    def test_input_file_initial_parsing(self):
        """Test the initial parsing of the input file."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = ParseSettings(format_name)
            prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(input_df, parse_settings)

            self.assertFalse(prepared_df.empty)
            self.assertFalse(replicate_to_raw == {})

    def test_input_file_processing(self):
        """Test the processing of the input files."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = ParseSettings(format_name)
            prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(input_df, parse_settings)

            # Get quantification data
            intermediate = Module().generate_intermediate(prepared_df, replicate_to_raw, parse_settings)

            self.assertFalse(intermediate.empty)

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
        result_performance, all_datapoints, input_df = Module().benchmarking(
            TESTDATA_FILES["MaxQuant"], "MaxQuant", user_input, None
        )
        self.assertTrue(isinstance(all_datapoints, pd.DataFrame))
        self.assertEqual(len(all_datapoints.results[len(all_datapoints.results) - 1]), 6)


class TestWrongFormatting(unittest.TestCase):
    """Simple tests that should break if the ."""

    def test_MaxQuant_file(self):
        """Test whether MaxQuant input will throw an error on missing user inputs."""
        format_name = "MaxQuant"
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[format_name]
        user_input["input_format"] = format_name

        with self.assertRaises(KeyError) as context:
            Module().benchmarking(user_input["input_csv"], user_input["input_format"], {}, None)


class TestPlot(unittest.TestCase):
    """Test if the plots return a figure."""

    def test_plot_metric(self):
        # all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
        all_datapoints = read_results_json_repo(DDA_QUANT_RESULTS_REPO)
        all_datapoints["old_new"] = "old"
        fig = PlotDataPoint().plot_metric(all_datapoints)
        self.assertIsNotNone(fig)

    def test_plot_bench(self):
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
        self.assertIsNotNone(fig)


class TestDatapoint(unittest.TestCase):
    """Test if the plots return a figure."""

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
