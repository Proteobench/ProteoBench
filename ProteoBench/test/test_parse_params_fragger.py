import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.fragger as fragger_params

TESTDATA_DIR = Path(__file__).parent / "params"


parameter_files = [
    "fragpipe.workflow",
    "fragpipe_win_paths.workflow",
    "fragpipe_v22.workflow",
]

parameter_files = [TESTDATA_DIR / params_file for params_file in parameter_files]

parameters = [(fname, (fname.with_suffix(".csv"))) for fname in parameter_files]


@pytest.mark.parametrize("file,csv_expected", parameters)
def test_read_fragpipe_workflow(file, csv_expected):
    expected = pd.read_csv(csv_expected, index_col=0)
    with open(file, "rb") as f:
        _, _, _, data = fragger_params.read_fragpipe_workflow(f)
    actual = pd.DataFrame.from_records(data, columns=(fragger_params.Parameter._fields)).set_index(
        fragger_params.Parameter._fields[0]
    )
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert actual.equals(expected)


parameters = [(fname, (fname.parent / (fname.stem + "_extracted_params.csv"))) for fname in parameter_files]


@pytest.mark.parametrize("file,csv_expected", parameters)
def test_extract_params(file, csv_expected):
    expected = pd.read_csv(csv_expected, index_col=0).squeeze("columns")
    with open(file, "rb") as f:
        actual = fragger_params.extract_params(f)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)
