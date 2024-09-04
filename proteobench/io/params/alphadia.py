import re
from proteobench.io.params import ProteoBenchParameters
import pathlib
import pandas as pd

levels = [0, 1, 5, 9, 13, 17]

ANSI_REGEX = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")


def parse_line(line):
    # Remove the info part and convert ansi
    line = ANSI_REGEX.sub("", line[22:].strip())
    # Split the string to tab part and setting part
    tab, setting = line.split("──")
    setting_list = setting.split(":")
    if len(setting_list) == 1:
        setting_dict = {setting_list[0]: None}
    else:
        setting_dict = {setting_list[0]: setting_list[1]}
    # Convert tab to level
    level = levels.index(len(tab))

    # Return header, parsed setting, and the level
    return setting_list[0], setting_dict, level


def parse_section(
    line,
    line_generator,
):
    section = {}

    # Parse the line (both level and dictionary)
    header_prev, line_dict, level_prev = line
    section.update(line_dict)

    try:
        # Get the next line to know what to do
        next_line = next(line_generator)
        header_next, line_dict_next, level_next = parse_line(next_line)
    except:
        # If no lines left, go up a level, returning the sectino so far
        return section, 0, None

    while True:
        # If no more lines go up a level
        try:
            header_next, line_dict_next, level_next = parse_line(next_line)
        except:
            break

        # If the next line is start of new section again
        if level_next > level_prev:
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
            section.update(line_dict_next)
            header_prev = header_next
            level_prev = level_next
            try:
                next_line = next(line_generator)
            except:
                break

        # The next line needs to go up and output the section
        # Also the new line should be returned
        else:
            return section, level_next, next_line

    return section, 0, None


def extract_file_version(line):
    # Regex pattern to extract the version number
    version_pattern = r"version:\s*([\d\.]+)"

    # Search for the version number in the line
    match = re.search(version_pattern, line)

    # Extract and print the version number if found
    version = match.group(1) if match else None
    return version


def add_fdr_parameters(parameter_dict, parsed_settings):
    fdr_value = float(parsed_settings["fdr"]["fdr"])
    fdr_level = parsed_settings["fdr"]["group_level"].strip()

    level_mapping = {"proteins": "ident_fdr_protein"}
    fdr_parameters = {"ident_fdr_psm": None, "ident_fdr_peptide": None, "ident_fdr_protein": None}
    fdr_parameters[level_mapping[fdr_level]] = fdr_value
    parameter_dict.update(fdr_parameters)


def get_min_max(list_of_elements):
    if "(user defined)" in list_of_elements[1]:
        min_value = int(list_of_elements[1].replace("(user defined)", ""))
        if len(list_of_elements) == 4:
            max_value = int(list_of_elements[3].replace("(user defined)", ""))
        else:
            max_value = int(list_of_elements[2])
    else:
        min_value = int(list_of_elements[0])
        if len(list_of_elements) == 3:
            max_value = int(list_of_elements[2].replace("(user defined)", ""))
        else:
            max_value = int(list_of_elements[1])
    return min_value, max_value


def extract_params(fname):
    with open(fname) as f:
        lines_read = f.readlines()
        lines = [line for line in lines_read if "──" in line]

    version = extract_file_version(lines_read[6])

    line_generator = iter(lines)
    first_line = next(line_generator)

    parsed_settings, level, line = parse_section(line=parse_line(first_line), line_generator=line_generator)

    peptide_lengths = get_min_max(list(parsed_settings["library_prediction"]["precursor_len"].keys()))
    precursor_charges = get_min_max(list(parsed_settings["library_prediction"]["precursor_charge"].keys()))

    if "(user defined)" in parsed_settings["search"]["target_ms1_tolerance"]:
        prec_tol = float(parsed_settings["search"]["target_ms1_tolerance"].replace("(user defined)", ""))
    else:
        prec_tol = float(parsed_settings["search"]["target_ms1_tolerance"])
    if "(user defined)" in parsed_settings["search"]["target_ms2_tolerance"]:
        frag_tol = float(parsed_settings["search"]["target_ms2_tolerance"].replace("(user defined)", ""))
    else:
        frag_tol = float(parsed_settings["search"]["target_ms2_tolerance"])

    parameters = {
        "software_name": "AlphaDIA",
        "search_engine": "AlphaDIA",
        "software_version": version,
        "search_engine_version": version,
        "enable_match_between_runs": "?",
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
        "max_mods": int(parsed_settings["library_prediction"]["max_var_mod_num"].replace("(user defined)", "")),
        "scan_window": int(parsed_settings["selection_config"]["max_size_rt"].replace("(user defined)", "")),
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
