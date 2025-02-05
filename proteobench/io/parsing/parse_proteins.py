from pathlib import Path

import pandas as pd


def load_input_file(input_csv: str, input_format: str) -> pd.DataFrame:
    """
    Loads a dataframe from a CSV file depending on its format.

    Args:
        input_csv (str): The path to the CSV file.
        input_format (str): The format of the input file (e.g., "MaxQuant", "AlphaPept", etc.).

    Returns:
        pd.DataFrame: The loaded dataframe.
    """

    if input_format == "DIA-NN":
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")

        # Remove the whole filepath in *.pg_matrix and the extension of the filenames
        rename_map = {c: Path(c.replace("/", "\\").split("\\")[-1]).stem for c in input_data_frame.columns[4:]}
        input_data_frame = input_data_frame.rename(columns=rename_map)

    return input_data_frame