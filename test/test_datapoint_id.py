"""Tests that generated datapoint IDs stay unique when datapoints are created in a batch.

The quant, de novo and entrapment datapoints all take their ID from ``generate_id``.
"""

import re

from proteobench.datapoint.quant_datapoint import generate_id

# software name, then date_time_microseconds
ID_PATTERN = re.compile(r"^(?P<software>.+)_\d{8}_\d{6}_\d{6}$")


def test_generated_id_is_software_name_plus_sub_second_timestamp():
    run_id = generate_id("TestTool")
    match = ID_PATTERN.match(run_id)
    assert match is not None, f"unexpected ID format: {run_id}"
    assert match.group("software") == "TestTool"


def test_ids_generated_in_a_tight_loop_are_unique():
    """A batch (e.g. the resubmission script) must not hand several runs the same ID."""
    ids = [generate_id("TestTool") for _ in range(50)]
    assert len(set(ids)) == len(ids)
