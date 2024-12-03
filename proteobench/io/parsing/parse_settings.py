"""All formats available for the module"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

import pandas as pd
import toml

from .parse_ion import get_proforma_bracketed


class ParseSettingsBuilder:
    def __init__(self, parse_settings_dir: Optional[str] = None, module_id: str = "quant_lfq_ion_DDA"):
        """
        Initializes the settings builder with parse settings from TOML files.

        Args:
            parse_settings_dir (Optional[str]): The directory containing the parse settings files. Defaults to None.
            module_id (str): The ID of the module used to fetch the specific parse settings. Defaults to "quant_lfq_ion_DDA".
        """
        self.PARSE_SETTINGS_TOMLS = toml.load(
            os.path.join(os.path.dirname(__file__), "io_parse_settings", "parse_settings_files.toml")
        )
        if parse_settings_dir is None:
            parse_settings_dir = os.path.join(
                os.path.dirname(__file__), "io_parse_settings", "Quant", "lfq", "ion", "DDA"
            )

        try:
            self.PARSE_SETTINGS_FILES = {
                key: os.path.join(parse_settings_dir, value)
                for key, value in self.PARSE_SETTINGS_TOMLS[module_id].items()
            }
        except KeyError:
            raise KeyError(
                f"Invalid module ID: {module_id}. Valid modules with configured parse settings are: {self.PARSE_SETTINGS_TOMLS.keys()}"
            )

        self.PARSE_SETTINGS_FILES_MODULE = os.path.join(parse_settings_dir, "module_settings.toml")
        self.INPUT_FORMATS = list(self.PARSE_SETTINGS_FILES.keys())

        # Check if all files are present
        missing_files = [file for file in self.PARSE_SETTINGS_FILES.values() if not os.path.isfile(file)]
        if not os.path.isfile(self.PARSE_SETTINGS_FILES_MODULE):
            missing_files.append(self.PARSE_SETTINGS_FILES_MODULE)

        if missing_files:
            raise FileNotFoundError(f"The following parse settings files are missing: {missing_files}")

    def build_parser(self, input_format: str) -> ParseSettings:
        """
        Build the parser for a given input format using the corresponding TOML files.

        Args:
            input_format (str): The input format to build the parser for (e.g., "MaxQuant", "Sage").

        Returns:
            ParseSettings: The parser for the specified input format.
        """
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

    def __init__(self, parse_settings: Dict[str, Any], parse_settings_module: Dict[str, Any]):
        """
        Initialize the ParseSettings object with the parameters from the TOML files.

        Args:
            parse_settings (Dict[str, Any]): The settings for parsing, typically loaded from a TOML file.
            parse_settings_module (Dict[str, Any]): Module-specific settings, typically loaded from a TOML file.
        """
        self.mapper = parse_settings["mapper"]
        self.condition_mapper = parse_settings["condition_mapper"]
        self.run_mapper = parse_settings["run_mapper"]
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self._species_dict = parse_settings["species_mapper"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]
        self.min_count_multispec = parse_settings_module["general"]["min_count_multispec"]
        self.analysis_level = parse_settings_module["general"]["level"]
        self._species_expected_ratio = parse_settings_module["species_expected_ratio"]

    def species_dict(self) -> Dict[str, str]:
        """
        Get the species dictionary.

        Returns:
            Dict[str, str]: A dictionary of species mappings.
        """
        return self._species_dict

    def species_expected_ratio(self) -> float:
        """
        Get the expected species ratio.

        Returns:
            float: The expected ratio of species.
        """
        return self._species_expected_ratio

    def convert_to_standard_format(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """
        Convert a software tool output into a generic format supported by the module.

        Args:
            df (pd.DataFrame): The input DataFrame to convert.

        Returns:
            tuple[pd.DataFrame, Dict[int, List[str]]]: The converted DataFrame and a dictionary mapping replicates to raw data.
        """
        # TODO: Add functionality/steps in docstring.
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
            df_filtered_melted = df_filtered.melt(
                id_vars=list(set(df_filtered.columns).difference(set(melt_vars))),
                value_vars=melt_vars,
                var_name="Raw file",
                value_name="Intensity",
            )
        else:
            df_filtered_melted = df_filtered.copy()

        df_filtered_melted["replicate"] = df_filtered_melted["Raw file"].map(self.condition_mapper)
        df_filtered_melted = pd.concat([df_filtered_melted, pd.get_dummies(df_filtered_melted["Raw file"])], axis=1)

        if self.analysis_level == "ion":
            if "proforma" in df_filtered_melted.columns and "Charge" in df_filtered_melted.columns:
                df_filtered_melted["precursor ion"] = (
                    df_filtered_melted["proforma"] + "|Z=" + df_filtered_melted["Charge"].astype(str)
                )
            else:
                print("Not all columns required for making the ion are available.")
            return df_filtered_melted, replicate_to_raw

        elif self.analysis_level == "peptidoform":
            if "proforma" in df_filtered_melted.columns:
                df_filtered_melted["peptidoform"] = df_filtered_melted["proforma"]
            else:
                print("Not all columns required for making the peptidoform are available.")
            return df_filtered_melted, replicate_to_raw

        else:
            raise ValueError("Analysis level not supported.")


class ParseModificationSettings:
    def __init__(self, parser: ParseSettings, parse_settings: Dict[str, Any]):
        """
        Initialize the ParseModificationSettings object.

        Args:
            parser (ParseSettings): The base parse settings object.
            parse_settings (Dict[str, Any]): The modifications-specific parse settings.
        """
        self.parser = parser
        self.modifications_mapper = parse_settings["modifications_parser"]["modification_dict"]
        self.modifications_isalpha = parse_settings["modifications_parser"]["isalpha"]
        self.modifications_isupper = parse_settings["modifications_parser"]["isupper"]
        self.modifications_before_aa = parse_settings["modifications_parser"]["before_aa"]
        self.modifications_pattern = parse_settings["modifications_parser"]["pattern"]
        self.modifications_pattern = rf"{self.modifications_pattern}"
        self.modifications_parse_column = parse_settings["modifications_parser"]["parse_column"]

    def species_dict(self) -> Dict[str, str]:
        """
        Get the species dictionary from the parser.

        Returns:
            Dict[str, str]: The species dictionary.
        """
        return self.parser.species_dict()

    def species_expected_ratio(self) -> float:
        """
        Get the expected species ratio from the parser.

        Returns:
            float: The expected species ratio.
        """
        return self.parser.species_expected_ratio()

    def convert_to_standard_format(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """
        Convert the DataFrame to a standard format, adding modifications to the 'proforma' column.

        Args:
            df (pd.DataFrame): The input DataFrame to convert.

        Returns:
            tuple[pd.DataFrame, Dict[int, List[str]]]: The converted DataFrame and a dictionary mapping replicates to raw data.
        """
        df, replicate_to_raw = self.parser.convert_to_standard_format(df)
        df["proforma"] = df[self.modifications_parse_column].apply(
            get_proforma_bracketed,
            before_aa=self.modifications_before_aa,
            isalpha=self.modifications_isalpha,
            isupper=self.modifications_isupper,
            pattern=self.modifications_pattern,
            modification_dict=self.modifications_mapper,
        )

        if self.parser.analysis_level == "ion":
            try:
                df["precursor ion"] = df["proforma"] + "|Z=" + df["Charge"].astype(str)
            except KeyError:
                raise KeyError(
                    "Not all columns required for making the ion are available."
                    " Is the charge available in the input file?"
                )

            return df, replicate_to_raw

        elif self.parser.analysis_level == "peptidoform":
            if "proforma" in df.columns:
                df["peptidoform"] = df["proforma"]
            else:
                print("Not all columns required for making the peptidoform are available.")
            return df, replicate_to_raw
