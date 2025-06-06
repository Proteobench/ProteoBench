"""
Functionality to parse FragPipe fragger.params parameter files.

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
from typing import List

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

logger = logging.getLogger(__name__)

Parameter = namedtuple("Parameter", ["name", "value", "comment"])

VERSION_NO_PATTERN = r"MSFragger-(.+)\.jar"


def parse_phi_report_filters(phi_report_cmd: str) -> tuple[float, float, float]:
    """
    Parse the filters from the phi-report command string.

    Parameters
    ----------
    phi_report_cmd : str
        The command string from the phi-report filter.

    Returns
    -------
    tuple of (float, float, float)
        A tuple containing the PSM, peptide, and protein FDR values.
    """
    # Define default FDR values
    default_fdr = 0.01

    # Define regex patterns for FDR values
    fdr_patterns = {
        "psm": r"--psm\s+(\d+\.\d+)",
        "peptide": r"--pep\s+(\d+\.\d+)",
        "protein": r"--prot\s+(\d+\.\d+)",
    }

    # Extract FDR values using regex
    fdr_values = {
        key: float(match.group(1)) if (match := re.search(pattern, phi_report_cmd)) else default_fdr
        for key, pattern in fdr_patterns.items()
    }

    return fdr_values["psm"], fdr_values["peptide"], fdr_values["protein"]


def parse_params(l_of_str: List[str], sep: str = " = ") -> List[Parameter]:
    """
    Parse the FragPipe parameter file and return a list of Parameter objects.

    Parameters
    ----------
    l_of_str : List[str]
        The lines of the FragPipe parameter file as a list of strings.
    sep : str, optional
        The separator between parameter names and values. Default is " = ".

    Returns
    -------
    List[Parameter]
        A list of Parameter namedtuples containing the parameter name, value, and any comment.
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


def read_fragpipe_workflow(file: BytesIO, sep: str = "=") -> tuple[str, str | None, list[Parameter]]:
    """
    Read the FragPipe workflow file and return the header and a list of Parameter objects.

    Parameters
    ----------
    file : BytesIO
        The FragPipe workflow file to read.
    sep : str, optional
        The separator used between parameter names and values. Default is "=".

    Returns
    -------
    tuple of (str, list of Parameter)
        A tuple containing the header and a list of Parameter objects.
    """
    l_of_str = file.read().decode("utf-8").splitlines()
    header = l_of_str[0][1:].strip()  # Skip leading '#' in the header
    msfragger_version = None
    fragpipe_version = None
    for ss in l_of_str[1:]:
        if ss.startswith("# MSFragger version"):
            msfragger_version = ss.split(" ")[-1].strip()
            break
        elif ss.startswith("fragpipe-config.bin-msfragger"):
            path = ss.split("=")[-1].strip()
            if "/" in path:
                filename = path.split("/")[-1]
            elif "\\" in path:
                filename = path.split("\\")[-1]
            else:
                filename = path
            match = re.search(VERSION_NO_PATTERN, filename)
            if match:
                msfragger_version = match.group(1)
        if ss.startswith("# FragPipe version"):
            fragpipe_version = ss.split(" ")[-1].strip()
    return header, msfragger_version, fragpipe_version, parse_params(l_of_str, sep=sep)


def extract_params(file: BytesIO) -> ProteoBenchParameters:
    """
    Parse FragPipe parameter files and extract relevant parameters into a `ProteoBenchParameters` object.

    Parameters
    ----------
    file : BytesIO
        The FragPipe parameter file to parse.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    header, msfragger_version, fragpipe_version, fragpipe_params = read_fragpipe_workflow(file)
    fragpipe_params = pd.DataFrame.from_records(fragpipe_params, columns=Parameter._fields).set_index(
        Parameter._fields[0]
    )["value"]

    # Extract version from header
    if not fragpipe_version:
        fragpipe_version = re.match(r"FragPipe \((\d+\.\d+.*)\)", header).group(1)

    # Initialize ProteoBenchParameters
    params = ProteoBenchParameters()
    params.software_name = "FragPipe"
    params.software_version = fragpipe_version
    params.search_engine = "MSFragger"
    params.search_engine_version = msfragger_version

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

    if fragpipe_params.loc["diann.run-dia-nn"] == "true":
        params.ident_fdr_protein = fragpipe_params.loc["diann.q-value"]
        params.ident_fdr_peptide = None
        params.ident_fdr_psm = fragpipe_params.loc["diann.q-value"]
        params.abundance_normalization_ions = None

    else:
        phi_report_cmd = fragpipe_params.loc["phi-report.filter"]
        params.ident_fdr_psm, params.ident_fdr_peptide, params.ident_fdr_protein = parse_phi_report_filters(
            phi_report_cmd
        )

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
        params.enable_match_between_runs = (
            "diann.fragpipe.cmd-opts" in fragpipe_params.index
            and "--reanalyse" in fragpipe_params.loc["diann.fragpipe.cmd-opts"]
        ) or ("diann.cmd-opts" in fragpipe_params.index and "--reanalyse" in fragpipe_params.loc["diann.cmd-opts"])
        params.quantification_method = diann_quant_dict[int(fragpipe_params.loc["diann.quantification-strategy"])]

    # Protein inference settings
    if fragpipe_params.loc["protein-prophet.run-protein-prophet"] == "true":
        params.protein_inference = f"ProteinProphet: {fragpipe_params.loc['protein-prophet.cmd-opts']}"

    params.fill_none()

    return params


if __name__ == "__main__":
    # Process FragPipe workflow file and extract parameters
    files = [
        "../../../test/params/fragpipe.workflow",
        "../../../test/params/fragpipe_older.workflow",
        "../../../test/params/fragpipe_win_paths.workflow",
        "../../../test/params/fragpipe_v22.workflow",
        "../../../test/params/fragpipe_fdr_test.workflow",
        "../../../test/params/fragpipe-version.workflow",
    ]

    for file_path in files:
        file = pathlib.Path(file_path)
        with open(file, "rb") as f:
            _, _, _, data = read_fragpipe_workflow(f)
        df = pd.DataFrame.from_records(data, columns=Parameter._fields).set_index(Parameter._fields[0])
        df.to_csv(file.with_suffix(".csv"))
        with open(file, "rb") as f:
            params = extract_params(f)
        series = pd.Series(params.__dict__)
        print(series)
        print("\n")
        series.to_csv(file.parent / f"{file.stem}_extracted_params.csv")
