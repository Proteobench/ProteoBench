"""Tests that generated datapoint IDs stay unique when datapoints are created in a batch."""

import re

import pytest

from proteobench.datapoint.denovo_datapoint import DenovoDatapoint
from proteobench.datapoint.entrapment_datapoint import EntrapmentDatapoint
from proteobench.datapoint.quant_datapoint import QuantDatapointHYE

DATAPOINT_CLASSES = [QuantDatapointHYE, DenovoDatapoint, EntrapmentDatapoint]

# software name, then date_time_microseconds
ID_PATTERN = re.compile(r"^(?P<software>.+)_\d{8}_\d{6}_\d{6}$")


@pytest.mark.parametrize("datapoint_class", DATAPOINT_CLASSES)
def test_generated_id_starts_with_the_software_name(datapoint_class):
    datapoint = datapoint_class(software_name="TestTool")
    datapoint.generate_id()
    assert datapoint.id.startswith("TestTool_")


@pytest.mark.parametrize("datapoint_class", DATAPOINT_CLASSES)
def test_generated_id_carries_sub_second_resolution(datapoint_class):
    datapoint = datapoint_class(software_name="TestTool")
    datapoint.generate_id()
    match = ID_PATTERN.match(datapoint.id)
    assert match is not None, f"unexpected ID format: {datapoint.id}"
    assert match.group("software") == "TestTool"


@pytest.mark.parametrize("datapoint_class", DATAPOINT_CLASSES)
def test_ids_generated_in_a_tight_loop_are_unique(datapoint_class):
    """A batch (e.g. the resubmission script) must not hand several runs the same ID."""
    ids = []
    for _ in range(50):
        datapoint = datapoint_class(software_name="TestTool")
        datapoint.generate_id()
        ids.append(datapoint.id)
    assert len(set(ids)) == len(ids)


def test_ids_stay_distinct_across_datapoint_types():
    ids = []
    for datapoint_class in DATAPOINT_CLASSES:
        datapoint = datapoint_class(software_name="TestTool")
        datapoint.generate_id()
        ids.append(datapoint.id)
    assert len(set(ids)) == len(ids)
