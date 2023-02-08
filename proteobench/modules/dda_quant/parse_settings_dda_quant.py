""" All formats available for the module """
import os


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