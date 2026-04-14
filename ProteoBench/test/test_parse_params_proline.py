import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.proline as proline_params

TESTDATA_DIR = Path(__file__).parent / "params"

fnames = [
    "Proline_example_w_Mascot_wo_proteinSets.xlsx",
    "Proline_example_2.xlsx",
    "ProlineStudio_withMBR.xlsx",
    "ProlineStudio_241024.xlsx",
]
fnames = [TESTDATA_DIR / f for f in fnames]

parameters = [
    (
        "PSM FILTER: PEP_SEQ_LENGTH; Description: peptide sequence length filter; Properties: [threshold_value=7]",
        7,
    ),
    (
        "PSM FILTER: PEP_SEQ_LENGTH; Description: peptide sequence length filter; Properties: [threshold_value=12]",
        12,
    ),
]


@pytest.mark.parametrize("string,expected_min_pep", parameters)
def test_find_pep_length(string, expected_min_pep):
    actual_min_pep = proline_params.find_min_pep_length(string)
    assert actual_min_pep == expected_min_pep


@pytest.mark.parametrize("file", fnames)
def test_extract_params(file, tmpdir):
    expected = pd.read_csv(file.with_suffix(".csv"), index_col=0).squeeze("columns")
    actual = proline_params.extract_params(file)
    actual = pd.Series(actual.__dict__)

    temp_file = tmpdir.join("test_proline.csv")
    actual.to_csv(temp_file)

    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")

    expected = expected.loc[actual.index]

    assert expected.equals(actual)


def test_find_charges():
    assert proline_params.find_charge("2+ and 3+") == [2, 3]
    assert proline_params.find_charge("2+") == [2]
    assert proline_params.find_charge("3+") == [3]
    assert proline_params.find_charge("30+ and 14+") == [30, 14]
