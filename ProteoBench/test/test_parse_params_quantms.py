import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.quantms as quantms_params

TESTDATA_DIR = Path(__file__).parent / "params"


parameter_files = [
    (
        "quantms_1-3_dev.json",
        "quantms_1-3.nf_core_quantms_software_mqc_versions.yml",
        None,
    ),
    (
        "quantms_1-3_test.json",
        None,
        "quantms_1-3_test-versions.yml",
    ),
]

parameter_files = [
    (
        TESTDATA_DIR / files[0] if files[0] is not None else None,
        TESTDATA_DIR / files[1] if files[1] is not None else None,
        TESTDATA_DIR / files[2] if files[2] is not None else None,
    )
    for files in parameter_files
]
parameters = [(fname, (fname[0].parent / (fname[0].stem + "_extracted_params.csv"))) for fname in parameter_files]


@pytest.mark.parametrize("inputs,csv_expected", parameters)
def test_extract_params(inputs, csv_expected):
    expected = pd.read_csv(csv_expected, index_col=0).squeeze("columns")
    input_files = [open(file, "rb") for file in inputs if file is not None]
    actual = quantms_params.extract_params(*input_files)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)
