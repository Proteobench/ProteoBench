import re
from proteobench.io.params import ProteoBenchParameters
import pathlib
import pandas as pd
from typing import Iterable, Tuple, Optional

levels = [0, 1, 5, 9, 13, 17]

ANSI_REGEX = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")

# Function to clean up "(default)" and "(user defined)" substrings
def clean_line(line: str) -> str:
    line = ANSI_REGEX.sub("", line)  
    return line.strip()

def parse_line(line: str) -> Tuple[str, dict, int]:
    """
    Parse a log line into a tuple.

    Parameter
    ---------
    line: str
        A log line.

    Returns
    -------
    str:
        Setting name
    dict:
        Dictionary of setting name and value
    int:
        The indentation level
    """
    # Remove the info part and convert ansi
    line = clean_line(line[22:])
    try:
        # Split the string to tab part and setting part
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
        
        # Convert tab to level
        level = levels.index(len(tab))
    except:
        return "", {}, 0
    # Return header, parsed setting, and the level
    return setting_list[0], setting_dict, level 
    
def parse_section(
    line: Tuple[str, dict, int],
    line_generator: Iterable,
) -> Tuple[dict, int, Optional[Tuple]]:
    """
    Parse a section into a dictionary.

    All settings at the same indentation level are added to a dictionary.

    Parameter
    ---------
    line: str
        First parsed line of a new section
    line_generator: Generator
        The line generator of log file lines

    Return
    ------
    dict:
        The parsed section
    int:
        The indentation level of the line after the section
    next_line:
        The line after the section
    """
    section = {}

    # Parse the line (both level and dictionary)
    header_prev, line_dict, level_prev = line
    section.update(line_dict)

    try:
        # Get the next line to know what to do
        next_line = next(line_generator)
        header_next, line_dict_next, level_next = parse_line(next_line)
    except:
        # If no lines left, go up a level, returning the section so far
        return {k: v[0] if isinstance(v, tuple) else v for k, v in section.items()}, 0, None
    
    nested_values = []
    current_header = None

    while True:
        # If no more lines go up a level
        try:
            header_next, line_dict_next, level_next = parse_line(next_line)
        except:
            break

        if not isinstance(line_dict_next, dict):
            continue

        # If the next line is start of new section again
        if level_next > level_prev:
            
            if header_prev in ['precursor_len', 'precursor_charge', 'precursor_mz', 'fragment_mz']:
                if current_header is None or current_header != header_prev:
                    nested_values = []
                    current_header = header_prev

                # Collect all values under this nested section
                value = list(line_dict_next.keys())[0].split()[0]  # Extract value before space
                nested_values.append(int(value))

                # If "user defined", overwrite the default
                if "(user defined)" in list(line_dict_next.keys())[0]:
                    nested_values.pop(-2)

                
                # Save the values in the section
                section[header_prev] = nested_values
                

                try:
                    next_line = next(line_generator)
                    continue
                except:
                    break
        
            else:
            # Get the subsection

                subsection, _, next_line = parse_section(
                    line=parse_line(next_line),
                    line_generator=line_generator,
                )
                # Add this subsection to new section
                # A new line is already outputted so continue
                section[header_prev] = subsection
                continue

        # if new line is at same level
        elif level_prev == level_next:
            if isinstance(line_dict_next, dict):
                for key, (value, flag) in line_dict_next.items():
                    if key in section and flag == "user defined":
                        section[key] = value
                    elif key not in section:
                        section[key] = value
            header_prev = header_next
            level_prev = level_next
            try:
                next_line = next(line_generator)
            except:
                break

        # The next line needs to go up and output the section
        # Also the new line should be returned
        else:
            break
    
    
    return {k: v[0] if isinstance(v, tuple) else v for k, v in section.items()}, level_next, next_line


def extract_file_version(line: str) -> str:
    """
    Extract file version from alphaDIA log file line.

    Parameter
    ---------
    line: str
        The line containing the version number.

    Return
    ------
    str
        Version number.
    """
    # Regex pattern to extract the version number
    version_pattern = r"version:\s*([\d\.]+)"

    # Search for the version number in the line
    match = re.search(version_pattern, line)

    # Extract and print the version number if found
    version = match.group(1) if match else None
    return version


def add_fdr_parameters(parameter_dict: dict, parsed_settings: dict) -> None:
    """
    Add fdr parameters to the parameter dictionary.

    Parameters
    ----------
    parameter_dict: dict
        Dictionary where proteobench parameters should be stored.
    parsed_settings: dict
        Dictionary of parsed maxDIA log-file.
    """
    fdr_value = float(parsed_settings["fdr"]["fdr"])
    fdr_level = parsed_settings["fdr"]["group_level"].strip()

    level_mapping = {"proteins": "ident_fdr_protein"}
    fdr_parameters = {"ident_fdr_psm": None, "ident_fdr_peptide": None, "ident_fdr_protein": None}
    fdr_parameters[level_mapping[fdr_level]] = fdr_value
    parameter_dict.update(fdr_parameters)


def get_min_max(list_of_elements: list) -> Tuple[int, int]:
    min_value = int(list_of_elements[0])
    if len(list_of_elements) == 3:
        max_value = int(list_of_elements[2])
    else:
        max_value = int(list_of_elements[1])
    return min_value, max_value

def extract_params(fname: str) -> ProteoBenchParameters:
    with open(fname) as f:
        lines_read = f.readlines()
        lines = [line for line in lines_read if "──" in line]

    version = extract_file_version(lines_read[6])

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
        "enable_match_between_runs": False, # Not in AlphaDIA AFAIK
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
        "quantification_method_DIANN": None,
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
