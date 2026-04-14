import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.spectronaut as spectronaut_params

TESTDATA_DIR = Path(__file__).parent / "params"


fnames = [
    "spectronaut_Experiment1_ExperimentSetupOverview_BGS_Factory_Settings.txt",
]

fnames = [TESTDATA_DIR / f for f in fnames]


@pytest.mark.parametrize("file", fnames)
def test_read_spectronaut_settings(file):
    expected = pd.read_csv(file.with_suffix(".csv"), index_col=0).squeeze("columns")
    actual = spectronaut_params.read_spectronaut_settings(file)
    print(actual.software_name)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)
