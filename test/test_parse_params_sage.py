import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.sage as sage_params

TESTDATA_DIR = Path(__file__).parent / "params"

fnames = [
    "sage_results.json",
    "sage_parameterfile.json",
]

fnames = [TESTDATA_DIR / f for f in fnames]


@pytest.mark.parametrize("file", fnames)
def test_read_sage_settings(file):
    expected = pd.read_csv(file.with_suffix(".csv"), index_col=0).squeeze("columns")
    actual = sage_params.extract_params(file)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]

    print(pd.concat([expected, actual], axis=1))

    assert expected.equals(actual)
