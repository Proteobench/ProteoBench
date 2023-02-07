import os
import unittest
import numpy as np

import proteobench.modules.dda_quant as dda_quant

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TESTDATA_FILES = { "wombat"         : os.path.join(TESTDATA_DIR, 'stand_pep_quant_mergedproline.csv'),
                 "maxquant"         : os.path.join(TESTDATA_DIR, 'evidence_sample.txt')
            }





