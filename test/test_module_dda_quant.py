import os
import unittest
import numpy as np

import proteobench.modules.dda_quant as dda_quant

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TESTDATA_FILES = { "WOMBAT"         : os.path.join(TESTDATA_DIR, 'stand_pep_quant_mergedproline.csv'),
                 "MaxQuant"         : os.path.join(TESTDATA_DIR, 'evidence_sample.txt')
            }
INPUT_FORMATS = {   "MaxQuant" : "MaxQuant",
                    "AlphaPept" : "AlphaPept",
                    "Proline" : "Proline",
                    "WOMBAT" : "WOMBAT"}
def load_file(dataset_name:str):
        user_input = dict()
        user_input["input_csv"] = TESTDATA_FILES[dataset_name]
        user_input["input_format"] = INPUT_FORMATS[dataset_name]
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

