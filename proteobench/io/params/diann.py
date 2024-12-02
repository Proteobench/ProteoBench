import pathlib
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

# Regular expression patterns for extracting specific settings
mass_tolerance_regex = r"(?<=Optimised mass accuracy: )\d*\.?\d+(?= ppm)"
software_version_regex = r"(?<=DIA-NN\s)(.*?)(?=\s\(Data-Independent Acquisition by Neural Networks\))"
scan_window_regex = r"(?<=Scan window radius set to )\d+"

# Dictionary to map command-line settings to ProteoBench parameters
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

# Lists of settings that should be treated as floats, integers, or modifications
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

    Args:
        lines (List[str]): All input lines from the DIA-NN log file.

    Returns:
        Optional[str]: The command line string if found, otherwise None.
    """
    for line in lines:
        if "diann" in line and "--f" in line and "--fasta" in line:
            return line.strip()
    return None


def parse_cmdline_string(line: str) -> dict:
    """
    Parse the command line string to extract settings.

    Args:
        line (str): The command line string to parse.

    Returns:
        dict: A dictionary of parsed settings.
            - Keys are setting names.
            - Values are lists of settings (or booleans if the setting is a flag).
    """
    setting_dict = {}
    settings = [setting.split() for setting in line.split(" --")]
    var_mods = []
    fixed_mods = []
    for setting_list in settings:
        if setting_list[0].startswith("unimod"):
            assert len(setting_list) == 1
            fixed_mods.append(setting_list[0])
        elif len(setting_list) == 1:
            setting_dict[setting_list[0]] = True
        elif setting_list[0] == "var-mod":
            var_mods.append("".join(setting_list[1:]).replace(",", "/"))
        else:
            setting_dict[setting_list[0]] = setting_list[1:]

    setting_dict["var-mod"] = var_mods
    if "mod" not in setting_dict:
        setting_dict["mod"] = fixed_mods
    return setting_dict


def parse_setting(setting_name: str, setting_list: list) -> Any:
    """
    Parse individual settings based on their type.

    Args:
        setting_name (str): The name of the setting.
        setting_list (list): The list of values for the setting.

    Returns:
        Any: The parsed value, which could be a float, integer, or string.
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


def extract_with_regex(lines: List[str], regex: str) -> str:
    """
    Extract a value from lines using the provided regular expression.

    Args:
        lines (List[str]): All input lines from the DIA-NN log file.
        regex (str): The regular expression pattern to search for.

    Returns:
        str: The matched string if found, otherwise None.
    """
    for line in lines:
        regex_match = re.search(regex, line)
        if regex_match:
            return regex_match.group(0)
    return None


def parse_protein_inference_method(cmdline_dict: dict) -> str:
    """
    Parse the protein inference method from the command-line settings.

    Args:
        cmdline_dict (dict): The parsed command line settings.

    Returns:
        str: The protein inference method.
            Possibilities are:
            - "Disabled"
            - "Isoforms"
            - "Protein_names"
            - "Genes"
    """
    if "no-prot-inf" in cmdline_dict:
        return "Disabled"
    elif "pg-level" in cmdline_dict:
        pg_setting = cmdline_dict["pg-level"][0]
        pg_level_mapping = {"0": "Isoforms", "1": "Protein_names", "2": "Genes"}
        try:
            return pg_level_mapping[pg_setting]
        except KeyError:
            raise Exception(f"Unexpected setting passed to --pg-level: {pg_setting}")


def parse_quantification_strategy(cmdline_dict: dict) -> str:
    """
    Parse the quantification strategy from the command-line settings.

    Args:
        cmdline_dict (dict): The parsed command line settings.

    Returns:
        str: The quantification method.
            Possibilities are:
            - "Legacy"
            - "QuantUMS high-accuracy"
            - "QuantUMS high-precision"
    """
    if "direct-quant" in cmdline_dict:
        return "Legacy"
    elif "high-acc" in cmdline_dict:
        return "QuantUMS high-accuracy"
    else:
        return "QuantUMS high-precision"  # Default value


def parse_predictors_library(cmdline_dict: dict) -> Dict[str, str]:
    """
    Parse the spectral library predictors from the parsed execution command string.

    Args:
        cmdline_dict (dict): The parsed command line settings.

    Returns:
        dict: A dictionary specifying the algorithm used for RT, IM, and MS2_int predictions.
    """
    if "predictor" in cmdline_dict:
        return {"RT": "DIANN", "IM": "DIANN", "MS2_int": "DIANN"}
    elif "lib" in cmdline_dict:
        if not isinstance(cmdline_dict["lib"], bool):
            return {"RT": "User defined speclib", "IM": "User defined speclib", "MS2_int": "User defined speclib"}


def extract_params(fname: str) -> ProteoBenchParameters:
    """
    Parse the DIA-NN log file and extract relevant parameters into a ProteoBenchParameters object.

    Args:
        fname (str): The path to the DIA-NN log file.

    Returns:
        ProteoBenchParameters: A parameters object containing extracted settings.
    """
    # Default parameters
    parameters = {
        "software_name": "DIA-NN",
        "search_engine": "DIA-NN",
        "enable_match_between_runs": False,
        "quantification_method": "QuantUMS high-precision",
        "protein_inference": "Heuristic protein inference",
    }

    try:
        with open(fname) as f:
            lines = f.readlines()
    except:
        lines = [l for l in fname.read().decode("utf-8").splitlines()]

    # Extract software version
    software_version = extract_with_regex(lines, software_version_regex)
    parameters["software_version"] = software_version
    parameters["search_engine_version"] = software_version

    # Extract settings from command-line
    cmdline_string = find_cmdline_string(lines)
    cmdline_dict = parse_cmdline_string(cmdline_string)

    parameters["second_pass"] = "double-search" in cmdline_dict or "double-pass" in cmdline_dict
    parameters["quantification_method"] = parse_quantification_strategy(cmdline_dict)
    parameters["protein_inference"] = parse_protein_inference_method(cmdline_dict)
    parameters["predictors_library"] = parse_predictors_library(cmdline_dict)

    # Map settings from command line to ProteoBench parameters
    for proteobench_setting, cmd_setting in PARAM_CMD_DICT.items():
        if cmd_setting in cmdline_dict:
            if isinstance(cmdline_dict[cmd_setting], bool):
                parameters[proteobench_setting] = cmdline_dict[cmd_setting]
            else:
                parameters[proteobench_setting] = parse_setting(proteobench_setting, cmdline_dict[cmd_setting])

    # Extract mass tolerance if not present in command line
    if "precursor_mass_tolerance" not in parameters:
        mass_tol = extract_with_regex(lines, mass_tolerance_regex)
        parameters["precursor_mass_tolerance"] = f"{mass_tol} ppm"
        parameters["fragment_mass_tolerance"] = f"{mass_tol} ppm"

    # Extract scan window
    parameters["scan_window"] = int(extract_with_regex(lines, scan_window_regex))

    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/DIANN_output_20240229_report.log.txt",
        "../../../test/params/Version1_9_Predicted_Library_report.log.txt",
        "../../../test/params/DIANN_WU304578_report.log.txt",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".csv"))
