"""
Extract parameters from a MetaMorpheus TOML file and convert them to a pandas Series.
"""

import os
import tomllib as toml
from io import BytesIO
from pathlib import Path, PosixPath
from typing import IO, Tuple, Union

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def load_files(file1: Union[str, IO], file2: Union[str, IO]) -> Tuple[Union[str, None], Union[dict, None]]:
    """
    Load two files (IO objects or file paths), returning:
    - The first line from a plain text file as the version string
    - A dictionary parsed from a TOML file

    Returns
    -------
    Tuple[Union[str, None], Union[dict, None]]
        versions_line, settings_dict
    """
    versions_line = None
    settings = None

    def try_parse(file: Union[str, IO]):
        nonlocal versions_line, settings

        # Case 1: Path
        if isinstance(file, (str, PosixPath, Path)):
            # Try TOML
            try:
                with open(file, "rb") as f:
                    settings_candidate = toml.load(f)
                    settings = settings_candidate
                    return
            except Exception:
                pass
            # Try version line
            try:
                with open(file, "r", encoding="utf-8") as f:
                    versions_line = f.readline().strip()
                    return
            except Exception:
                pass

        # Case 2: IO object
        elif hasattr(file, "read"):
            try:
                file.seek(0)
                # Try loading directly (only works if binary)
                settings_candidate = toml.load(file)
                settings = settings_candidate
                return
            except Exception:
                pass
            try:
                # Try to convert to binary buffer if in text mode
                file.seek(0)
                content = file.read()
                if isinstance(content, str):
                    buffer = BytesIO(content.encode("utf-8"))
                    settings_candidate = toml.load(buffer)
                    settings = settings_candidate
                    return
            except Exception:
                pass
            try:
                file.seek(0)
                line = file.readline()
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                versions_line = line.strip()
                return
            except Exception:
                pass

    for f in (file1, file2):
        try_parse(f)

    if versions_line and settings:
        print("Successfully parsed both versions and settings.")
    else:
        print("Could not identify both versions and settings from the provided files.")

    return versions_line, settings


def parse_modifications(mods: str) -> list:
    """
    Parse modifications from a string or list format into a standardized list.

    Parameters
    ----------
    mods : Union[str]
        Modifications in string format (e.g., ""Common Fixed\tCarbamidomethyl on C\t\tCommon Fixed\tCarbamidomethyl on U"")

    Returns
    -------
    list
        List of modifications.
    """
    parsed_mod_list = []
    mod_list = mods.split("\t\t")
    for mod in mod_list:
        mod_spec = mod.split("\t")[1]
        parsed_mod_list.append(mod_spec)

    return ";".join(parsed_mod_list) if parsed_mod_list else []


def format_tolerances(tolerance: str) -> str:
    """
    Format mass tolerance values from a string to a standardized format.

    Parameters
    ----------
    tolerance : str
        Mass tolerance in string format (e.g., "±20.0000 PPM")

    Returns
    -------
    str
        Formatted mass tolerance as a string.
    """
    tolerance, unit = tolerance.split()
    tolerance = tolerance.strip("±")
    tolerance = float(tolerance)
    formatted_tolerance = f"[-{tolerance:.2f} {unit}, {tolerance:.2f} {unit}]"
    return formatted_tolerance


def extract_params(file_path_1, file_path_2) -> ProteoBenchParameters:
    params = ProteoBenchParameters()

    versions_line, settings = load_files(file_path_1, file_path_2)

    params.software_name = "MetaMorpheus"
    params.search_engine = "MetaMorpheus"
    params.software_version = versions_line.split()[2]
    params.enzyme = settings["CommonParameters"]["DigestionParams"]["Protease"]
    params.semi_specific = settings["CommonParameters"]["DigestionParams"]["FragmentationTerminus"] != "Both"
    params.allowed_miscleavages = settings["CommonParameters"]["DigestionParams"]["MaxMissedCleavages"]
    params.fixed_mods = parse_modifications(settings["CommonParameters"]["ListOfModsFixed"])
    params.variable_mods = parse_modifications(settings["CommonParameters"]["ListOfModsVariable"])
    params.precursor_mass_tolerance = format_tolerances(settings["CommonParameters"]["PrecursorMassTolerance"])
    params.fragment_mass_tolerance = format_tolerances(settings["CommonParameters"]["ProductMassTolerance"])
    params.min_peptide_length = settings["CommonParameters"]["DigestionParams"]["MinPeptideLength"]
    params.max_peptide_length = settings["CommonParameters"]["DigestionParams"]["MaxPeptideLength"]
    params.max_mods = settings["CommonParameters"]["DigestionParams"]["MaxModsForPeptide"]
    params.min_precursor_charge = settings["CommonParameters"]["PrecursorDeconvolutionParameters"][
        "MinAssumedChargeState"
    ]
    params.max_precursor_charge = settings["CommonParameters"]["PrecursorDeconvolutionParameters"][
        "MaxAssumedChargeState"
    ]
    params.enable_match_between_runs = bool(settings["SearchParameters"]["MatchBetweenRuns"])
    params.quantification_method = "FlashLFQ"
    params.protein_inference = "Parsimony" if settings["SearchParameters"]["DoParsimony"] == True else None
    params.abundance_normalization_ions = True if settings["SearchParameters"]["Normalize"] == True else False
    params.ident_fdr_psm = "{}".format(settings["CommonParameters"]["QValueThreshold"])
    params.ident_fdr_peptide = None
    params.ident_fdr_protein = None
    params.search_engine_version = None
    return params


if __name__ == "__main__":
    fnames = [
        [
            "../../../test/params/metamorpheus_search_task_config.toml",
            "../../../test/params/metamorpheus_version_result.txt",
        ],
        # Reverse order
        [
            "../../../test/params/metamorpheus_version_result.txt",
            "../../../test/params/metamorpheus_search_task_config.toml",
        ],
    ]

    for file1, file2 in fnames:
        # Extract parameters from the file
        parameters = extract_params(file1, file2)
        print(parameters.__dict__)
        # With streamlit the IO object is used -> open files
        print("\n")
        with open(file1, "r") as f1, open(file2, "r") as f2:
            parameters = extract_params(f1, f2)

            f1.seek(0), f2.seek(0)
        print("\n")
        print(parameters.__dict__)
        series = pd.Series(parameters.__dict__)
        series.to_csv("../../../test/params/metamorpheus_parameters.csv")
        print("\n")
