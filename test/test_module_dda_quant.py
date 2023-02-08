import os
import unittest

import proteobench.modules.dda_quant as dda_quant

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TESTDATA_FILES = { "WOMBAT"         : os.path.join(TESTDATA_DIR, 'WOMBAT_stand_pep_quant_mergedproline.csv'),
                   "MaxQuant"         : os.path.join(TESTDATA_DIR, 'MaxQuant_evidence_sample.txt'),
                   "MSFragger"         : os.path.join(TESTDATA_DIR, 'MSFragger_combined_ion.tsv'),
                   "AlphaPept"         : os.path.join(TESTDATA_DIR, 'AlphaPept_subset.csv')
            }

INPUT_FORMATS = {   "MaxQuant" : "MaxQuant",
                    "AlphaPept" : "AlphaPept",
                    "MSFragger" : "MSFragger",
                    "Proline" : "Proline",
                    "WOMBAT" : "WOMBAT"}


def load_file(format_name:str):
        """ Method used to load the input file of a given format."""
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[format_name]
        user_input["input_format"] = INPUT_FORMATS[format_name]
        user_input["mbr"] = True
        df = dda_quant.main(
            user_input["input_csv"],
            user_input["input_format"],
            user_input["mbr"]
        )
        return df

class TestOutputFileReading(unittest.TestCase):
    """ Simple tests for reading of input files."""
    def test_MaxQuant_file(self):
        """ Test whether MaxQuant input is parsed correctly."""
        test_dataset_name = "MaxQuant"
        df = load_file(test_dataset_name)
        self.assertFalse(df.empty)

    def test_Wombat_file(self):
        """ Test whether WOMBAT input is parsed correctly."""
        test_dataset_name = "WOMBAT"
        df = load_file(test_dataset_name)
        self.assertFalse(df.empty)

    def test_MSFragger_file(self):
        """ Test whether MSFragger input is parsed correctly."""
        test_dataset_name = "MSFragger"
        df = load_file(test_dataset_name)
        self.assertFalse(df.empty)

