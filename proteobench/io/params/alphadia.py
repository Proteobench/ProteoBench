import pathlib
import re
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

levels = [0, 1, 5, 9, 13, 17]

# Regular expression to remove ANSI escape codes from strings (used for terminal color codes)
ANSI_REGEX = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")


def clean_line(line: str) -> str:
    """
    Cleans up a line by removing ANSI escape codes and leading/trailing whitespace.

    Args:
        line (str): The line to be cleaned.

    Returns:
        str: The cleaned line with no ANSI codes and stripped whitespace.
    """
    line = ANSI_REGEX.sub("", line)
    return line.strip()


def parse_line(line: str) -> Tuple[str, Dict[str, Tuple[Optional[str], Optional[str]]], int]:
    """
    Parses a log line into a tuple containing the setting name, a dictionary of settings, and the indentation level.

    Args:
        line (str): A log line to parse.

    Returns:
        Tuple[str, dict, int]:
            - The setting name as a string.
            - A dictionary of setting names and their associated values (and flags, if any).
            - The indentation level as an integer, indicating the depth of the setting in the hierarchy.
    """
    line = clean_line(line[22:])
    tab, setting = line.split("──")
    setting_list = setting.split(":")

    if len(setting_list) == 1:
        setting_dict = {setting_list[0]: (None, None)}
    else:
        value = setting_list[1].strip()
        if "(user defined)" in value:
            value = value.replace("(user defined)", "").strip()
            setting_dict = {setting_list[0]: (value, "user defined")}
        elif "(default)" in value:
            value = value.replace("(default)", "").strip()
            setting_dict = {setting_list[0]: (value, "default")}
        else:
            setting_dict = {setting_list[0]: (value, None)}

    level = levels.index(len(tab))  # Convert tab count to level
    return setting_list[0], setting_dict, level


def process_nested_values(
    header_prev: str, current_header: Optional[str], nested_values: list, line_dict_next: dict, section: dict
) -> Tuple[Optional[str], list]:
    """
    Processes nested values from a given line dictionary and updates the section dictionary.

    Args:
        header_prev (str): The previous header string.
        current_header (Optional[str]): The current header string, which can be None.
        nested_values (list): A list of nested values to be updated.
        line_dict_next (dict): A dictionary representing the next line to be processed.
        section (dict): A dictionary representing the section to be updated.

    Returns:
        Tuple[Optional[str], list]: A tuple containing the updated current header and the list of nested values.
    """
    if current_header is None or current_header != header_prev:
        nested_values = []
        current_header = header_prev

    value = list(line_dict_next.keys())[0].split()[0]  # Extract value before space
    nested_values.append(int(value))

    if "(user defined)" in list(line_dict_next.keys())[0]:
        nested_values.pop(-2)  # Remove the default value if overridden by user defined

    section[header_prev] = nested_values
    return current_header, nested_values


def update_section_with_line_dict(section: dict, line_dict_next: dict) -> None:
    """
    Updates the section dictionary with values from the line_dict_next.

    Args:
        section (dict): The section dictionary to update.
        line_dict_next (dict): The dictionary containing the new values to add to the section.
    """
    for key, (value, flag) in line_dict_next.items():
        if key in section and flag == "user defined":
            section[key] = value
        elif key not in section:
            section[key] = value


def parse_section(line: Tuple[str, dict, int], line_generator: Iterable[str]) -> Tuple[dict, int, Optional[Tuple]]:
    """
    Parses a section from a log file into a dictionary and returns the parsed section along with the indentation level and the next line.

    Args:
        line (Tuple[str, dict, int]): The first parsed line of a new section.
        line_generator (Iterable[str]): The line generator of log file lines.

    Returns:
        Tuple[dict, int, Optional[Tuple]]:
            - The parsed section as a dictionary.
            - The indentation level of the line after the section.
            - The next line after the section, or None if no more lines are available.
    """
    section = {}

    # Parse the current line and add to the section
    header_prev, line_dict, level_prev = line
    section.update(line_dict)

    try:
        next_line = next(line_generator)
        header_next, line_dict_next, level_next = parse_line(next_line)
    except StopIteration:
        return {k: v[0] if isinstance(v, tuple) else v for k, v in section.items()}, 0, None

    nested_values = []
    current_header = None

    while True:
        try:
            header_next, line_dict_next, level_next = parse_line(next_line)
        except StopIteration:
            break

        if not isinstance(line_dict_next, dict):
            continue

        if level_next > level_prev:  # Start of a new section
            if header_prev in ["precursor_len", "precursor_charge", "precursor_mz", "fragment_mz"]:
                current_header, nested_values = process_nested_values(
                    header_prev, current_header, nested_values, line_dict_next, section
                )
                try:
                    next_line = next(line_generator)
                    continue
                except StopIteration:
                    break
            else:
                subsection, _, next_line = parse_section(
                    line=parse_line(next_line),
                    line_generator=line_generator,
                )
                section[header_prev] = subsection
                continue

        elif level_prev == level_next:  # Same level
            update_section_with_line_dict(section, line_dict_next)
            header_prev = header_next
            level_prev = level_next
            try:
                next_line = next(line_generator)
            except StopIteration:
                break

        else:  # Going up a level
            break

    return {k: v[0] if isinstance(v, tuple) else v for k, v in section.items()}, level_next, next_line


def extract_file_version(line: str) -> str:
    """
    Extracts the version from a given line of an alphaDIA log file.

    Args:
        line (str): The line containing the version number.

    Returns:
        str: The extracted version number as a string, or None if not found.
    """
    version_pattern = r"version:\s*([\d\.]+)"
    match = re.search(version_pattern, line)
    return match.group(1) if match else None


def add_fdr_parameters(parameter_dict: dict, parsed_settings: dict) -> None:
    """
    Adds FDR parameters (e.g., ident_fdr_psm, ident_fdr_peptide) to the parameter dictionary.

    Args:
        parameter_dict (dict): The dictionary where the FDR parameters will be added.
        parsed_settings (dict): The parsed settings containing the FDR values.
    """
    fdr_value = float(parsed_settings["fdr"]["fdr"])
    fdr_level = parsed_settings["fdr"]["group_level"].strip()

    level_mapping = {"proteins": "ident_fdr_protein"}
    fdr_parameters = {"ident_fdr_psm": None, "ident_fdr_peptide": None, "ident_fdr_protein": None}
    fdr_parameters[level_mapping[fdr_level]] = fdr_value
    parameter_dict.update(fdr_parameters)


def get_min_max(list_of_elements: list) -> Tuple[int, int]:
    """
    Extracts the minimum and maximum values from a list of elements.

    Args:
        list_of_elements (list): A list containing at least two elements. The first element is the minimum,
                                  and the second element is the maximum (if three elements, the third is used as the max).

    Returns:
        Tuple[int, int]: A tuple containing the minimum and maximum values.
    """
    min_value = int(list_of_elements[0])
    if len(list_of_elements) == 3:
        max_value = int(list_of_elements[2])
    else:
        max_value = int(list_of_elements[1])
    return min_value, max_value


def extract_params(fname: str) -> ProteoBenchParameters:
    """
    Extracts parameters from a log file and returns them as a `ProteoBenchParameters` object.

    Args:
        fname (str): The path to the log file.

    Returns:
        ProteoBenchParameters: An object containing the extracted parameters.
    """
    try:
        with open(fname) as f:
            lines_read = f.readlines()
            lines = [line for line in lines_read if "──" in line]
        version = extract_file_version(lines_read[6])
    except:
        lines = [l for l in fname.read().decode("utf-8").splitlines() if "──" in l]
        version = extract_file_version(lines[6])

    line_generator = iter(lines)
    first_line = next(line_generator)

    parsed_settings, level, line = parse_section(line=parse_line(first_line), line_generator=line_generator)

    peptide_lengths = get_min_max(parsed_settings["library_prediction"]["precursor_len"])
    precursor_charges = get_min_max(parsed_settings["library_prediction"]["precursor_charge"])

    prec_tol = float(parsed_settings["search"]["target_ms1_tolerance"])
    frag_tol = float(parsed_settings["search"]["target_ms2_tolerance"])

    parameters = {
        "software_name": "AlphaDIA",
        "search_engine": "AlphaDIA",
        "software_version": version,
        "search_engine_version": version,
        "enable_match_between_runs": False,
        "precursor_mass_tolerance": prec_tol,
        "fragment_mass_tolerance": frag_tol,
        "enzyme": parsed_settings["library_prediction"]["enzyme"].strip(),
        "allowed_miscleavages": int(parsed_settings["library_prediction"]["missed_cleavages"]),
        "min_peptide_length": peptide_lengths[0],
        "max_peptide_length": peptide_lengths[1],
        "min_precursor_charge": precursor_charges[0],
        "max_precursor_charge": precursor_charges[1],
        "fixed_mods": parsed_settings["library_prediction"]["fixed_modifications"].strip(),
        "variable_mods": parsed_settings["library_prediction"]["variable_modifications"].strip(),
        "max_mods": int(parsed_settings["library_prediction"]["max_var_mod_num"]),
        "scan_window": int(parsed_settings["selection_config"]["max_size_rt"]),
        "second_pass": None,
        "protein_inference": parsed_settings["fdr"]["inference_strategy"].strip(),
        "predictors_library": "Built-in",
    }

    add_fdr_parameters(parameters, parsed_settings)
    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/log_alphadia_1.txt",
        "../../../test/params/log_alphadia_2.txt",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".csv"))
