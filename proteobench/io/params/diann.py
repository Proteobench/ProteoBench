import re
import pandas as pd
import pathlib
from typing import List, Optional, Any
from proteobench.io.params import ProteoBenchParameters

mass_tolerance_regex = "(?<=Optimised mass accuracy: )\d*\.?\d+(?= ppm)"
software_version_regex = "(?<=DIA-NN\s)(.*?)(?=\s\(Data-Independent Acquisition by Neural Networks\))"
PARAM_CMD_DICT = {
    "ident_fdr_psm": "qvalue",
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
}
FLOAT_SETTINGS = [
    "ident_fdr_psm",
    "ident_fdr_peptide",
    "ident_fdr_protein",
    "precursor_mass_tolerance",
    "fragment_mass_tolerance",
]
INTEGER_SETTINGS = [
    "allowed_miscleavages",
    "min_peptide_length",
    "max_peptide_length",
    "max_mods",
    "min_precursor_charge",
    "max_precursor_charge",
]
MODIFICATION_SETTINGS = ["fixed_mods", "variable_mods"]


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


def get_version_number(lines: List[str]) -> Optional[str]:
    """
    Get the DIA-NN version number.

    It is assumed that the version number is specified on line
    with prefix 'DIA-NN ' and suffix ' (Data-Independent Acquisition by Neural Networks)'

    Parameter
    ---------
    lines: list[str]
        All input lines from the DIA-NN log file.

    Return
    ------
    str
        The software version.
    """
    for line in lines:
        software_version_match = re.search(software_version_regex, line)
        if software_version_match:
            software_version = software_version_match.group()
            return software_version
    return None


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
    if setting_name in FLOAT_SETTINGS:
        assert len(setting_list) == 1
        return float(setting_list[0])
    if setting_name in INTEGER_SETTINGS:
        assert len(setting_list) == 1
        return int(setting_list[0])
    if setting_name in MODIFICATION_SETTINGS:
        return ",".join(setting_list)
    return "".join(setting_list)


def extract_mass_accuracy(lines: List[str]) -> str:
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
        mass_tolerance_match = re.search(mass_tolerance_regex, line)
        if mass_tolerance_match:
            fragment_mass_tolerance = mass_tolerance_match.group()
            return fragment_mass_tolerance


def extract_params(fname: str) -> ProteoBenchParameters:
    """Parse DIA-NN log file and extract relevant parameters."""
    parameters = {"software_name": "DIA-NN", "search_engine": "DIA-NN", "enable_match_between_runs": False}

    # Read in the log file
    with open(fname) as f:
        lines = f.readlines()

    software_version = search_engine_version = get_version_number(lines)
    cmdline_string = find_cmdline_string(lines)
    settings_dict = parse_cmdline_string(cmdline_string)

    for proteobench_setting, cmd_setting in PARAM_CMD_DICT.items():
        if cmd_setting in settings_dict.keys():
            if isinstance(settings_dict[cmd_setting], bool):
                parameters[proteobench_setting] = settings_dict[cmd_setting]
            else:
                parameters[proteobench_setting] = parse_setting(proteobench_setting, settings_dict[cmd_setting])

    parameters["software_version"] = software_version
    parameters["search_engine_version"] = search_engine_version

    if "precursor_mass_tolerance" not in parameters.keys():
        mass_tol = extract_mass_accuracy(lines)
        parameters["precursor_mass_tolerance"] = mass_tol + " ppm"
        parameters["fragment_mass_tolerance"] = mass_tol + " ppm"
    else:
        parameters["precursor_mass_tolerance"] += " ppm"
        parameters["fragment_mass_tolerance"] += " ppm"

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
