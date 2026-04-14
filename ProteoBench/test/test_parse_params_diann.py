import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.diann as diann_params

TESTDATA_DIR = Path(__file__).parent / "params"

# "DIANN_output_20240229_report.log.txt",
fnames = [
    "DIANN_output_20240229_report.log.txt",
    "DIANN_WU304578_report.log.txt",
    "Version1_9_Predicted_Library_report.log.txt",
]

fnames = [TESTDATA_DIR / f for f in fnames]


@pytest.mark.parametrize("file", fnames)
def test_read_spectronaut_settings(file):
    expected = pd.read_csv(file.with_suffix(".csv"), index_col=0).squeeze("columns")
    actual = diann_params.extract_params(file)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)
