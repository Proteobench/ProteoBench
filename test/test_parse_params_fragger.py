import io
from pathlib import Path

import pandas as pd

import proteobench.io.params.fragger as fragger_params

TESTDATA_DIR = Path(__file__).parent / "params"


def test_read_msfragger_params():
    file = TESTDATA_DIR / "fragger.params"
    csv_expected = TESTDATA_DIR / "fragger.csv"
    expected = pd.read_csv(csv_expected, index_col=0)
    with open(file, "rb") as f:
        data = fragger_params.read_msfragger_params(f)
    actual = pd.DataFrame.from_records(data, columns=(fragger_params.Parameter._fields)).set_index(
        fragger_params.Parameter._fields[0]
    )
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    assert actual.equals(expected)


def test_read_fragpipe_workflow():
    file = TESTDATA_DIR / "fragpipe.workflow"
    csv_expected = TESTDATA_DIR / "fragpipe.csv"
    expected = pd.read_csv(csv_expected, index_col=0)
    with open(file, "rb") as f:
        _, data = fragger_params.read_fragpipe_workflow(f)
    actual = pd.DataFrame.from_records(data, columns=(fragger_params.Parameter._fields)).set_index(
        fragger_params.Parameter._fields[0]
    )
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    assert actual.equals(expected)


def test_extract_params():
    file = TESTDATA_DIR / "fragger.params"
    f_fragpipe_workflow = TESTDATA_DIR / "fragpipe.workflow"
    expected = pd.read_csv(TESTDATA_DIR / "fragger_extracted_params.csv", index_col=0).squeeze("columns")
    with open(file, "rb") as f1, open(f_fragpipe_workflow, "rb") as f2:
        actual = fragger_params.extract_params(f1, f2)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    assert expected.equals(actual)
