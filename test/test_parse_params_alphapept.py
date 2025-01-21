import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.alphapept as alpahpept_params

TESTDATA_DIR = Path(__file__).parent / "params"

fnames = [
    "alphapept_0.4.9_unnormalized.yaml",
    "alphapept_0.4.9.yaml",
]
fnames = [TESTDATA_DIR / f for f in fnames]


@pytest.mark.parametrize("file", fnames)
def test_extract_params(file):
    expected = pd.read_csv(file.with_suffix(".csv"), index_col=0).squeeze("columns")
    actual = alpahpept_params.extract_params(file)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)
