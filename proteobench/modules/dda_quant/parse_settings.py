""" All formats available for the module """
from __future__ import annotations

import os
from pathlib import Path

import toml

from ..interfaces import Settings

#import proteobench.modules.dda_quant.p

PARSE_SETTINGS_DIR = os.path.join(os.path.dirname(__file__), 'io_parse_settings')

MapSettingFiles: dict[str, Path]

PARSE_SETTINGS_FILES = { "WOMBAT"     : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_wombat.toml'),
                         "MaxQuant"         : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_maxquant.toml'),
                        "MSFragger"        : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_msfragger.toml'),
                        "Proline"         : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_proline.toml'),
                        "AlphaPept"        : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_alphapept.toml'),
                        "Sage"        : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_sage.toml'),
                        "Custom"        : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_custom.toml')
            }

# ! Could be created from keys of PARSE_SETTINGS_FILES
INPUT_FORMATS = ("MaxQuant", 
                "AlphaPept",
                "MSFragger",
                "Proline",
                "WOMBAT",
                "Sage",
                "Custom")

LOCAL_DEVELOPMENT = False

# For local development change below to the json and path, if you do not want to download it from github
DDA_QUANT_RESULTS_PATH = "https://raw.githubusercontent.com/Proteobench/Results_Module2_quant_DDA/main/results.json" #e.g., K:/results.json

DDA_QUANT_RESULTS_REPO = "https://github.com/Proteobench/Results_Module2_quant_DDA.git"

class ParseSettings:
    """ Structure that contains all the parameters used to parse the given database search output. """
   
    def __init__(self, input_format:str):
        parse_settings = toml.load(PARSE_SETTINGS_FILES[input_format])

        self.mapper = parse_settings["mapper"]
        self.replicate_mapper = parse_settings["replicate_mapper"]
        self.run_mapper = parse_settings["run_mapper"]
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self.species_dict = parse_settings["species_mapper"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]
        self.min_count_multispec = parse_settings["general"]["min_count_multispec"]
        self.species_expected_ratio = parse_settings["species_expected_ratio"]
    

def parse_settings(input_format:str) -> Settings:
    """load settings from toml file"""
    raise NotImplementedError
