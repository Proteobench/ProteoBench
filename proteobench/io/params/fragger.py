"""Functionality to parse FragPipe fragger.params parameter files.

FragPipe has a text based paramter file format which
separates parameters and their value using an equal sign. Optional comments are
expressed with a hash sign.
"""

from __future__ import annotations

import logging
import re
from collections import namedtuple
from io import BytesIO
from pathlib import PureWindowsPath

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

logger = logging.getLogger(__name__)

Parameter = namedtuple("Parameter", ["name", "value", "comment"])

VERSION_NO_PATTERN = r"\d+(\.\d+)*"


def parse_params(l_of_str: list[str], sep: str = " = ") -> list[Parameter]:
    """Read FragPipe parameter file as list of records."""
    data = []
    for line in l_of_str:
        line = line.strip()
        logger.debug(line)
        # ! logic below also allows to keep the comments as comments
        if line.startswith("#"):
            continue
        if not line:
            continue
        if "#" in line:
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


def read_fragpipe_workflow(file: BytesIO, sep: str = "=") -> list[Parameter]:
    l_of_str = file.read().decode("utf-8").splitlines()
    header = l_of_str[0][1:].strip()
    return header, parse_params(l_of_str, sep=sep)


def extract_params(file: BytesIO) -> ProteoBenchParameters:
    """Parse FragPipe parameter files and extract relevant parameters."""
    header, fragpipe_params = read_fragpipe_workflow(file)
    fragpipe_params = pd.DataFrame.from_records(fragpipe_params, columns=Parameter._fields).set_index(
        Parameter._fields[0]
    )["value"]

    match = re.search(VERSION_NO_PATTERN, header)

    if match:
        header = match.group()

    params = ProteoBenchParameters()
    params.software_name = "FragPipe"
    params.software_version = header
    params.search_engine = "MSFragger"

    try:
        msfragger_executable = fragpipe_params.loc["fragpipe-config.bin-msfragger"]
        msfragger_executable = PureWindowsPath(msfragger_executable).name
        match = re.search(VERSION_NO_PATTERN, msfragger_executable)

        if match:
            msfragger_executable = match.group()
    except KeyError:
        msfragger_executable = ""

    params.search_engine_version = msfragger_executable
    enzyme = fragpipe_params.loc["msfragger.search_enzyme_name_1"]
    if fragpipe_params.loc["msfragger.search_enzyme_name_2"] != "null":
        enzyme += f"|{fragpipe_params.loc['msfragger.search_enzyme_name_2']}"
    params.enzyme = enzyme
    params.allowed_miscleavages = fragpipe_params.loc["msfragger.allowed_missed_cleavage_1"]
    # TODO: Fragpipe reports "0.0" mass shift for each unmodified AA here, which is not useful and could be removed
    params.fixed_mods = fragpipe_params.loc["msfragger.table.fix-mods"]
    # TODO: Fragpipe reports a lot of default suggestions for variable mods and assigns them as 'false' here,
    # which is not useful and could be removed, i.e. only retain true variable mods
    params.variable_mods = fragpipe_params.loc["msfragger.table.var-mods"]
    params.max_mods = fragpipe_params.loc["msfragger.max_variable_mods_per_peptide"]
    params.min_peptide_length = fragpipe_params.loc["msfragger.digest_min_length"]
    params.max_peptide_length = fragpipe_params.loc["msfragger.digest_max_length"]

    precursor_mass_units = "Da"
    if int(fragpipe_params.loc["msfragger.precursor_mass_units"]):
        precursor_mass_units = "ppm"
    params.precursor_mass_tolerance = f'{fragpipe_params.loc["msfragger.precursor_mass_lower"]} {precursor_mass_units}|{fragpipe_params.loc["msfragger.precursor_mass_upper"]} {precursor_mass_units}'

    fragment_mass_units = "Da"
    if int(fragpipe_params.loc["msfragger.fragment_mass_units"]):
        fragment_mass_units = "ppm"
    params.fragment_mass_tolerance = f'{fragpipe_params.loc["msfragger.fragment_mass_tolerance"]} {fragment_mass_units}'
    # ! ionquant is not necessarily fixed?
    if fragpipe_params.loc["quantitation.run-label-free-quant"] == "true":
        params.ident_fdr_protein = fragpipe_params.loc["ionquant.proteinfdr"]
        params.ident_fdr_peptide = fragpipe_params.loc["ionquant.peptidefdr"]
        params.ident_fdr_psm = fragpipe_params.loc["ionquant.ionfdr"]
    elif fragpipe_params.loc["diann.run-dia-nn"] == "true":
        params.ident_fdr_protein = fragpipe_params.loc["diann.q-value"]
        params.ident_fdr_peptide = fragpipe_params.loc["diann.q-value"]
        params.ident_fdr_psm = fragpipe_params.loc["diann.q-value"]

    # I think this is incorrect? The values are stored as proportions in the fragpipe.workflow file? Commenting out for now
    # for key in ["ident_fdr_protein", "ident_fdr_peptide", "ident_fdr_psm"]:
    #     value = getattr(params, key)
    #     try:
    #         value = int(value) / 100
    #         setattr(params, key, value)
    #     except ValueError:
    #         logging.warning(f"Could not convert {value} to int.")

    if fragpipe_params.loc["msfragger.override_charge"] == "true":
        params.min_precursor_charge = int(fragpipe_params.loc["msfragger.misc.fragger.precursor-charge-lo"])
        params.max_precursor_charge = int(fragpipe_params.loc["msfragger.misc.fragger.precursor-charge-hi"])
    else:  # Fragpipe takes charge info from data, this is the default
        params.min_precursor_charge = 1
        params.max_precursor_charge = None
    if fragpipe_params.loc["quantitation.run-label-free-quant"] == "true":
        params.enable_match_between_runs = bool(fragpipe_params.loc["ionquant.mbr"])
    elif fragpipe_params.loc["diann.run-dia-nn"] == "true":
        diann_quant_dict = {1: 'Any LC (high accuracy)', 2: 'Any LC (high precision)', 3: 'Robust LC (high accuracy)', 4:'Robust LC (high precision)'}
        if "--reanalyse" in fragpipe_params.loc["diann.fragpipe.cmd-opts"]:
            params.enable_match_between_runs = True
        else:
            params.enable_match_between_runs = False
        params.quantification_method_DIANN = diann_quant_dict[int(fragpipe_params.loc["diann.quantification-strategy"])]
    if fragpipe_params.loc["protein-prophet.run-protein-prophet"] == "true":
        params.protein_inference = "ProteinProphet: {}".format(fragpipe_params.loc["protein-prophet.cmd-opts"])

    return params


if __name__ == "__main__":
    # TODO create test csv files
    import pathlib
    from pprint import pprint

    file = pathlib.Path("../../../test/params/fragpipe.workflow")
    with open(file, "rb") as f:
        _, data = read_fragpipe_workflow(f)
    df = pd.DataFrame.from_records(data, columns=Parameter._fields).set_index(Parameter._fields[0])
    df.to_csv(file.with_suffix(".csv"))
    with open(file, "rb") as f:
        params = extract_params(f)
    pprint(params.__dict__)
    series = pd.Series(params.__dict__)
    series.to_csv(file.parent / f"{file.stem}_extracted_params.csv")

    file = pathlib.Path("../../../test/params/fragpipe_win_paths.workflow")
    with open(file, "rb") as f:
        _, data = read_fragpipe_workflow(f)
    df = pd.DataFrame.from_records(data, columns=Parameter._fields).set_index(Parameter._fields[0])
    df.to_csv(file.with_suffix(".csv"))
    with open(file, "rb") as f:
        params = extract_params(f)
    pprint(params.__dict__)
    series = pd.Series(params.__dict__)
    series.to_csv(file.parent / f"{file.stem}_extracted_params.csv")

    file = pathlib.Path("../../../test/params/fragpipe_v22.workflow")
    with open(file, "rb") as f:
        _, data = read_fragpipe_workflow(f)
    df = pd.DataFrame.from_records(data, columns=Parameter._fields).set_index(Parameter._fields[0])
    df.to_csv(file.with_suffix(".csv"))
    with open(file, "rb") as f:
        params = extract_params(f)
    pprint(params.__dict__)
    series = pd.Series(params.__dict__)
    series.to_csv(file.parent / f"{file.stem}_extracted_params.csv")
