"""
AlphaDIA parameter parsing.
"""

import pathlib
import re
from typing import Dict, Tuple, List

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

# Regular expression to clean up lines from ANSI escape codes
ANSI_REGEX = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
TIMESTAMP_REGEX = re.compile(r"(\d+ day,)|(\d+):\d{2}:\d{2}\.?\d*")
DEBUG_LEVEL_REGEX = re.compile(r"(PROGRESS|INFO|WARNING|ERROR|CRITICAL|DEBUG):")
TREE_REGEX = re.compile(r"^\s*(├──|└──|\│)\s*|\s*(├──|└──|\│)\s*")
USER_DEFINED_REGEX = re.compile(r"(\[|\()?user defined(\]|\))?")
DEFAULT_REGEX = re.compile(r"(\[|\()?default:?(\]|\))?")

CONFIG_KEY_MAPPER = {
    "version": "software_version",
    "software_name": "software_name",
    "search_engine": "search_engine",
    "search_engine_version": "search_engine_version",
    "fdr": ["ident_fdr_psm", "ident_fdr_protein"],
    "mbr_step_enabled": "enable_match_between_runs",
    "target_ms1_tolerance": "precursor_mass_tolerance",
    "target_ms2_tolerance": "fragment_mass_tolerance",
    "enzyme": "enzyme",
    "missed_cleavages": "allowed_miscleavages",
    "min_peptide_length": "min_peptide_length",
    "max_peptide_length": "max_peptide_length",
    "fixed_modifications": "fixed_mods",
    "variable_modifications": "variable_mods",
    "max_var_mod_num": "max_mods",
    "min_precursor_charge": "min_precursor_charge",
    "max_precursor_charge": "max_precursor_charge",
    "quantification_method": "quantification_method",
    "inference_strategy": "protein_inference",
    "predictors_library": "predictors_library",
}


def clean_line(line: str) -> str:
    """Clean up a line by removing ANSI escape codes and trimming whitespace, as well as removing timestamps."""
    line = ANSI_REGEX.sub("", line)
    line = TIMESTAMP_REGEX.sub("", line)
    line = DEBUG_LEVEL_REGEX.sub("", line)
    line = TREE_REGEX.sub("", line)
    return line.strip()


def parse_key_value(line: str) -> Tuple[str, str]:
    """
    Parse a key-value pair from a line in the log. It assumes the format 'key: value'.

    Parameters
    ----------
    line : str
        The line to parse.

    Returns
    -------
    Tuple[str, str]
        The parsed key and value.
    """
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def extract_values_from_nested_lines(lines: List[str], start_index: int) -> List[int]:
    """
    Extract values from lines that are indented, following the format for parameters like precursor_len.

    Parameters
    ----------
    lines : List[str]
        List of log lines.
    start_index : int
        Index of the line where the key (e.g., precursor_len) is found.

    Returns
    -------
    List[int]
        A list of integers representing the values extracted from the nested lines.
    """
    newer_version = False
    values = []
    for line in lines[start_index:]:
        if len(values) == 3:
            break
        cleaned_line = clean_line(line)

        if cleaned_line:
            if "user defined" in cleaned_line:
                cleaned_line = USER_DEFINED_REGEX.sub("", cleaned_line)
                number = re.search(r"\d+", cleaned_line)

                if number and values and not newer_version:
                    values[-1] = number.group(0)
                elif number:
                    newer_version = True
                    values.append(number.group(0))
                elif number and values and newer_version:
                    values.append(number.group(0))
            else:
                number = re.search(r"\d+", cleaned_line)
                if number:
                    values.append(number.group(0))

    return values[:-1]


def read_file_lines(file_path: str) -> List[str]:
    """Read lines from a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except:
        lines = [l for l in file_path.read().decode("utf-8").splitlines()]
    return lines


def initialize_default_parameters() -> Dict[str, str]:
    """Initialize default parameters."""
    return {
        "software_name": "AlphaDIA",
        "search_engine": "AlphaDIA",
        "quantification_method": "DirectLFQ",
        "predictors_library": "AlphaPeptDeep",
        "enable_match_between_runs": False,
    }


def process_key_value_line(cleaned_line: str, all_parameters: Dict[str, str], version_filled: bool) -> bool:
    """Process a line containing a key-value pair."""
    key, value = parse_key_value(cleaned_line)
    if key and value:
        if key == "version" and version_filled:
            return version_filled
        if key == "version":
            version_filled = True
        if key in all_parameters:
            all_parameters[key] += f", {value}"
        else:
            all_parameters[key] = value
    return version_filled


def process_precursor_len(lines: List[str], index: int, all_parameters: Dict[str, str]) -> None:
    """Process precursor length parameters."""
    values = extract_values_from_nested_lines(lines, index + 1)
    all_parameters["min_peptide_length"] = values[0]
    all_parameters["max_peptide_length"] = values[-1]


def process_precursor_charge(lines: List[str], index: int, all_parameters: Dict[str, str]) -> None:
    """Process precursor charge parameters."""
    values = extract_values_from_nested_lines(lines, index + 1)
    all_parameters["min_precursor_charge"] = values[0]
    all_parameters["max_precursor_charge"] = values[-1]


def map_keys_to_desired_format(all_parameters: Dict[str, str]) -> None:
    """Map keys to the desired format."""
    for key in list(all_parameters.keys()):
        if key in CONFIG_KEY_MAPPER:
            mapped_keys = CONFIG_KEY_MAPPER[key]
            if isinstance(mapped_keys, list):
                for mapped_key in mapped_keys:
                    all_parameters[mapped_key] = all_parameters[key]
            else:
                all_parameters[mapped_keys] = all_parameters[key]


def clean_up_parameters(all_parameters: Dict[str, str]) -> None:
    """Clean up parameters by removing redundant keys and processing values."""
    keys_to_remove = []
    for key in all_parameters.keys():
        if key == "fdr":
            all_parameters["ident_fdr_psm"] = all_parameters[key]
            all_parameters["ident_fdr_protein"] = all_parameters[key]
            keys_to_remove.append(key)
        elif (key not in CONFIG_KEY_MAPPER.values()) and (key not in ["ident_fdr_psm", "ident_fdr_protein"]):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del all_parameters[key]

    for key, value in all_parameters.items():
        if isinstance(value, str):
            value_list = list(set(value.split(", ")))
            if len(value_list) == 1:
                all_parameters[key] = DEFAULT_REGEX.sub("", value_list[0])
            else:
                for val in value_list:
                    if "default" in val:
                        all_parameters[key] = DEFAULT_REGEX.sub("", val).replace("]", "").strip()

                    if "user defined" in val:
                        all_parameters[key] = USER_DEFINED_REGEX.sub("", val)
                        break
        elif isinstance(value, list):
            all_parameters[key] = list(set(value))


def extract_params(file_path: str) -> Dict[str, str]:
    """
    Extract parameters from the log file and return them as a dictionary.

    Parameters
    ----------
    file_path : str
        The path to the log file.

    Returns
    -------
    Dict[str, str]
        A dictionary containing the extracted parameters.
    """
    lines = read_file_lines(file_path)
    all_parameters = initialize_default_parameters()
    version_filled = False

    for i, line in enumerate(lines):
        cleaned_line = clean_line(line)
        if ":" in cleaned_line:
            version_filled = process_key_value_line(cleaned_line, all_parameters, version_filled)

        if "precursor_len" in cleaned_line:
            process_precursor_len(lines, i, all_parameters)

        if "precursor_charge" in cleaned_line:
            process_precursor_charge(lines, i, all_parameters)

    map_keys_to_desired_format(all_parameters)
    clean_up_parameters(all_parameters)
    # Format some values
    all_parameters["precursor_mass_tolerance"] = (
        "[-"
        + all_parameters["precursor_mass_tolerance"]
        + "ppm, "
        + all_parameters["precursor_mass_tolerance"]
        + "ppm]"
    )
    all_parameters["fragment_mass_tolerance"] = (
        "[-" + all_parameters["fragment_mass_tolerance"] + "ppm, " + all_parameters["fragment_mass_tolerance"] + "ppm]"
    )

    # 'True' and 'False' to boolean
    all_parameters["enable_match_between_runs"] = all_parameters["enable_match_between_runs"] == "True"

    return ProteoBenchParameters(**all_parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/log_alphadia_1.txt",
        "../../../test/params/log_alphadia_2.txt",
        "../../../test/params/log_alphadia_1.8.txt",
        "../../../test/params/log_alphadia_1.10.txt",
    ]:
        file = pathlib.Path(fname)
        pb_params = extract_params(file)
        params = pb_params.__dict__
        series = pd.Series(params)
        series.to_csv(file.with_suffix(".csv"))
        print("\n" * 3)
