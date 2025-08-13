import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.metamorpheus as metamorpheus_params

TESTDATA_DIR = Path(__file__).parent / "params"

fnames = [
    [
        TESTDATA_DIR / "metamorpheus_search_task_config.toml",
        TESTDATA_DIR / "metamorpheus_version_result.txt",
    ],
    # Reverse order
    [
        TESTDATA_DIR / "metamorpheus_version_result.txt",
        TESTDATA_DIR / "metamorpheus_search_task_config.toml",
    ],
]


@pytest.mark.parametrize("file1, file2", fnames)
def test_extract_params(file1, file2):
    print(f"Testing with files: {file1}, {file2}")
    params = metamorpheus_params.extract_params(file1, file2)
    expected = pd.read_csv(TESTDATA_DIR / "metamorpheus_parameters.csv", index_col=0).squeeze("columns")
    actual = pd.Series(params.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)
