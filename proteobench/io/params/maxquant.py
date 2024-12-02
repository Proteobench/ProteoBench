"""Functionality to parse Maxquant mqpar.xml parameter files"""

from __future__ import annotations

import collections
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from proteobench.io.params import ProteoBenchParameters

logger = logging.getLogger()


def extend_tuple(t: tuple, target_length: int) -> tuple:
    """
    Extend a tuple with `None` values to match the target length.

    Args:
        t (tuple): The original tuple.
        target_length (int): The target length for the extended tuple.

    Returns:
        tuple: The extended tuple with `None` values added.

    Raises:
        TypeError: If the input is not a tuple.
        ValueError: If the tuple is longer than the target length.
    """
    if not isinstance(t, tuple):
        raise TypeError(f"Wrong type provided. Expected tuple, got {type(t)} : {t!r}")
    if len(t) > target_length:
        raise ValueError(f"Tuple is too long (got {len(t)}, expected {target_length}: {t!r}")
    return t + (None,) * (target_length - len(t))


def extend_tuples_with_none(list_of_tuples: List[tuple], target_length: int) -> List[tuple]:
    """
    Extend the tuples in a list of tuples with `None` values to match the target length.

    Args:
        list_of_tuples (List[tuple]): List of tuples to extend.
        target_length (int): The target length for each tuple.

    Returns:
        List[tuple]: List of extended tuples.
    """
    extended_tuples = []
    for tuple_ in list_of_tuples:
        extended_tuple = extend_tuple(tuple_, target_length)
        extended_tuples.append(extended_tuple)
    return extended_tuples


def add_record(data: dict, tag: str, record: Any) -> dict:
    """
    Add a record to a dictionary under a given tag.

    Args:
        data (dict): The data dictionary to update.
        tag (str): The tag under which the record should be added.
        record (Any): The record to add.

    Returns:
        dict: The updated dictionary.
    """
    if tag in data:
        if isinstance(data[tag], list):
            data[tag].append(record)
        else:
            data[tag] = [data[tag], record]
    else:
        data[tag] = record
    return data


def read_xml_record(element: ET.Element) -> dict:
    """
    Recursively read an XML element into a nested dictionary structure.

    Args:
        element (ET.Element): The XML element to read.

    Returns:
        dict: A dictionary representing the element and its children.
    """
    data = dict()
    if element.attrib:
        data.update(element.attrib)
    for child in element:
        if len(child) > 1 and child.tag:
            data[child.tag] = [
                add_record(
                    dict(),
                    tag=child.tag,
                    record=read_xml_record(child) if not (child.text and child.text.strip()) else child.text.strip(),
                )
                for child in child
            ]
        elif child.text and child.text.strip():
            data = add_record(data=data, tag=child.tag, record=child.text.strip())
        else:
            record = read_xml_record(child)
            data = add_record(data, child.tag, record)
    if not data:
        return None
    return data


def read_file(file: str) -> dict:
    """
    Read all entries in a MaxQuant XML file.

    Args:
        file (str): The file path of the XML file.

    Returns:
        dict: A dictionary representing the parsed XML content.
    """
    tree: ET.ElementTree = ET.parse(file)
    root: ET.Element = tree.getroot()
    params: dict = read_xml_record(root)
    return params


def flatten_dict_of_dicts(d: dict, parent_key: str = "") -> dict:
    """
    Flatten a nested dictionary to a single-level dictionary with tuple keys.

    Args:
        d (dict): The nested dictionary to flatten.
        parent_key (str, optional): The outer key used for recursion, defaults to an empty string.

    Returns:
        dict: A flattened dictionary with tuple keys.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + (k,) if parent_key else (k,)
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten_dict_of_dicts(v, parent_key=new_key))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, collections.abc.MutableMapping):
                    items.extend(flatten_dict_of_dicts(item, parent_key=new_key))
                elif isinstance(item, str):
                    items.append((new_key, item))
                else:
                    raise ValueError(f"Unknown item: {item:r}")
        else:
            items.append((new_key, v))
    return items


def build_Series_from_records(records: Any, index_length: int = 4) -> pd.Series:
    """
    Convert records into a pandas Series, using a MultiIndex.

    Args:
        records (Any): The records to convert.
        index_length (int, optional): The length of the index. Defaults to 4.

    Returns:
        pd.Series: A pandas Series with the flattened records and a MultiIndex.
    """
    records = flatten_dict_of_dicts(records)
    idx = pd.MultiIndex.from_tuples((extend_tuple(k, index_length) for (k, _) in records))
    return pd.Series((v for (k, v) in records), index=idx)


def extract_params(fname: str, ms2frac: str = "FTMS") -> ProteoBenchParameters:
    """
    Parse MaxQuant mqpar.xml file and extract relevant parameters.

    Args:
        fname (str): The file path to the MaxQuant parameter file.
        ms2frac (str, optional): The MS2 fragmentation method to select. Defaults to "FTMS".

    Returns:
        ProteoBenchParameters: The extracted parameters as a `ProteoBenchParameters` object.
    """
    params = ProteoBenchParameters()

    record = read_file(fname)

    # Select MS2 fragmentation method specified by parameter
    record["msmsParamsArray"] = [d for d in record["msmsParamsArray"] if d["msmsParams"]["Name"] == ms2frac]
    record = build_Series_from_records(record, 4).sort_index()

    # Extract parameters from the XML record
    params.search_engine = "Andromeda"
    params.software_version = record.loc["maxQuantVersion"].squeeze()
    params.ident_fdr_psm = None
    params.ident_fdr_peptide = record.loc["peptideFdr"].squeeze()
    params.ident_fdr_protein = record.loc["proteinFdr"].squeeze()
    params.enable_match_between_runs = record.loc["matchBetweenRuns"].squeeze()

    precursor_mass_tolerance = record.loc[
        pd.IndexSlice["parameterGroups", "parameterGroup", "mainSearchTol", :]
    ].squeeze()
    params.precursor_mass_tolerance = f"{precursor_mass_tolerance} ppm"

    fragment_mass_tolerance = record.loc[pd.IndexSlice["msmsParamsArray", "msmsParams", "MatchTolerance", :]].squeeze()
    in_ppm = bool(record.loc[pd.IndexSlice["msmsParamsArray", "msmsParams", "MatchToleranceInPpm", :]].squeeze())
    if in_ppm:
        fragment_mass_tolerance = f"{fragment_mass_tolerance} ppm"
    params.fragment_mass_tolerance = fragment_mass_tolerance

    # Extract enzyme and cleavage settings
    params.enzyme = record.loc[("parameterGroups", "parameterGroup", "enzymes", "string")].squeeze()
    params.allowed_miscleavages = record.loc[
        pd.IndexSlice["parameterGroups", "parameterGroup", "maxMissedCleavages", :]
    ].squeeze()

    # Extract peptide length information
    try:
        params.min_peptide_length = record.loc["minPepLen"].squeeze()
    except KeyError:
        params.minPeptideLength = record.loc["minPeptideLength"].squeeze()

    # Fixed and variable modifications
    fixed_mods = record.loc[pd.IndexSlice["parameterGroups", "parameterGroup", "fixedModifications", :]].squeeze()
    if isinstance(fixed_mods, str):
        params.fixed_mods = fixed_mods
    else:
        params.fixed_mods = ",".join(fixed_mods)

    variable_mods = record.loc[pd.IndexSlice["parameterGroups", "parameterGroup", "variableModifications", :]].squeeze()
    if isinstance(variable_mods, str):
        params.variable_mods = variable_mods
    else:
        params.variable_mods = ",".join(variable_mods)

    params.max_mods = record.loc[("parameterGroups", "parameterGroup", "maxNmods")].squeeze()
    params.min_precursor_charge = None
    params.max_precursor_charge = record.loc[
        pd.IndexSlice["parameterGroups", "parameterGroup", "maxCharge", :]
    ].squeeze()

    return params


# Create a first version of json files to match
if __name__ == "__main__":
    import json
    from pprint import pprint

    # Process different MaxQuant XML files
    for test_file in [
        "../../../test/params/mqpar_MQ1.6.3.3_MBR.xml",
        "../../../test/params/mqpar_MQ2.1.3.0_noMBR.xml",
        "../../../test/params/mqpar1.5.3.30_MBR.xml",
        "../../../test/params/mqpar_mq2.6.2.0_1mc_MBR.xml",
    ]:
        print(f"{test_file = }")
        record = read_file(test_file)

        # Save the XML record as a JSON file
        Path(test_file).with_suffix(".json").write_text(json.dumps(record, indent=4))

        # Create a pandas Series from the record and save it as a CSV file
        record = build_Series_from_records(record, 4)
        record = record.to_frame("run_identifier")
        record.to_csv(Path(test_file).with_suffix(".csv"))

        # Extract parameters and save them in JSON format
        params = extract_params(test_file, ms2frac="FTMS")
        pprint(params.__dict__)

        # Save extracted parameters as a JSON file
        test_file = Path(test_file)
        fname = Path(str(test_file.with_suffix(".json").with_name(test_file.stem + "_sel")) + ".json")
        with open(fname, "w") as f:
            json.dump(params.__dict__, f, indent=4)
