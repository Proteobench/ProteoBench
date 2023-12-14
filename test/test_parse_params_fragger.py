from pathlib import Path

import pandas as pd

import proteobench.io.params.fragger as fragger_params

TESTDATA_DIR = Path(__file__).parent / "params"


def test_read_file():
    file = TESTDATA_DIR / "fragger.params"
    csv_expected = TESTDATA_DIR / "fragger.csv"
    expected = pd.read_csv(csv_expected)
    data = fragger_params.read_file(file)
    actual = pd.DataFrame.from_records(data, columns=(fragger_params.Parameter._fields)).set_index(
        fragger_params.Parameter._fields[0]
    )
    actual.equals(expected)
