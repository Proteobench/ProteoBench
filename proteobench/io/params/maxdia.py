"""
MaxDIA parameter file parser for ProteoBench.
"""

import pathlib
import re
from typing import Any

import pandas as pd
from maxquant import build_Series_from_records
from maxquant import extract_params as extract_params_mq
from maxquant import read_file

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname: str) -> ProteoBenchParameters:
    """
    Parse MaxDIA parameters using MaxQuant's parser and extract additional parameters.

    Parameters
    ----------
    fname : str
        The file path to the MaxDIA parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a `ProteoBenchParameters` object.
    """
    # Use MaxQuant's extract_params to parse the base parameters
    parameters = extract_params_mq(fname)

    # Read the MaxDIA parameter file and build a pandas Series from the records
    series = build_Series_from_records(read_file(fname)).reset_index()

    # Extract and set peptide length parameters
    parameters.min_peptide_length = int(series.loc[series["level_0"] == "minPeptideLength", 0].values[0])
    parameters.max_peptide_length = int(
        series.loc[series["level_0"] == "maxPeptideLengthForUnspecificSearch", 0].values[0]
    )

    return parameters


if __name__ == "__main__":
    """
    Reads MaxDIA parameter files, extracts parameters, and writes them to CSV files.
    """
    for fname in ["../../../test/params/mqpar_maxdia.xml"]:
        file = pathlib.Path(fname)

        # Extract parameters using the defined function
        params = extract_params(file)

        # Convert the parameters to a dictionary and then to a pandas Series
        data_dict = params.__dict__
        series = pd.Series(data_dict)

        print(series)
        # Write the Series to a CSV file
        series.to_csv(file.with_suffix(".csv"))
