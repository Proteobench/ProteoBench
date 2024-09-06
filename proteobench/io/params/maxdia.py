import re
from proteobench.io.params import ProteoBenchParameters
from maxquant import extract_params as extract_params_mq, read_file, build_Series_from_records
import pathlib
import pandas as pd


def extract_params(fname: str) -> ProteoBenchParameters:
    """Relying on maxquant parser for maxDIA parameter parsing."""

    parameters = extract_params_mq(fname)
    series = build_Series_from_records(read_file(fname)).reset_index()

    parameters.min_peptide_length = series.loc[series["level_0"] == "minPeptideLength", 0].values[0]
    parameters.max_peptide_length = series.loc[series["level_0"] == "maxPeptideLengthForUnspecificSearch", 0].values[0]
    parameters.search_engine_version = parameters.__dict__["software_version"]
    return parameters


if __name__ == "__main__":
    for fname in ["../../../test/params/mqpar_maxdia.xml"]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".csv"))
