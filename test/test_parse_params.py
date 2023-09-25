import json
from pathlib import Path

import pytest

import proteobench.io.params.maxquant as mq_params

TESTDATA_DIR = Path(__file__).parent / "params"

mq_paras = [
    "mqpar_MQ1.6.3.3_MBR.xml",
    "mqpar_MQ2.1.3.0_noMBR.xml",
    "mqpar1.5.3.30_MBR.xml",
]

mq_paras = [TESTDATA_DIR / mq_para for mq_para in mq_paras]


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


parameters = [(fname, Path(fname).with_suffix(".json")) for fname in mq_paras]


@pytest.mark.parametrize("file,json_expected", parameters)
def test_file_reading(file, json_expected):
    dict_expected = json.loads(json_expected.read_text())
    dict_actual = mq_params.read_file(file)
    assert dict_actual == dict_expected
