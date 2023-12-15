"""Functionality to parse MSFragger fragger.params parameter files.

MSFragger has a text based paramter file format which 
separates paramters and their value using an equal sign. Optional comments are 
expressed with a hash sign.
"""
from __future__ import annotations

import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

Parameter = namedtuple("Parameter", ["name", "value", "comment"])


def read_file(file: str) -> list[Parameter]:
    """Read MSFragger parameter file as list of records."""
    with open(file) as f:
        data = []
        for line in f:
            line = line.strip()
            logger.debug(line)
            # ! logic below also allows to keep the comments as comments
            if line.startswith("#"):
                continue
            if not line:
                continue
            if "#" in line:
                res = line.split("#")
                if len(res) == 1:
                    comment = res[0]
                    data.append(Parameter(None, None, comment.strip()))
                    continue
                param, comment = [x.strip() for x in res]
            else:
                param = line
                comment = None
            res = param.strip().split(" = ")
            if len(res) == 1:
                param = res[0].strip()
                data.append(Parameter(param, None, comment))
                continue
            param, value = [x.strip() for x in res]
            data.append(Parameter(param, value, comment))
    return data


if __name__ == "__main__":
    import pathlib

    import pandas as pd

    file = pathlib.Path("../../../test/params/fragger.params")
    data = read_file(file)
    df = pd.DataFrame.from_records(data, columns=Parameter._fields).set_index(Parameter._fields[0])
    df
    df.to_csv(file.with_suffix(".csv"))
