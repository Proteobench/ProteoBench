import datetime
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from proteobench.datapoint.quant_datapoint import Datapoint
from proteobench.github.gh import GithubProteobotRepo
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.modules.dia_quant_ion.dia_quant_ion_module import DIAQuantIonModule
from proteobench.score.quant.quantscores import QuantScores
from proteobench.utils.plotting.plot import PlotDataPoint

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/dia_quant")
TESTDATA_FILES = {
    "DIA-NN" : os.path.join(TESTDATA_DIR, "DIANN_1.9_beta_sample_report.tsv"),
}

def load_file(format_name:str):
    """Method used to load the input file."""
    input_df = load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df

def load_local_parsing_configuration_file(format_name: str):
    """Method used to load the input file of a given format."""
    input_df = load_file(format_name)
    parse_settings_dir = os.path.join(os.path.dirname(__package__), "io", "parsing", "io_parse_settings")
    parse_settings = ParseSettingsBuilder(parse_settings_dir, acquisition_method="dia").build_parser(format_name)
    prepared_ddf, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
    intermediate = DIAQuantIonModule("").generate_intermediate(prepared_ddf, replicate_to_raw, parse_settings)
    return intermediate

def process_file(format_name: str):
    """Method used to process the input file."""
    input_df = load_file(format_name)
    parse_settings = ParseSettingsBuilder(acquisition_method="dia").build_parser(format_name)
    prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
    intermediate = DIAQuantIonModule("").generate_intermediate(prepared_df, replicate_to_raw, parse_settings)

    return intermediate

class TestOutputFileReading(unittest.TestCase):
    supported_formats = ("DIA-NN",)
    """Simple tests for reading csv input files."""

    def test_search_engines_supported(self):
        """Test whether the supported formats are supported."""
        parse_settings = ParseSettingsBuilder(acquisition_method="dia")

        for format_name in self.supported_formats:
            self.assertTrue(format_name in parse_settings.INPUT_FORMATS)

    def test_input_file_loading(self):
        """Test whether the inputs input are loaded successfully."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            self.assertFalse(input_df.empty)

    def test_local_parsing_configuration_file(self):
        """Test whether the input files are loaded successfully."""
        parse_settings_builder = ParseSettingsBuilder(acquisition_method="dia")
        for format_name in self.supported_formats:
            parse_settings = parse_settings_builder.build_parser(format_name)
            self.assertFalse(parse_settings is None)

    def test_input_file_initial_parsing(self):
        """Test the initial parsing of the input file."""
        parse_settings_builder = ParseSettingsBuilder(acquisition_method="dia") 

        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = parse_settings_builder.build_parser(format_name)
            prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

            self.assertFalse(prepared_df.empty)
            self.assertFalse(replicate_to_raw == {})

    def test_input_file_processing(self):
        """Test the processing of the input file."""
        parse_settings_builder = ParseSettingsBuilder(acquisition_method="dia")
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = parse_settings_builder.build_parser(format_name)
            prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

            # Get quantification data
            quant_score = QuantScores("precursor ion", parse_settings.species_expected_ratio(), parse_settings.species_dict()
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

if __name__ == "__main__":
    unittest.main()
        