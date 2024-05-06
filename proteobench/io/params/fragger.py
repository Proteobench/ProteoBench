"""Functionality to parse FragPipe fragger.params parameter files.

FragPipe has a text based paramter file format which
separates paramters and their value using an equal sign. Optional comments are
expressed with a hash sign.
"""

from __future__ import annotations

import logging
import re
from collections import namedtuple
from io import BytesIO
from pathlib import Path

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

    msfragger_executable = fragpipe_params.loc["fragpipe-config.bin-msfragger"]
    msfragger_executable = Path(msfragger_executable).name
    match = re.search(VERSION_NO_PATTERN, msfragger_executable)

    if match:
        msfragger_executable = match.group()

    params.search_engine_version = msfragger_executable
    params.enzyme = fragpipe_params.loc["msfragger.search_enzyme_name_1"]
    params.allowed_miscleavages = fragpipe_params.loc["msfragger.allowed_missed_cleavage_1"]
    params.fixed_mods = fragpipe_params.loc["msfragger.table.fix-mods"]
    params.variable_mods = fragpipe_params.loc["msfragger.table.var-mods"]
    params.max_mods = fragpipe_params.loc["msfragger.max_variable_mods_per_peptide"]
    params.min_peptide_length = fragpipe_params.loc["msfragger.digest_min_length"]
    params.max_peptide_length = fragpipe_params.loc["msfragger.digest_max_length"]

    precursor_mass_units = "Da"
    if int(fragpipe_params.loc["msfragger.precursor_mass_units"]):
        precursor_mass_units = "ppm"
    params.precursor_mass_tolerance = (
        f'{fragpipe_params.loc["msfragger.precursor_true_tolerance"]} {precursor_mass_units}'
    )

    fragment_mass_units = "Da"
    if int(fragpipe_params.loc["msfragger.fragment_mass_units"]):
        fragment_mass_units = "ppm"
    params.fragment_mass_tolerance = f'{fragpipe_params.loc["msfragger.fragment_mass_tolerance"]} {fragment_mass_units}'
    # ! ionquant is not necessarily fixed?
    params.ident_fdr_protein = fragpipe_params.loc["ionquant.proteinfdr"]
    params.ident_fdr_peptide = fragpipe_params.loc["ionquant.peptidefdr"]
    params.ident_fdr_psm = fragpipe_params.loc["ionquant.ionfdr"]

    for key in ["ident_fdr_protein", "ident_fdr_peptide", "ident_fdr_psm"]:
        value = getattr(params, key)
        try:
            value = int(value) / 100
            setattr(params, key, value)
        except ValueError:
            logging.warning(f"Could not convert {value} to int.")

    params.min_precursor_charge = int(fragpipe_params.loc["msfragger.misc.fragger.precursor-charge-lo"])
    params.max_precursor_charge = int(fragpipe_params.loc["msfragger.misc.fragger.precursor-charge-hi"])
    params.enable_match_between_runs = bool(fragpipe_params.loc["ionquant.mbr"])
    return params


if __name__ == "__main__":
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
    series.to_csv(file.parent / "fragger_extracted_params.csv")
