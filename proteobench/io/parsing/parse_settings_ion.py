""" All formats available for the module """

from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List

import pandas as pd
import toml

from .parse_ion import get_proforma_bracketed


class ParseSettingsBuilder:
    def __init__(self, parse_settings_dir=None, acquisition_method="dda"):
        if parse_settings_dir is None:
            parse_settings_dir = os.path.join(os.path.dirname(__file__), "io_parse_settings")
        if acquisition_method == "dda":
            self.PARSE_SETTINGS_FILES = {
                "MaxQuant": os.path.join(parse_settings_dir, "parse_settings_maxquant.toml"),
                "FragPipe": os.path.join(parse_settings_dir, "parse_settings_fragpipe.toml"),
                "ProlineStudio": os.path.join(parse_settings_dir, "parse_settings_proline.toml"),
                "i2MassChroQ": os.path.join(parse_settings_dir, "parse_settings_i2massChroQ.toml"),
                "AlphaPept": os.path.join(parse_settings_dir, "parse_settings_alphapept.toml"),
                "Sage": os.path.join(parse_settings_dir, "parse_settings_sage.toml"),
                "Custom": os.path.join(parse_settings_dir, "parse_settings_custom_DDA_quant_ion.toml"),
            }
        elif acquisition_method == "dia":
            self.PARSE_SETTINGS_FILES = {
                "DIA-NN": os.path.join(parse_settings_dir, "parse_settings_diann.toml"),
                # "Skyline": os.path.join(parse_settings_dir, "parse_settings_skyline.toml"),
                # "EncyclopeDIA": os.path.join(parse_settings_dir, "parse_settings_encyclopedia.toml"),
                # "MSFraggerDIA": os.path.join(parse_settings_dir, "parse_settings_msfragger.toml"),
                # "Spectronaut": os.path.join(parse_settings_dir, "parse_settings_spectronaut.toml"),
                "AlphaDIA": os.path.join(parse_settings_dir, "parse_settings_alphadia.toml"),
                "Custom": os.path.join(parse_settings_dir, "parse_settings_custom_DIA_quant_ion.toml"),
            }
        else:
            raise ValueError("Invalid acquisition mode. Please choose either 'dda' or 'dia'.")
        self.PARSE_SETTINGS_FILES_MODULE = os.path.join(parse_settings_dir, "module_settings.toml")
        self.INPUT_FORMATS = list(self.PARSE_SETTINGS_FILES.keys())

        # Check if all files are present
        missing_files = [file for file in self.PARSE_SETTINGS_FILES.values() if not os.path.isfile(file)]
        if not os.path.isfile(self.PARSE_SETTINGS_FILES_MODULE):
            missing_files.append(self.PARSE_SETTINGS_FILES_MODULE)

        if missing_files:
            raise FileNotFoundError(f"The following parse settings files are missing: {missing_files}")

    def build_parser(self, input_format: str) -> ParseSettings:
        toml_file = self.PARSE_SETTINGS_FILES[input_format]
        parse_settings = toml.load(toml_file)
        parse_settings_module = toml.load(self.PARSE_SETTINGS_FILES_MODULE)

        parser = ParseSettings(parse_settings, parse_settings_module)
        if "modifications_parser" in parse_settings.keys():
            parser = ParseModificationSettings(parser, parse_settings)

        return parser


class ParseSettings:
    """Structure that contains all the parameters used to parse
    the given benchmark run output depending on the software tool used."""

    def __init__(self, parse_settings: dict[str, any], parse_settings_module: dict[str, any]):
        self.mapper = parse_settings["mapper"]
        self.condition_mapper = parse_settings["condition_mapper"]
        self.run_mapper = parse_settings["run_mapper"]
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self._species_dict = parse_settings["species_mapper"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]

        self.min_count_multispec = parse_settings_module["general"]["min_count_multispec"]
        self._species_expected_ratio = parse_settings_module["species_expected_ratio"]

    def species_dict(self):
        return self._species_dict

    def species_expected_ratio(self):
        return self._species_expected_ratio

    def convert_to_standard_format(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """Convert a software tool output into a generic format supported by the module."""
        # TODO add functionality/steps in docstring
        # if any of the keys are not in the columns, raise an error
        if not all(k in df.columns for k in self.mapper.keys()):
            raise ValueError(
                f"Columns {set(self.mapper.keys()).difference(set(df.columns))} not found in input dataframe."
                " Please check input file and selected software tool."
            )

        df.rename(columns=self.mapper, inplace=True)

        replicate_to_raw = defaultdict(list)
        for k, v in self.condition_mapper.items():
            replicate_to_raw[v].append(k)

        if "Reverse" in self.mapper:
            df_filtered = df[df["Reverse"] != self.decoy_flag].copy()
        else:
            df_filtered = df.copy()

        df_filtered.columns = [c.replace(".mzML.gz", ".mzML") for c in df.columns]

        df_filtered["contaminant"] = df_filtered["Proteins"].str.contains(self.contaminant_flag)
        for flag, species in self._species_dict.items():
            df_filtered[species] = df_filtered["Proteins"].str.contains(flag)
        df_filtered["MULTI_SPEC"] = (
            df_filtered[list(self._species_dict.values())].sum(axis=1) > self.min_count_multispec
        )

        df_filtered = df_filtered[df_filtered["MULTI_SPEC"] == False]

        # If there is "Raw file" then it is a long format, otherwise short format
        if "Raw file" not in self.mapper.values():
            melt_vars = self.condition_mapper.keys()
            # Should be handled more elegant
            try:
                df_filtered_melted = df_filtered.melt(
                    id_vars=list(set(df_filtered.columns).difference(set(melt_vars))),
                    value_vars=melt_vars,
                    var_name="Raw file",
                    value_name="Intensity",
                )
            except KeyError:
                df_filtered_melted = df_filtered.melt(
                    id_vars=list(set(df_filtered.columns).difference(set(melt_vars))),
                    value_vars=melt_vars,
                    var_name="Raw file",
                    value_name="Intensity",
                )
        else:
            df_filtered_melted = df_filtered.copy()

        df_filtered_melted.loc[:, "replicate"] = df_filtered_melted["Raw file"].map(self.condition_mapper)
        df_filtered_melted = pd.concat([df_filtered_melted, pd.get_dummies(df_filtered_melted["Raw file"])], axis=1)

        if "proforma" in df_filtered_melted.columns and "Charge" in df_filtered_melted.columns:
            df_filtered_melted["precursor ion"] = (
                df_filtered_melted["proforma"] + "|Z=" + df_filtered_melted["Charge"].astype(str)
            )
        else:
            print("Not all columns required for making the ion are available.")
        return df_filtered_melted, replicate_to_raw


class ParseModificationSettings:
    def __init__(self, parser: ParseSettings, parse_settings: dict[str, any]):
        self.parser = parser
        self.modifications_mapper = parse_settings["modifications_parser"]["modification_dict"]
        self.modifications_isalpha = parse_settings["modifications_parser"]["isalpha"]
        self.modifications_isupper = parse_settings["modifications_parser"]["isupper"]
        self.modifications_before_aa = parse_settings["modifications_parser"]["before_aa"]
        self.modifications_pattern = parse_settings["modifications_parser"]["pattern"]
        self.modifications_pattern = rf"{self.modifications_pattern}"
        self.modifications_parse_column = parse_settings["modifications_parser"]["parse_column"]

    def species_dict(self):
        return self.parser.species_dict()

    def species_expected_ratio(self):
        return self.parser.species_expected_ratio()

    def convert_to_standard_format(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        df, replicate_to_raw = self.parser.convert_to_standard_format(df)
        df["proforma"] = df[self.modifications_parse_column].apply(
            get_proforma_bracketed,
            before_aa=self.modifications_before_aa,
            isalpha=self.modifications_isalpha,
            isupper=self.modifications_isupper,
            pattern=self.modifications_pattern,
            modification_dict=self.modifications_mapper,
        )

        try:
            df["precursor ion"] = df["proforma"] + "|Z=" + df["Charge"].astype(str)
        except KeyError:
            raise KeyError(
                "Not all columns required for making the ion are available."
                "Is the charge available in the input file?"
            )

        if "proforma" in df.columns and "Charge" in df.columns:
            df["precursor ion"] = df["proforma"] + "|Z=" + df["Charge"].astype(str)
        else:
            print("Not all columns required for making the ion are available.")

        return df, replicate_to_raw
