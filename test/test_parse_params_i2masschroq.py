import io
from pathlib import Path

import pandas as pd

import proteobench.io.params.i2masschroq as params_module

TESTDATA_DIR = Path(__file__).parent / "params"


def test_extract_params():
    file = TESTDATA_DIR / "i2mproteobench_2pep_fdr01psm_fdr01prot.tsv"
    expected = pd.read_csv(TESTDATA_DIR / f"{file.stem}_sel.csv", index_col=0).squeeze("columns")
    actual = params_module.extract_params(file)
    actual = pd.Series(actual.__dict__)
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=0).squeeze("columns")
    assert expected.equals(actual)


if __name__ == "__main__":
    test_extract_params()
