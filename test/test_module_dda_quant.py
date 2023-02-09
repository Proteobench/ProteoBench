import os
import unittest

from proteobench.modules.dda_quant import module_dda_quant, parse_dda_id
from proteobench.modules.dda_quant.parse_settings_dda_quant import INPUT_FORMATS

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TESTDATA_FILES = { "WOMBAT"         : os.path.join(TESTDATA_DIR, 'WOMBAT_stand_pep_quant_mergedproline.csv'),
                   "MaxQuant"         : os.path.join(TESTDATA_DIR, 'MaxQuant_evidence_sample.txt'),
                   "MSFragger"         : os.path.join(TESTDATA_DIR, 'MSFragger_combined_ion.tsv'),
                   "AlphaPept"         : os.path.join(TESTDATA_DIR, 'AlphaPept_subset.csv')
            }


def load_file(format_name:str):
        """ Method used to load the input file of a given format."""
        input_df = module_dda_quant.load_input_file(TESTDATA_FILES[format_name],format_name)
        return input_df

def load__local_parsing_configuration_file(format_name:str):
        """ Method used to load the input file of a given format."""
        input_df = load_file(format_name)
        parse_settings = module_dda_quant.parse_settings_dda_quant.ParseSettings(format_name)
        prepared_df, replicate_to_raw = parse_dda_id.prepare_df(input_df, parse_settings)
        species_quant_df, cv_replicate_quant_df = module_dda_quant.get_quant(
            prepared_df,
            replicate_to_raw,
            parse_settings
        )

        # Compute quantification ratios
        result_performance = module_dda_quant.get_quant_ratios(
                    cv_replicate_quant_df,
                    species_quant_df,
                    parse_settings
        )

        return result_performance

def process_file(format_name:str):
        """ Method used to load the input file of a given format."""
        input_df = load_file(format_name)
        parse_settings = module_dda_quant.parse_settings_dda_quant.ParseSettings(format_name)
        prepared_df, replicate_to_raw = parse_dda_id.prepare_df(input_df, parse_settings)
        species_quant_df, cv_replicate_quant_df = module_dda_quant.get_quant(
            prepared_df,
            replicate_to_raw,
            parse_settings
        )

        # Compute quantification ratios
        result_performance = module_dda_quant.get_quant_ratios(
                    cv_replicate_quant_df,
                    species_quant_df,
                    parse_settings
        )

        return result_performance

class TestOutputFileReading(unittest.TestCase):
    supported_formats = ("MaxQuant","WOMBAT","MSFragger")
    """ Simple tests for reading csv input files."""
    def test_search_engines_supported(self):
         """ Test whether the expected formats are supported."""
         for format_name in ("MaxQuant","AlphaPept","MSFragger","Proline","WOMBAT"):
              self.assertTrue(format_name in INPUT_FORMATS)

    def test_input_file_loading(self):
        """ Test whether the inputs input are loaded successfully."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            self.assertFalse(input_df.empty)

    def test_local_parsing_configuration_file(self):
        """ Test parsing of the local parsing configuration files."""
        for format_name in self.supported_formats:
            parse_settings = module_dda_quant.parse_settings_dda_quant.ParseSettings(format_name)
            
            self.assertFalse(parse_settings is None)

    def test_input_file_initial_parsing(self):
        """ Test the initial parsing of the input file."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = module_dda_quant.parse_settings_dda_quant.ParseSettings(format_name)
            prepared_df, replicate_to_raw = parse_dda_id.prepare_df(input_df, parse_settings)
            
            self.assertFalse(prepared_df.empty)
            self.assertFalse(replicate_to_raw == {})

    def test_input_file_processing(self):
        """ Test the processing of the input files."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = module_dda_quant.parse_settings_dda_quant.ParseSettings(format_name)
            prepared_df, replicate_to_raw = parse_dda_id.prepare_df(input_df, parse_settings)

            # Get quantification data
            species_quant_df, cv_replicate_quant_df = module_dda_quant.get_quant(
            prepared_df,
            replicate_to_raw,parse_settings
            )

            # Compute quantification ratios
            result_performance = module_dda_quant.get_quant_ratios(
                        cv_replicate_quant_df,
                        species_quant_df,
                        parse_settings
            )
            self.assertFalse(result_performance.empty)
       
class TestWrongFormatting(unittest.TestCase):
    """ Simple tests that should break if the ."""
    def test_MaxQuant_file(self):
        """ Test whether MaxQuant input will throw an error on missing user inputs."""
        format_name = "MaxQuant"
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[format_name]
        user_input["input_format"] = format_name
       
        with self.assertRaises(KeyError) as context:
            module_dda_quant.benchmarking(
                user_input["input_csv"],
                user_input["input_format"],
                {}
            )