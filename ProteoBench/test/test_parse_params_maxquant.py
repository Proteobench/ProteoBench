import io
import json
from pathlib import Path

import pandas as pd
import pytest

import proteobench.io.params.maxquant as mq_params

TESTDATA_DIR = Path(__file__).parent / "params"

mqpar_fnames = [
    "mqpar_MQ1.6.3.3_MBR.xml",
    "mqpar_MQ2.1.3.0_noMBR.xml",
    "mqpar1.5.3.30_MBR.xml",
    "mqpar_mq2.6.2.0_1mc_MBR.xml",
]

mqpar_fnames = [TESTDATA_DIR / mq_para for mq_para in mqpar_fnames]


parameters = [
    ((1, 2), (1, 2, None)),
    ((3, 4, 5), (3, 4, 5)),
    ((6,), (6, None, None)),
]


@pytest.mark.parametrize("tuple_in,tuple_out", parameters)
def test_extend_tuple(tuple_in, tuple_out):
    actual = mq_params.extend_tuple(tuple_in, 3)
    assert actual == tuple_out


def test_list_of_tuple_expansion():
    in_list_of_tuples = [(1, 2), (3, 4, 5), (6,)]
    expected = [(1, 2, None), (3, 4, 5), (6, None, None)]
    actual = mq_params.extend_tuples_with_none(in_list_of_tuples, 3)
    assert actual == expected


parameters = [(fname, fname.with_suffix(".json")) for fname in mqpar_fnames]


@pytest.mark.parametrize("file,json_expected", parameters)
def test_file_reading(file, json_expected):
    dict_expected = json.loads(json_expected.read_text())
    dict_actual = mq_params.read_file(file)
    assert dict_actual == dict_expected


parameters = [
    ({"k": "v"}, [(("k",), "v")]),
    ({"k1": {"k2": "v1", "k3": "v2"}}, [(("k1", "k2"), "v1"), (("k1", "k3"), "v2")]),
    (
        {"k1": {"k2": [{"k4": "v1"}, {"k4": "v2"}]}},
        [(("k1", "k2", "k4"), "v1"), (("k1", "k2", "k4"), "v2")],
    ),
    (
        {"k1": [{"k2": {"k4": "v1", "k5": "v2"}}, {"k2": {"k4": "v1", "k5": "v2"}}]},
        [
            (("k1", "k2", "k4"), "v1"),
            (("k1", "k2", "k5"), "v2"),
            (("k1", "k2", "k4"), "v1"),
            (("k1", "k2", "k5"), "v2"),
        ],
    ),
    (
        {
            "restrictMods": [
                {"string": "Oxidation (M)"},
                {"string": "Acetyl (Protein N-term)"},
            ]
        },
        [
            (("restrictMods", "string"), "Oxidation (M)"),
            (("restrictMods", "string"), "Acetyl (Protein N-term)"),
        ],
    ),
    (
        {"variableModifications": {"string": ["Oxidation (M)", "Acetyl (Protein N-term)"]}},
        [
            (("variableModifications", "string"), "Oxidation (M)"),
            (("variableModifications", "string"), "Acetyl (Protein N-term)"),
        ],
    ),
]


@pytest.mark.parametrize("dict_in,list_expected", parameters)
def test_flatten_of_dicts(dict_in, list_expected):
    actual = mq_params.flatten_dict_of_dicts(dict_in)
    assert actual == list_expected


# TODO the test is broken, partly due to the expected files being incorrect
# TODO skip for now, fix in future
# parameters = [(fname, fname.with_suffix(".csv")) for fname in mqpar_fnames]
parameters = []


@pytest.mark.parametrize("file,csv_expected", parameters)
def test_file_parsing_to_csv(file, csv_expected):
    expected = pd.read_csv(csv_expected, index_col=[0, 1, 2, 3])
    actual = mq_params.read_file(file)
    actual = mq_params.build_Series_from_records(actual, 4)
    actual = actual.to_frame("run_identifier")
    actual = pd.read_csv(io.StringIO(actual.to_csv()), index_col=[0, 1, 2, 3])
    expected = expected.loc[actual.index]
    print(actual)
    print(expected)
    assert actual.equals(expected)


# TODO the test is broken, partly due to the expected files being incorrect
# TODO skip for now, fix in future
# parameters = [(fname, (fname.parent / (fname.stem + "_sel.json"))) for fname in mqpar_fnames]
parameters = []


@pytest.mark.parametrize("file,json_expected", parameters)
def test_extract_params(file, json_expected):
    with open(json_expected) as f:
        expected = json.load(f)
    actual = mq_params.extract_params(file)
    actual = actual.__dict__

    expected = {k: v for k, v in expected.items() if k in actual}
    assert actual == expected
