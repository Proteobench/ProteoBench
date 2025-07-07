"""
DIA-NN parameter parsing.
"""

import pathlib
import re
from typing import Any, List, Optional

import pandas as pd
from packaging.version import Version

from proteobench.io.params import ProteoBenchParameters

# Regexes
fragment_mass_tolerance_regex = r"Optimised mass accuracy: (\d*\.?\d+) ppm"
precursor_mass_tolerance_regex = r"Recommended MS1 mass accuracy setting: (\d*\.?\d+) ppm"
software_version_regex = r"DIA-NN\s(.*?)\s\(Data-Independent Acquisition by Neural Networks\)"
scan_window_regex = r"Scan window radius set to (\d+)"
fdr_regex = r"Output will be filtered at (\d+\.\d+) FDR"
min_pep_len_regex = r"Min peptide length set to (\d+)"
max_pep_len_regex = r"Max peptide length set to (\d+)"
min_z_regex = r"Min precursor charge set to (\d+)"
max_z_regex = r"Max precursor charge set to (\d+)"
cleavage_regex = r"In silico digest will involve cuts at (.*)"
cleavage_exc_regex = r"But excluding cuts at (.*)"
missed_cleavages_regex = r"Maximum number of missed cleavages set to (\d+)"
max_mods_regex = r"Maximum number of variable modifications set to (\d+)"
fixed_mods_regex_1 = r"(.*) enabled as a fixed modification"
fixed_mods_regex_2 = r"Modification (.*) with mass delta \d+\.*\d* at .+ will be considered as fixed"
var_mods_regex = r"Modification (.*) with mass delta \d+\.*\d* at .+ will be considered as variable"
quant_mode_regex = r"(.*?) quantification mode"
protein_inference_regex = r"Implicit protein grouping: (.*);"

# Flags
enable_match_between_runs_regex = r"(MBR enabled)|(reanalyse them)"  # If present, MBR is enabled

PARAM_REGEX_DICT = {
    "ident_fdr_psm": fdr_regex,
    "ident_fdr_protein": fdr_regex,
    "precursor_mass_tolerance": precursor_mass_tolerance_regex,
    "fragment_mass_tolerance": fragment_mass_tolerance_regex,
    "enzyme": cleavage_regex,
    "allowed_miscleavages": missed_cleavages_regex,
    "min_peptide_length": min_pep_len_regex,
    "max_peptide_length": max_pep_len_regex,
    "fixed_mods": [fixed_mods_regex_1, fixed_mods_regex_2],
    "variable_mods": var_mods_regex,
    "max_mods": max_mods_regex,
    "min_precursor_charge": min_z_regex,
    "max_precursor_charge": max_z_regex,
    "scan_window": scan_window_regex,
    "enable_match_between_runs": enable_match_between_runs_regex,
}


PARAM_CMD_DICT = {
    "ident_fdr_psm": "qvalue",
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
    "protein_inference": "pg-level",
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

PROT_INF_MAP = {"isoform IDs": "Isoforms", "protein names": "Protein_names", "genes": "Genes"}


def find_cmdline_string(lines: List[str]) -> Optional[str]:
    """
    Find the command line statement in the log file of DIANN.

    It is assumed that this statement is stored on a single line.

    Parameters
    ----------
    lines : list[str]
        All input lines from the DIA-NN log file.

    Returns
    -------
    str
        The command line string.
    """
    for line in lines:
        if "diann" in line and "--" in line:
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
        """
        Add a modification to the specified list.

        Parameters
        ----------
        mod_list : list
            The list of parsed modifications.
        setting : str
            The parsed setting file line.
        description : str, optional
            Modification description that overwrites the parsed setting file line.
        """
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
    setting_name : str
        The name of the setting (ProteoBench).
    setting_list : list
        The input value of a given setting.

    Returns
    -------
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


def extract_with_regex(lines: List[str], regex, search_all=False) -> str:
    """
    If no mass accuracy was specified in the cmd string, extract it from the log-file.

    Parameters
    ----------
    lines : list[str]
        All input lines from the DIA-NN log file.
    regex : str
        The regex pattern to be matched.

    Returns
    -------
    str:
        The MS1 and MS2 mass accuracy specified in ppm.
    """
    if search_all:
        container = []
    for line in lines:
        regex_match = re.search(regex, line)
        if search_all and regex_match:
            container.append(regex_match.group(1))
        if not search_all and regex_match:
            return regex_match.group(1)
    if search_all and container:
        return container[-1]  # Return the last match if multiple matches are found
    return None


def parse_protein_inference_method(cmdline_dict: dict) -> str:
    """
    Parse the protein inference method from the parsed execution command string.

    This setting is defined by disparate setting tags, namely:
    - no-prot-inf: No protein inference
    - pg-level: Code specifies inference method

    Parameters
    ----------
    cmdline_dict : dict
        Parsed execution command string.

    Returns
    -------
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
    else:
        return (
            "Genes"  # Default value, when --pg-level is not changed in the GUI it does not appear in the command string
        )


def parse_quantification_strategy(cmdline_dict: dict):
    """
    Parse the quantification method from the parsed execution command string.

    This setting is defined by disparate setting tags, namely:
    - direct-quant: use legacy quantification within DIANN
    - high-acc: QuantUMS high-accuracy setting
    - no tag: Default is QuantUMS high-precision

    Parameters
    ----------
    cmdline_dict : dict
        Parsed execution command string.

    Returns
    -------
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

    Parameters
    ----------
    cmdline_dict : dict
        Parsed execution command string.

    Returns
    -------
    dict
        Dictionary specifying algorithm name for RT, IM and MS2_int.
    """
    if "predictor" in cmdline_dict.keys():
        return {"RT": "DIANN", "IM": "DIANN", "MS2_int": "DIANN"}
    elif "lib" in cmdline_dict.keys():
        if not isinstance(cmdline_dict["lib"], bool):
            return {"RT": "User defined speclib", "IM": "User defined speclib", "MS2_int": "User defined speclib"}


def extract_cfg_parameter(lines: List[str], regex: str, cast_type: type = str, default=None, search_all=False) -> Any:
    """Extract and cast a parameter using a regex pattern."""
    match = extract_with_regex(lines, regex, search_all=search_all)
    if match is None:
        return default
    try:
        return cast_type(match)
    except ValueError:
        return default


def extract_modifications(lines: List[str], regexes: List[str]) -> Optional[str]:
    """Extract and join modifications from a list of regexes."""
    modifications = []
    for regex in regexes:
        modifications.extend(
            match.group(1) if match.group(1).endswith("\n") else match.group(1) + "\n"
            for match in re.finditer(regex, "\n".join(lines))
        )
    return ",".join(modifications).replace("\n", "") if modifications else None


def extract_params(fname: str) -> ProteoBenchParameters:
    """
    Parse DIA-NN log file and extract relevant parameters.

    Logic:
    1. Read the log file and extract the software version.
    2. Find the command line string that was used to run DIA-NN.
    3. Parse the command line string to extract settings.
    Default values are set for parameters that are not specified in the command line.
    4. If the --cfg flag is used (meaning a configuration file was used),
      the parameters are parsed from the free text underneath the cmd line.


    Parameters
    ----------
    fname : str
        Parameter file name path.

    Returns
    -------
    ProteoBenchParameters
        The parsed ProteoBenchParameters object.
    """
    cfg_used = False
    # Some default and flag settings
    parameters = {
        "software_name": "DIA-NN",
        "search_engine": "DIA-NN",
        "enable_match_between_runs": False,
        "quantification_method": "QuantUMS high-precision",
        "protein_inference": "Genes",  # Default value, if not specified in the command line
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
    if cmdline_string and "--cfg" in cmdline_string:
        cfg_used = True
        # If a configuration file was used, the parameters are specified in the free text below the cmd line.
    cmdline_dict = parse_cmdline_string(cmdline_string, software_version)

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
    if "enzyme" not in parameters.keys():  # This happens when running fragpipe-diann
        parameters["enzyme"] = "cut"
    elif parameters["enzyme"] == "K*,R*":
        parameters["enzyme"] = "Trypsin/P"
    elif parameters["enzyme"] == "K*,R*,!*P":
        parameters["enzyme"] = "Trypsin"

    # If mass-acc flag is not present in cmdline string, extract it from the log file
    if "fragment_mass_tolerance" not in parameters.keys():
        fragment_mass_tol = extract_with_regex(lines, fragment_mass_tolerance_regex)
        parameters["fragment_mass_tolerance"] = "[-" + fragment_mass_tol + " ppm" + ", " + fragment_mass_tol + " ppm]"
    else:
        parameters["fragment_mass_tolerance"] = (
            "[-"
            + str(parameters["fragment_mass_tolerance"])
            + " ppm"
            + ", "
            + str(parameters["fragment_mass_tolerance"])
            + " ppm]"
        )

    if "precursor_mass_tolerance" not in parameters.keys():
        precursor_mass_tol = extract_with_regex(lines, precursor_mass_tolerance_regex)
        parameters["precursor_mass_tolerance"] = (
            "[-" + precursor_mass_tol + " ppm" + ", " + precursor_mass_tol + " ppm]"
        )
    else:
        parameters["precursor_mass_tolerance"] = (
            "[-"
            + str(parameters["precursor_mass_tolerance"])
            + " ppm"
            + ", "
            + str(parameters["precursor_mass_tolerance"])
            + " ppm]"
        )

    # If scan window is not customely set, extract it from the log file
    parameters["scan_window"] = int(extract_with_regex(lines, scan_window_regex))
    parameters["abundance_normalization_ions"] = None

    # If cfg file is used, extract the parameters from the free text below the cmd line.
    if cfg_used:
        print("DEBUG: Extracting parameters from the configuration file.")
        parameters.update(
            {
                "ident_fdr_psm": extract_cfg_parameter(lines, fdr_regex, float),
                "ident_fdr_protein": None,
                "enable_match_between_runs": bool(re.search(enable_match_between_runs_regex, "".join(lines))),
                "enzyme": (
                    f"{extract_cfg_parameter(lines, cleavage_regex) or ''},!{extract_cfg_parameter(lines, cleavage_exc_regex) or ''}"
                ),
                "allowed_miscleavages": extract_cfg_parameter(lines, missed_cleavages_regex, int),
                "min_peptide_length": extract_cfg_parameter(lines, min_pep_len_regex, int),
                "max_peptide_length": extract_cfg_parameter(lines, max_pep_len_regex, int),
                "min_precursor_charge": extract_cfg_parameter(lines, min_z_regex, int),
                "max_precursor_charge": extract_cfg_parameter(lines, max_z_regex, int),
                "max_mods": extract_cfg_parameter(lines, max_mods_regex, int),
                "quantification_method": extract_cfg_parameter(
                    lines, quant_mode_regex, str, "QuantUMS high-precision", search_all=True
                ),
                "fixed_mods": extract_modifications(lines, PARAM_REGEX_DICT["fixed_mods"]),
                "variable_mods": extract_modifications(lines, [PARAM_REGEX_DICT["variable_mods"]]),
            }
        )

        protein_inference = extract_cfg_parameter(lines, protein_inference_regex)
        parameters["protein_inference"] = PROT_INF_MAP.get(protein_inference, "Genes")

    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/DIANN_output_20240229_report.log.txt",
        "../../../test/params/Version1_9_Predicted_Library_report.log.txt",
        "../../../test/params/DIANN_WU304578_report.log.txt",
        "../../../test/params/DIANN_1.7.16.log.txt",
        "../../../test/params/DIANN_cfg_settings.txt",
        "../../../test/params/DIANN_cfg_MBR.txt",
        "../../../test/params/DIA-NN_cfg_directq.txt",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        print(series)
        series.to_csv(file.with_suffix(".csv"))
