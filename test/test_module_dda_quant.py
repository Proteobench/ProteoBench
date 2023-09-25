import os
import unittest

import pandas as pd

from proteobench.github.gh import read_json_repo
from proteobench.modules.dda_quant.module import Module
from proteobench.modules.dda_quant.parse import ParseInputs
from proteobench.modules.dda_quant.parse_settings import (
    DDA_QUANT_RESULTS_REPO, INPUT_FORMATS, ParseSettings)
from proteobench.modules.dda_quant.plot import PlotDataPoint

# genereate_input_field


TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TESTDATA_FILES = {
    "WOMBAT": os.path.join(TESTDATA_DIR, "WOMBAT_stand_pep_quant_mergedproline.csv"),
    "MaxQuant": os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt"),
    "MSFragger": os.path.join(TESTDATA_DIR, "MSFragger_combined_ion.tsv"),
    "AlphaPept": os.path.join(TESTDATA_DIR, "AlphaPept_subset.csv"),
}


def load_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = Module().load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df


def load__local_parsing_configuration_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_file(format_name)
    parse_settings = ParseSettings(format_name)
    prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(
        input_df, parse_settings
    )
    intermediate = Module().generate_intermediate(
        prepared_df, replicate_to_raw, parse_settings
    )

    return intermediate


def process_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_file(format_name)
    parse_settings = ParseSettings(format_name)
    prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(
        input_df, parse_settings
    )
    intermediate = Module().generate_intermediate(
        prepared_df, replicate_to_raw, parse_settings
    )

    return intermediate


class TestOutputFileReading(unittest.TestCase):
    supported_formats = ("MaxQuant", "WOMBAT", "MSFragger", "AlphaPept")
    """ Simple tests for reading csv input files."""

    def test_search_engines_supported(self):
        """Test whether the expected formats are supported."""
        for format_name in ("MaxQuant", "AlphaPept", "MSFragger", "Proline", "WOMBAT"):
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
            prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(
                input_df, parse_settings
            )

            self.assertFalse(prepared_df.empty)
            self.assertFalse(replicate_to_raw == {})

    def test_input_file_processing(self):
        """Test the processing of the input files."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = ParseSettings(format_name)
            prepared_df, replicate_to_raw = ParseInputs().convert_to_standard_format(
                input_df, parse_settings
            )

            # Get quantification data
            intermediate = Module().generate_intermediate(
                prepared_df, replicate_to_raw, parse_settings
            )
            self.assertFalse(intermediate.empty)


class TestWrongFormatting(unittest.TestCase):
    """Simple tests that should break if the ."""

    def test_MaxQuant_file(self):
        """Test whether MaxQuant input will throw an error on missing user inputs."""
        format_name = "MaxQuant"
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[format_name]
        user_input["input_format"] = format_name

        with self.assertRaises(KeyError) as context:
            Module().benchmarking(
                user_input["input_csv"], user_input["input_format"], {}, None
            )


class TestPlot(unittest.TestCase):
    """Test if the plots return a figure."""

    def test_plot_metric(self):

        #all_datapoints = pd.read_json(DDA_QUANT_RESULTS_PATH)
        all_datapoints = read_json_repo(DDA_QUANT_RESULTS_REPO)

        fig = PlotDataPoint().plot_metric(all_datapoints)
        self.assertIsNotNone(fig)


if __name__ == "__main__":
    unittest.main()
