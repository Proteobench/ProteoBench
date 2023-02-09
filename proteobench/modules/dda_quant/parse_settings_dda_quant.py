""" All formats available for the module """
import os
from dataclasses import dataclass
import toml
#import proteobench.modules.dda_quant.p

PARSE_SETTINGS_DIR = os.path.join(os.path.dirname(__file__), 'io_parse_settings')

PARSE_SETTINGS_FILES = { "WOMBAT"     : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_wombat.toml'),
                         "MaxQuant"         : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_maxquant.toml'),
                        "MSFragger"        : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_msfragger.toml'),
                        #"Proline"         : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_msfragger.toml')
                        "AlphaPept"        : os.path.join(PARSE_SETTINGS_DIR, 'parse_settings_alphapept.toml')
            }

INPUT_FORMATS = ("MaxQuant", 
                "AlphaPept",
                "MSFragger",
                "Proline",
                "WOMBAT")

        

class ParseSettings:
    """ Structure that contains all the parameters used to parse the given database search output. """
   
    def __init__(self, input_format:str):
        parse_settings = toml.load(PARSE_SETTINGS_FILES[input_format])

        self.mapper = parse_settings["mapper"]
        self.replicate_mapper = parse_settings["replicate_mapper"]
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self.species_dict = parse_settings["species_dict"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]
        self.min_count_multispec = parse_settings["general"]["min_count_multispec"]
        self.species_expected_ratio = parse_settings["species_expected_ratio"]
    
