import re
import pandas as pd
import pathlib
from typing import List, Optional, Any
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
        if line.startswith("diann.exe"):
            return line.strip()
    return None


def parse_cmdline_string(line: str) -> dict:
    """
    Parse the command line string to the settings it specifies.

    The GitHub README.md of DIA-NN from version 1.9 was used to interpret settings.

    Parameter
    ---------
    line: str
        The command line string to parse.

    Return
    ------
    dict:
        Parsed setting parameters in dictionary format.
        Keys are setting names and values the inputted setting in list format.
        The value is boolean if the setting is considered a boolean flag.
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
    if "mod" not in setting_dict.keys():
        setting_dict["mod"] = fixed_mods
    return setting_dict


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
        "quantification_method_DIANN": "QuantUMS high-precision",
        "protein_inference": "Heuristic protein inference",
    }

    # Read in the log file
    with open(fname) as f:
        lines = f.readlines()

    # Extract software versions from the log file.
    software_version = search_engine_version = extract_with_regex(lines, software_version_regex)
    parameters["software_version"] = software_version
    parameters["search_engine_version"] = search_engine_version

    # Get settings from the execution command string
    cmdline_string = find_cmdline_string(lines)
    cmdline_dict = parse_cmdline_string(cmdline_string)

    parameters["second_pass"] = "double-search" in cmdline_dict.keys() or "double-pass" in cmdline_dict.keys()
    parameters["quantification_method_DIANN"] = parse_quantification_strategy(cmdline_dict)
    parameters["protein_inference"] = parse_protein_inference_method(cmdline_dict)
    parameters["predictors_library"] = parse_predictors_library(cmdline_dict)

    # Parse most settings as possible from the execution command using PARAM_CMD_DICT for mapping.
    for proteobench_setting, cmd_setting in PARAM_CMD_DICT.items():
        if cmd_setting in cmdline_dict.keys():
            if isinstance(cmdline_dict[cmd_setting], bool):
                parameters[proteobench_setting] = cmdline_dict[cmd_setting]
            else:
                parameters[proteobench_setting] = parse_setting(proteobench_setting, cmdline_dict[cmd_setting])

    # If mass-acc flag is not present in cmdline string, extract it from the log file
    if "precursor_mass_tolerance" not in parameters.keys():
        mass_tol = extract_with_regex(lines, mass_tolerance_regex)
        parameters["precursor_mass_tolerance"] = mass_tol + " ppm"
        parameters["fragment_mass_tolerance"] = mass_tol + " ppm"
    else:
        parameters["precursor_mass_tolerance"] += " ppm"
        parameters["fragment_mass_tolerance"] += " ppm"

    # If scan window is not customely set, extract it from the log file
    parameters["scan_window"] = int(extract_with_regex(lines, scan_window_regex))

    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/DIANN_output_20240229_report.log.txt",
        "../../../test/params/Version1_9_Predicted_Library_report.log.txt",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".csv"))
