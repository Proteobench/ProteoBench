import os
import unittest

from proteobench.modules.dda_quant import module_dda_quant
from proteobench.modules.dda_quant.parse_settings_dda_quant import INPUT_FORMATS

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TESTDATA_FILES = { "WOMBAT"         : os.path.join(TESTDATA_DIR, 'WOMBAT_stand_pep_quant_mergedproline.csv'),
                   "MaxQuant"         : os.path.join(TESTDATA_DIR, 'MaxQuant_evidence_sample.txt'),
                   "MSFragger"         : os.path.join(TESTDATA_DIR, 'MSFragger_combined_ion.tsv')
            }


def load_file(format_name:str):
        """ Method used to load the input file of a given format."""
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[format_name]
        user_input["input_format"] = format_name
        df = module_dda_quant.main(
            user_input["input_csv"],
            user_input["input_format"]
        )
        return df

class TestOutputFileReading(unittest.TestCase):
    """ Simple tests for reading of input files."""
    def test_MaxQuant_file(self):
        """ Test whether MaxQuant input is parsed correctly."""
        test_dataset_name = "MaxQuant"
        self.assertTrue(test_dataset_name in INPUT_FORMATS)
        df = load_file(test_dataset_name)
        self.assertFalse(df.empty)

    def test_Wombat_file(self):
        """ Test whether WOMBAT input is parsed correctly."""
        test_dataset_name = "WOMBAT"
        self.assertTrue(test_dataset_name in INPUT_FORMATS)
        df = load_file(test_dataset_name)
        self.assertFalse(df.empty)

    def test_MSFragger_file(self):
        """ Test whether MSFragger input is parsed correctly."""
        test_dataset_name = "MSFragger"
        self.assertTrue(test_dataset_name in INPUT_FORMATS)
        df = load_file(test_dataset_name)
        self.assertFalse(df.empty)

