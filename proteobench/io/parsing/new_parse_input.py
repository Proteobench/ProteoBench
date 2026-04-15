"""
Module providing a single entry point for parsing tool output files into standard format.

Encapsulates: load input file -> build parse settings -> convert to standard format.
Provides module-level settings loading and species processing as standalone functions.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import toml

from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder


@dataclass
class ParsedInput:
    """Result of parsing a tool output file into standard format."""

    standard_format: pd.DataFrame
    replicate_to_raw: Dict[str, List[str]]


@dataclass
class ModuleSettings:
    """Module-level configuration from module_settings.toml.

    Parameters
    ----------
    species_dict : Dict[str, str]
        Mapping from protein ID flags to species names (e.g., {"_YEAST": "YEAST"}).
    species_expected_ratio : Dict[str, Any]
        Expected ratios per species with A_vs_B and color.
    min_count_multispec : int
        Maximum number of species a protein can match before being filtered.
    analysis_level : str
        Analysis level: "ion" or "peptidoform".
    """

    species_dict: Dict[str, str]
    species_expected_ratio: Dict[str, Any]
    min_count_multispec: int
    analysis_level: str


def load_module_settings(parse_settings_dir: str) -> ModuleSettings:
    """
    Load module_settings.toml and return structured config.

    Parameters
    ----------
    parse_settings_dir : str
        Path to the directory containing module_settings.toml.

    Returns
    -------
    ModuleSettings
        Structured module configuration.
    """
    module_toml_path = os.path.join(parse_settings_dir, "module_settings.toml")
    settings = toml.load(module_toml_path)
    return ModuleSettings(
        species_dict=settings["species_mapper"],
        species_expected_ratio=settings["species_expected_ratio"],
        min_count_multispec=settings["general"]["min_count_multispec"],
        analysis_level=settings["general"]["level"],
    )


def process_species(df: pd.DataFrame, module_settings: ModuleSettings) -> pd.DataFrame:
    """
    Add species boolean columns and filter multi-species rows.

    Extracted from ParseSettingsQuant._process_species_information().

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a "Proteins" column.
    module_settings : ModuleSettings
        Module settings containing species_dict and min_count_multispec.

    Returns
    -------
    pd.DataFrame
        DataFrame with species columns added and multi-species rows filtered out.
    """
    for flag, species in module_settings.species_dict.items():
        df[species] = df["Proteins"].str.contains(flag)

    species_columns = list(module_settings.species_dict.values())
    df["MULTI_SPEC"] = df[species_columns].sum(axis=1) > module_settings.min_count_multispec
    return df[df["MULTI_SPEC"] == False]


def parse_input(
    input_file,
    input_format: str,
    module_id: str,
    parse_settings_dir: str,
    input_file_secondary=None,
) -> ParsedInput:
    """
    Load input file, build parse settings, and convert to standard format.

    Parameters
    ----------
    input_file : str or file-like
        Path to the tool output file.
    input_format : str
        Software tool name (e.g., "MaxQuant", "DIA-NN").
    module_id : str
        Module identifier (e.g., "quant_lfq_DDA_ion_QExactive").
    parse_settings_dir : str
        Path to the TOML settings directory.
    input_file_secondary : str or file-like, optional
        Secondary file (used by AlphaDIA).

    Returns
    -------
    ParsedInput
        Dataclass with standard_format DataFrame and replicate_to_raw mapping.
    """
    input_df = load_input_file(input_file, input_format, input_file_secondary)
    parse_settings = ParseSettingsBuilder(
        parse_settings_dir=parse_settings_dir, module_id=module_id
    ).build_parser(input_format)
    standard_format = parse_settings.convert_to_standard_format(input_df)
    replicate_to_raw = parse_settings.create_replicate_mapping()
    return ParsedInput(standard_format=standard_format, replicate_to_raw=replicate_to_raw)
