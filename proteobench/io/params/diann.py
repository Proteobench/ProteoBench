import pathlib
import re
from typing import Any, List, Optional

import pandas as pd
from packaging.version import Version

from proteobench.io.params import ProteoBenchParameters

mass_tolerance_regex = r"(?<=Optimised mass accuracy: )\d*\.?\d+(?= ppm)"
software_version_regex = r"(?<=DIA-NN\s)(.*?)(?=\s\(Data-Independent Acquisition by Neural Networks\))"
scan_window_regex = r"(?<=Scan window radius set to )\d+"

PARAM_CMD_DICT = {
    "ident_fdr_peptide": "qvalue",
    "ident_fdr_protein": "qvalue",
    "enable_match_between_runs": "reanalyse",
    "precursor_mass_tolerance": "mass-acc-ms1",
    "fragment_mass_tolerance": "mass-acc",
    "enzyme": "cut",
    "allowed_miscleavages": "missed-cleavages",
    "min_peptide_length": "min-pep-len",
    "max_peptide_length": "max-pep-len",
    "fixed_mods": "mod",
    "variable_mods": "var-mod",
    "max_mods": "var-mods",
    "min_precursor_charge": "min-pr-charge",
    "max_precursor_charge": "max-pr-charge",
    "scan_window": "window",
}
SETTINGS_PB_FLOAT = [
    "ident_fdr_psm",
    "ident_fdr_peptide",
    "ident_fdr_protein",
    "precursor_mass_tolerance",
    "fragment_mass_tolerance",
]
SETTINGS_PB_INT = [
    "allowed_miscleavages",
    "min_peptide_length",
    "max_peptide_length",
    "max_mods",
    "min_precursor_charge",
    "max_precursor_charge",
    "scan_window",
]
SETTINGS_PB_MOD = ["fixed_mods", "variable_mods"]


def find_cmdline_string(lines: List[str]) -> Optional[str]:
    """
    Find the command line statement in the log file of DIANN.

    It is assumed that this statement is stored on a single line.

    Parameter
    ---------
    lines: list[str]
        All input lines from the DIA-NN log file.

    Return
    ------
    str
        The command line string.
    """
    for line in lines:
        if "diann" in line and "--f" in line and "--fasta" in line:
            return line.strip()
    return None


def parse_cmdline_string(cmd_line: str, software_version: str) -> dict:
    """
    Parse a DIA-NN command line string into a dictionary of settings.

    Parameters
    ----------
    cmd_line : str
        The command line string to parse.
    software_version : str
        The version of the DIA-NN software, e.g., "1.8".

    Returns
    -------
    dict
        Parsed settings in dictionary format. Keys are setting names, and values are:
        - List of inputs for multi-value settings.
        - Boolean `True` for flag-like settings (without values).
        - Modified settings for variable and fixed modifications.

    Raises
    ------
    AssertionError
        If an unsupported setting format is detected (e.g., `unimod` with extra arguments).
    """
    settings_dict = {}
    settings_list = [setting.split() for setting in cmd_line.split(" --")]
    variable_modifications = []
    fixed_modifications = []

    def add_modification(mod_list, setting, description=None):
        """Add a modification to the specified list."""
        if len(setting) != 1:
            raise ValueError(f"Invalid `unimod` format: {setting}")
        mod_list.append(description or setting[0])

    is_version_below_1_8 = Version(software_version.split(" ")[0]) < Version("1.8")

    for setting_parts in settings_list:
        key = setting_parts[0]
        values = setting_parts[1:]

        if key.startswith("unimod"):
            if is_version_below_1_8:
                if key == "unimod4":
                    add_modification(fixed_modifications, setting_parts, "Carbamidomethyl (C)")
                elif key == "unimod35":
                    add_modification(variable_modifications, setting_parts, "Oxidation (M)")
            else:
                add_modification(fixed_modifications, setting_parts)

        elif len(setting_parts) == 1:  # Boolean flag
            settings_dict[key] = True

        elif key == "var-mod":  # Handle variable modifications
            variable_modifications.append("".join(values).replace(",", "/"))

        else:  # General key-value settings
            settings_dict[key] = values

    # Add modifications to the settings dictionary
    settings_dict["var-mod"] = variable_modifications
    if "mod" not in settings_dict:
        settings_dict["mod"] = fixed_modifications

    return settings_dict


def parse_setting(setting_name: str, setting_list: list) -> Any:
    """
    Parse individual settings based on their setting type.

    Parameters
    ----------
    setting_name: str
        The name of the setting (ProteoBench).
    setting_list: list
        The input value of a given setting.

    Return
    ------
    Any
        The parsed setting.
    """
    if setting_name in SETTINGS_PB_FLOAT:
        assert len(setting_list) == 1
        return float(setting_list[0])
    if setting_name in SETTINGS_PB_INT:
        assert len(setting_list) == 1
        return int(setting_list[0])
    if setting_name in SETTINGS_PB_MOD:
        return ",".join(setting_list)
    return "".join(setting_list)


def extract_with_regex(lines: List[str], regex) -> str:
    """
    If no mass accuracy was specified in the cmd string, extract it from the log-file.

    Parameter
    ---------
    lines: list[str]
        All input lines from the DIA-NN log file.

    Return
    ------
    str:
        The MS1 and MS2 mass accuracy specified in ppm.
    """
    for line in lines:
        regex_match = re.search(regex, line)
        if regex_match:
            x = regex_match.group(0)
            return x
    return None


def parse_protein_inference_method(cmdline_dict: dict) -> str:
    """
    Parse the protein inference method from the parsed execution command string.

    This setting is defined by disparate setting tags, namely:
    - no-prot-inf: No protein inference
    - pg-level: Code specifies inference method

    Parameter
    ---------
    cmdline_dict: dict
        Parsed execution command string

    Return
    ------
    str
        The protein inference method.
        Possibilities:
        - Disabled
        - Isoforms
        - Protein_names
        - Genes
    """
    if "no-prot-inf" in cmdline_dict.keys():
        return "Disabled"
    elif "pg-level" in cmdline_dict.keys():
        pg_setting = cmdline_dict["pg-level"][0]
        pg_level_mapping = {"0": "Isoforms", "1": "Protein_names", "2": "Genes"}
        try:
            return pg_level_mapping[pg_setting]
        except KeyError:
            Exception(f"Unexpected setting passed to --pg-level in diann.exe: {pg_setting}")


def parse_quantification_strategy(cmdline_dict: dict):
    """
    Parse the quatnification method from the parsed execution command string.

    This setting is defined by disparate setting tags, namely:
    - direct-quant: use legacy quantification within DIANN
    - high-acc: QuantUMS high-accuracy setting
    - no tag: Default is QuantUMS high-precision

    Parameter
    ---------
    cmdline_dict: dict
        Parsed execution command string

    Return
    ------
    str
        The quantification method.
        Possibilities:
        - Legacy
        - QuantUMS high-accuracy
        - QuantUMS high-precision
    """
    if "direct-quant" in cmdline_dict.keys():
        return "Legacy"
    elif "high-acc" in cmdline_dict.keys():
        return "QuantUMS high-accuracy"
    else:
        # Default value
        return "QuantUMS high-precision"


def parse_predictors_library(cmdline_dict: dict):
    """
    Parse the spectral library predictors from parsed execute command string.

    For now, only 'DIANN' and 'User defined speclib' are supported.
    In the future, the user might specify which algorithm was used for library generation.

    Parameter
    ---------
    cmdline_dict: dict
        Parsed execution command string

    Return
    ------
    dict
        Dictionary specifying algorithm name for RT, IM and MS2_int.
    """
    if "predictor" in cmdline_dict.keys():
        return {"RT": "DIANN", "IM": "DIANN", "MS2_int": "DIANN"}
    elif "lib" in cmdline_dict.keys():
        if not isinstance(cmdline_dict["lib"], bool):
            return {"RT": "User defined speclib", "IM": "User defined speclib", "MS2_int": "User defined speclib"}


def extract_params(fname: str) -> ProteoBenchParameters:
    """Parse DIA-NN log file and extract relevant parameters."""
    # Some default and flag settings
    parameters = {
        "software_name": "DIA-NN",
        "search_engine": "DIA-NN",
        "enable_match_between_runs": False,
        "quantification_method": "QuantUMS high-precision",
        "protein_inference": "Heuristic protein inference",
    }

    try:
        # Read in the log file
        with open(fname) as f:
            lines = f.readlines()
    except:
        lines = [l for l in fname.read().decode("utf-8").splitlines()]

    # Extract software versions from the log file.
    software_version = search_engine_version = extract_with_regex(lines, software_version_regex)
    parameters["software_version"] = software_version
    parameters["search_engine_version"] = search_engine_version

    # Get settings from the execution command string
    cmdline_string = find_cmdline_string(lines)
    cmdline_dict = parse_cmdline_string(cmdline_string, software_version)

    parameters["second_pass"] = "double-search" in cmdline_dict.keys() or "double-pass" in cmdline_dict.keys()
    parameters["quantification_method"] = parse_quantification_strategy(cmdline_dict)
    parameters["protein_inference"] = parse_protein_inference_method(cmdline_dict)
    parameters["predictors_library"] = parse_predictors_library(cmdline_dict)

    # Parse most settings as possible from the execution command using PARAM_CMD_DICT for mapping.
    for proteobench_setting, cmd_setting in PARAM_CMD_DICT.items():
        if cmd_setting in cmdline_dict.keys():
            if isinstance(cmdline_dict[cmd_setting], bool):
                parameters[proteobench_setting] = cmdline_dict[cmd_setting]
            else:
                parameters[proteobench_setting] = parse_setting(proteobench_setting, cmdline_dict[cmd_setting])

    # Parse cut parameter to standard enzyme name
    if parameters["enzyme"] == "K*,R*":
        parameters["enzyme"] = "Trypsin/P"
    elif parameters["enzyme"] == "K*,R*,!*P":
        parameters["enzyme"] = "Trypsin"

    # If mass-acc flag is not present in cmdline string, extract it from the log file
    if "precursor_mass_tolerance" not in parameters.keys():
        mass_tol = extract_with_regex(lines, mass_tolerance_regex)
        parameters["precursor_mass_tolerance"] = "[-" + mass_tol + " ppm" + ", " + mass_tol + " ppm]"
        parameters["fragment_mass_tolerance"] = "[-" + mass_tol + " ppm" + ", " + mass_tol + " ppm]"
    else:
        parameters["precursor_mass_tolerance"] = (
            "[-"
            + str(parameters["precursor_mass_tolerance"])
            + " ppm"
            + ", "
            + str(parameters["precursor_mass_tolerance"])
            + " ppm]"
        )
        parameters["fragment_mass_tolerance"] = (
            "[-"
            + str(parameters["fragment_mass_tolerance"])
            + " ppm"
            + ", "
            + str(parameters["fragment_mass_tolerance"])
            + " ppm]"
        )

    # If scan window is not customely set, extract it from the log file
    parameters["scan_window"] = int(extract_with_regex(lines, scan_window_regex))

    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/DIANN_output_20240229_report.log.txt",
        "../../../test/params/Version1_9_Predicted_Library_report.log.txt",
        "../../../test/params/DIANN_WU304578_report.log.txt",
        "../../../test/params/DIANN_1.7.16.log.txt",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        print(series)
        series.to_csv(file.with_suffix(".csv"))
