"""Functionality to parse Maxqunt mqpar.xml parameter files"""
from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger()


def extend_tuple(t, target_length: int):
    """Extend tuple with None values to match target length."""
    if not isinstance(t, tuple):
        raise TypeError(f"Wrong type provided. Expected tuple, got {type(t)} : {t!r}")
    if len(t) > target_length:
        raise ValueError(
            f"Tuple is too long (got {len(t)}, expected {target_length}: {t!r}"
        )
    return t + (None,) * (target_length - len(t))


def extend_tuples_with_none(list_of_tuples: list[tuple], target_length: int):
    """Extend the tuples in a list of tuples with None values to match target length."""
    extended_tuples = []
    for tuple_ in list_of_tuples:
        # if len(tuple_) > target_length:
        #     raise ValueError(f"tuple is too long: {len(tuple_)}")
        extended_tuple = extend_tuple(tuple_, target_length)
        extended_tuples.append(extended_tuple)
    return extended_tuples


def add_record(data: dict, tag: str, record) -> dict:
    """Add tag and record to data dict.

    The record can be many things."""
    if tag in data:
        if isinstance(data[tag], list):
            data[tag].append(record)
        else:
            data[tag] = [data[tag], record]
    else:
        data[tag] = record
    return data


def read_xml_record(element: ET.Element) -> dict:
    """Read entire record in a nested dict structure."""
    data = dict()
    for child in element:
        if len(child) > 1 and child.tag:
            # if there is a list, process each element one by one
            # either nested or a plain text
            data[child.tag] = [
                add_record(
                    dict(),
                    tag=child.tag,
                    record=read_xml_record(child)
                    if not (child.text and child.text.strip())
                    else child.text.strip(),
                )
                for child in child
            ]
        elif child.text and child.text.strip():
            # just plain text record
            data = add_record(data=data, tag=child.tag, record=child.text.strip())
        else:
            record = read_xml_record(child)
            data = add_record(data, child.tag, record)
    if not data:
        # empty strings and None are normalzied to None
        return None
    return data


def read_file(file: str) -> dict:
    """Read all entries in a MaxQuant xml file."""
    tree: ET.ElementTree = ET.parse(file)
    root: ET.Element = tree.getroot()
    params: dict = read_xml_record(root)
    return params


# create a first version of json files to match
if __name__ == "__main__":
    for test_file in [
        "../../../test/params/mqpar_MQ1.6.3.3_MBR.xml",
        "../../../test/params/mqpar_MQ2.1.3.0_noMBR.xml",
        "../../../test/params/mqpar1.5.3.30_MBR.xml",
    ]:
        print(f"{test_file = }")
        record_example = read_file(test_file)
        (
            Path(test_file)
            .with_suffix(".json")
            .write_text(
                json.dumps(
                    record_example,
                    indent=4,
                )
            )
        )
