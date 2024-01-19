import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.fragger as fragger_params

TESTDATA_DIR = Path(__file__).parent / "params"

# ! currently fragpipe with msfragger has two parameter/configuration files per run
fnames = ["fragger.params", "fragpipe.workflow"]
fnames = [TESTDATA_DIR / fname for fname in fnames]

fnames = [(fname, fname.with_suffix(".json")) for fname in fnames]


@pytest.mark.parametrize("file,csv_expected", fnames)
def test_read_file(file, csv_expected):
    file = TESTDATA_DIR / "fragger.params"
    csv_expected = TESTDATA_DIR / "fragger.csv"
    expected = pd.read_csv(csv_expected)
    data = fragger_params.read_file(file)
    actual = pd.DataFrame.from_records(data, columns=(fragger_params.Parameter._fields)).set_index(
        fragger_params.Parameter._fields[0]
    )
    actual.equals(expected)


def test_extract_params():
    file = TESTDATA_DIR / "fragger.params"
    f_fragpipe_workflow = TESTDATA_DIR / "fragpipe.workflow"
    expected = pd.read_csv(TESTDATA_DIR / "fragger_extracted_params.csv", index_col=0).squeeze("columns")
    actual = fragger_params.extract_params(file, f_fragpipe_workflow)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    assert expected.equals(actual)
