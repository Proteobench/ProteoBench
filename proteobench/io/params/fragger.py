"""Functionality to parse FragPipe fragger.params parameter files.

FragPipe has a text based parameter file format which
separates parameters and their value using an equal sign. Optional comments are
expressed with a hash sign.
"""

from __future__ import annotations

import logging
import pathlib
import re
from collections import namedtuple
from io import BytesIO
from pathlib import PureWindowsPath
from typing import List, Optional, Tuple

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

logger = logging.getLogger(__name__)

Parameter = namedtuple("Parameter", ["name", "value", "comment"])

VERSION_NO_PATTERN = r"\d+(\.\d+)*"


def parse_params(l_of_str: List[str], sep: str = " = ") -> List[Parameter]:
    """
    Parse the FragPipe parameter file and return a list of Parameter objects.

    Args:
        l_of_str (List[str]): The lines of the FragPipe parameter file as a list of strings.
        sep (str): The separator between parameter names and values. Default is " = ".

    Returns:
        List[Parameter]: A list of Parameter namedtuples containing the parameter name, value, and any comment.
    """
    data = []
    for line in l_of_str:
        line = line.strip()
        logger.debug(line)
        if line.startswith("#"):
            continue  # Skip comments
        if not line:
            continue  # Skip empty lines
        if "#" in line:  # Handle lines with inline comments
            res = line.split("#")
            if len(res) == 1:
                comment = res[0]
                data.append(Parameter(None, None, comment.strip()))
                continue
            param, comment = [x.strip() for x in res]
        else:
            param = line
            comment = None
        res = param.strip().split(sep, maxsplit=1)
        if len(res) == 1:
            param = res[0].strip()
            data.append(Parameter(param, None, comment))
            continue
        param, value = [x.strip() for x in res]
        data.append(Parameter(param, value, comment))
    return data


def read_fragpipe_workflow(file: BytesIO, sep: str = "=") -> Tuple[str, List[Parameter]]:
    """
    Reads the FragPipe workflow file, extracting the header and parameters.

    Args:
        file (BytesIO): The FragPipe workflow file to read.
        sep (str): The separator used between parameter names and values. Default is "=".

    Returns:
        Tuple[str, List[Parameter]]: A tuple containing the header and a list of Parameter objects.
    """
    l_of_str = file.read().decode("utf-8").splitlines()
    header = l_of_str[0][1:].strip()  # Skip leading '#' in the header
    return header, parse_params(l_of_str, sep=sep)


def extract_params(file: BytesIO) -> ProteoBenchParameters:
    """
    Parse FragPipe parameter files and extract relevant parameters into a `ProteoBenchParameters` object.

    Args:
        file (BytesIO): The FragPipe parameter file to parse.

    Returns:
        ProteoBenchParameters: The extracted parameters encapsulated in a ProteoBenchParameters object.
    """
    header, fragpipe_params = read_fragpipe_workflow(file)
    fragpipe_params = pd.DataFrame.from_records(fragpipe_params, columns=Parameter._fields).set_index(
        Parameter._fields[0]
    )["value"]

    # Extract version from header
    match = re.search(VERSION_NO_PATTERN, header)
    if match:
        header = match.group()

    # Initialize ProteoBenchParameters
    params = ProteoBenchParameters()
    params.software_name = "FragPipe"
    params.software_version = header
    params.search_engine = "MSFragger"

    try:
        # Extract MSFragger executable version
        msfragger_executable = fragpipe_params.loc["fragpipe-config.bin-msfragger"]
        msfragger_executable = PureWindowsPath(msfragger_executable).name
        match = re.search(VERSION_NO_PATTERN, msfragger_executable)
        if match:
            msfragger_executable = match.group()
    except KeyError:
        msfragger_executable = ""

    params.search_engine_version = msfragger_executable

    # Enzyme and cleavage settings
    enzyme = fragpipe_params.loc["msfragger.search_enzyme_name_1"]
    if fragpipe_params.loc["msfragger.search_enzyme_name_2"] != "null":
        enzyme += f"|{fragpipe_params.loc['msfragger.search_enzyme_name_2']}"
    if enzyme == "stricttrypsin":
        enzyme = "Trypsin/P"  # strict trypsin: always cut after K and R
    elif enzyme == "trypsin":
        enzyme = "Trypsin"  # trypsin: do not cut before P
    params.enzyme = enzyme
    params.allowed_miscleavages = int(fragpipe_params.loc["msfragger.allowed_missed_cleavage_1"])

    # Modifications
    params.fixed_mods = fragpipe_params.loc["msfragger.table.fix-mods"]
    params.variable_mods = fragpipe_params.loc["msfragger.table.var-mods"]
    params.max_mods = int(fragpipe_params.loc["msfragger.max_variable_mods_per_peptide"])

    # Peptide length
    params.min_peptide_length = int(fragpipe_params.loc["msfragger.digest_min_length"])
    params.max_peptide_length = int(fragpipe_params.loc["msfragger.digest_max_length"])

    # Precursor mass tolerance
    precursor_mass_units = "Da"
    if int(fragpipe_params.loc["msfragger.precursor_mass_units"]):
        precursor_mass_units = "ppm"
    params.precursor_mass_tolerance = f'[{fragpipe_params.loc["msfragger.precursor_mass_lower"]} {precursor_mass_units}, {fragpipe_params.loc["msfragger.precursor_mass_upper"]} {precursor_mass_units}]'

    # Fragment mass tolerance
    fragment_mass_units = "Da"
    if int(fragpipe_params.loc["msfragger.fragment_mass_units"]):
        fragment_mass_units = "ppm"
    params.fragment_mass_tolerance = f'[-{fragpipe_params.loc["msfragger.fragment_mass_tolerance"]} {fragment_mass_units}, {fragpipe_params.loc["msfragger.fragment_mass_tolerance"]} {fragment_mass_units}]'

    # Quantification settings
    if fragpipe_params.loc["quantitation.run-label-free-quant"] == "true":
        params.ident_fdr_protein = fragpipe_params.loc["ionquant.proteinfdr"]
        params.ident_fdr_peptide = fragpipe_params.loc["ionquant.peptidefdr"]
        params.ident_fdr_psm = fragpipe_params.loc["ionquant.ionfdr"]
    elif fragpipe_params.loc["diann.run-dia-nn"] == "true":
        params.ident_fdr_protein = fragpipe_params.loc["diann.q-value"]
        params.ident_fdr_peptide = fragpipe_params.loc["diann.q-value"]
        params.ident_fdr_psm = fragpipe_params.loc["diann.q-value"]

    # Precursor charge settings
    if fragpipe_params.loc["msfragger.override_charge"] == "true":
        params.min_precursor_charge = int(fragpipe_params.loc["msfragger.misc.fragger.precursor-charge-lo"])
        params.max_precursor_charge = int(fragpipe_params.loc["msfragger.misc.fragger.precursor-charge-hi"])
    else:
        params.min_precursor_charge = 1
        params.max_precursor_charge = None

    # Match between runs and quantification method settings
    if fragpipe_params.loc["quantitation.run-label-free-quant"] == "true":
        params.enable_match_between_runs = bool(fragpipe_params.loc["ionquant.mbr"])
    elif fragpipe_params.loc["diann.run-dia-nn"] == "true":
        diann_quant_dict = {
            1: "Any LC (high accuracy)",
            2: "Any LC (high precision)",
            3: "Robust LC (high accuracy)",
            4: "Robust LC (high precision)",
        }
        if "--reanalyse" in fragpipe_params.loc["diann.fragpipe.cmd-opts"]:
            params.enable_match_between_runs = True
        else:
            params.enable_match_between_runs = False
        params.quantification_method = diann_quant_dict[int(fragpipe_params.loc["diann.quantification-strategy"])]

    # Protein inference settings
    if fragpipe_params.loc["protein-prophet.run-protein-prophet"] == "true":
        params.protein_inference = f"ProteinProphet: {fragpipe_params.loc['protein-prophet.cmd-opts']}"

    return params


if __name__ == "__main__":
    # Process FragPipe workflow file and extract parameters
    files = [
        "../../../test/params/fragpipe.workflow",
        "../../../test/params/fragpipe_win_paths.workflow",
        "../../../test/params/fragpipe_v22.workflow",
    ]

    for file_path in files:
        file = pathlib.Path(file_path)
        with open(file, "rb") as f:
            _, data = read_fragpipe_workflow(f)
        df = pd.DataFrame.from_records(data, columns=Parameter._fields).set_index(Parameter._fields[0])
        df.to_csv(file.with_suffix(".csv"))
        with open(file, "rb") as f:
            params = extract_params(f)
        series = pd.Series(params.__dict__)
        print(series)
        series.to_csv(file.parent / f"{file.stem}_extracted_params.csv")
