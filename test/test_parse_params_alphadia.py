import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.alphadia as alphadia_params

TESTDATA_DIR = Path(__file__).parent / "params"

fnames = [
    "log_alphadia_1.txt",
    "log_alphadia_2.txt",
    "log_alphadia_1.8.txt",
    "log_alphadia_1.10.txt",
]
fnames = [TESTDATA_DIR / f for f in fnames]


@pytest.mark.parametrize("file", fnames)
def test_extract_params(file):
    expected = pd.read_csv(file.with_suffix(".csv"), index_col=0).squeeze("columns")
    actual = alphadia_params.extract_params(file)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    assert expected.equals(actual)
