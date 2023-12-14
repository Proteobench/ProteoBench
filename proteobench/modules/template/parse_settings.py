""" All input formats available for the module """
import os
from dataclasses import dataclass
from typing import List

import toml

PARSE_SETTINGS_DIR = os.path.join(os.path.dirname(__file__), "io_parse_settings")

PARSE_SETTINGS_FILES = {
    "Format1": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_format1.toml"),
    "Format2": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_format2.toml"),
}

INPUT_FORMATS = ("Format1", "Format2")

LOCAL_DEVELOPMENT = False

# TODO Path with all the stored results of the modules
TEMPLATE_RESULTS_PATH = "https://raw.githubusercontent.com/Proteobench/Results_Module_TEMPLATE/main/results.json"


class ParseSettings:
    """Structure that contains all the parameters used to parse the given database search output."""

    def __init__(self, input_format: str):
        parse_settings = toml.load(PARSE_SETTINGS_FILES[input_format])

        # Here you can add the parameters and design from the ground truth for the benchmarking
        # They need to be defined in the different formats' .toml files
        # e.g.
        self.mapper = parse_settings["mapper"]
        self.condition_mapper = parse_settings["condition_mapper"]
