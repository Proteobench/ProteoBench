import io
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.i2masschroq as params_module

TESTDATA_DIR = Path(__file__).parent / "params"

parameter_files = [
    "i2mproteobench_2pep_fdr01psm_fdr01prot_xtandem.tsv",
    "i2mq_result_parameters.tsv",
    "i2mproteobench_params_sage.tsv",
]

parameter_files = [TESTDATA_DIR / params_file for params_file in parameter_files]


@pytest.mark.parametrize("file", parameter_files)
def test_extract_params(file: str):
    expected = pd.read_csv(TESTDATA_DIR / f"{file.stem}_sel.csv", index_col=0).squeeze("columns")
    actual = params_module.extract_params(file)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    expected = expected.loc[actual.index]
    assert expected.equals(actual)


if __name__ == "__main__":
    test_extract_params()
