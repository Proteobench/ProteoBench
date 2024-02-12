""" All formats available for the module """

from __future__ import annotations

import os
from pathlib import Path

import toml

from ..interfaces import Settings

# import proteobench.modules.dda_quant.p

PARSE_SETTINGS_DIR = os.path.join(os.path.dirname(__file__), "io_parse_settings")

MapSettingFiles: dict[str, Path]

PARSE_SETTINGS_FILES = {
    # "WOMBAT": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_wombat.toml"), # Wombat is not compatible with the module precursor ions
    "MaxQuant": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_maxquant.toml"),
    "FragPipe": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_fragpipe.toml"),
    "Proline": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_proline.toml"),
    "i2MassChroQ": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_i2masschroq.toml"),
    "AlphaPept": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_alphapept.toml"),
    "Sage": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_sage.toml"),
    "Custom": os.path.join(PARSE_SETTINGS_DIR, "parse_settings_custom.toml"),
}

PARSE_SETTINGS_FILES_MODULE = os.path.join(PARSE_SETTINGS_DIR, "module_settings.toml")

# ! Could be created from keys of PARSE_SETTINGS_FILES
INPUT_FORMATS = (
    "MaxQuant",
    "AlphaPept",
    "FragPipe",
    "Proline",
    "i2MassChroQ",
    # "WOMBAT",
    "Sage",
    "Custom",
)

LOCAL_DEVELOPMENT = False

# For local development change below to the json and path,
# if you do not want to download it from github
DDA_QUANT_RESULTS_PATH = (
    "https://raw.githubusercontent.com/Proteobench/Results_Module2_quant_DDA/main/results.json"  # e.g., K:/results.json
)

PRECURSOR_NAME = "precursor ion"

DDA_QUANT_RESULTS_REPO = "https://github.com/Proteobench/Results_quant_ion_DDA.git"


class ParseSettings:
    """Structure that contains all the parameters used to parse
    the given benchmark run output depending on the software tool used."""

    def __init__(self, input_format: str):
        parse_settings = toml.load(PARSE_SETTINGS_FILES[input_format])

        self.mapper = parse_settings["mapper"]
        self.condition_mapper = parse_settings["condition_mapper"]
        self.run_mapper = parse_settings["run_mapper"]
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self.species_dict = parse_settings["species_mapper"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]

        if "modifications_parser" in parse_settings.keys():
            self.apply_modifications_parser = True
            self.modifications_mapper = parse_settings["modifications_parser"]["modification_dict"]
            self.modifications_isalpha = parse_settings["modifications_parser"]["isalpha"]
            self.modifications_isupper = parse_settings["modifications_parser"]["isupper"]
            self.modifications_before_aa = parse_settings["modifications_parser"]["before_aa"]
            self.modifications_pattern = parse_settings["modifications_parser"]["pattern"]
            self.modifications_pattern = rf"{self.modifications_pattern}"
            self.modifications_parse_column = parse_settings["modifications_parser"]["parse_column"]
        else:
            self.apply_modifications_parser = False

        parse_settings_module = toml.load(PARSE_SETTINGS_FILES_MODULE)
        self.min_count_multispec = parse_settings_module["general"]["min_count_multispec"]
        self.species_expected_ratio = parse_settings_module["species_expected_ratio"]


def parse_settings(input_format: str) -> Settings:
    """load settings from toml file corresponding to the software tool."""
    raise NotImplementedError
