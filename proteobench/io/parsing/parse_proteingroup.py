"""
Module for parsing protein groups data from various formats.
"""

import math
import os
import re
import warnings

import pandas as pd


def load_input_file(input_csv: str, input_format: str = None, input_csv_secondary: str = None) -> pd.DataFrame:
    """
    Load a dataframe from a CSV file depending on its format.

    Parameters
    ----------
    input_csv : str
        The path to the CSV file.
    input_format : str
        The format of the input file (e.g., "DIA-NN", etc.).
    input_csv_secondary : str, optional
        The path to a secondary CSV file (currently unused for protein group parsing).

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    try:  # TODO: is this necessary? I have to try out MQ input.
        if input_format == "MaxQuant":
            warnings.warn(
                """
                WARNING: MaxQuant proforma parsing does not take into account fixed modifications\n
                because they are implicit. Only after providing the appropriate parameter file,\n
                fixed modifications will be added correctly.
                """
            )
        load_function = _LOAD_FUNCTIONS[input_format]
    except KeyError as e:
        raise ValueError(f"Invalid input format: {input_format}") from e

    return load_function(input_csv)


# def _load_custom(input_csv: str) -> pd.DataFrame:
#     """
#     Load a custom output file.

#     Parameters
#     ----------
#     input_csv : str
#         The path to the custom output file.

#     Returns
#     -------
#     pd.DataFrame
#         The loaded dataframe.
#     """
#     input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
#     return input_data_frame


def _load_alphadia(input_csv: str) -> pd.DataFrame:
    """
    Load an AlphaDIA output file.

    Parameters
    ----------
    input_csv : str
        The path to the AlphaDIA output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    if isinstance(input_csv, str):
        filename = input_csv
    else:  # streamlit OpenedFile object
        filename = input_csv.name
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    input_data_frame["pg"] = input_data_frame["pg"].str.split(";")
    input_data_frame["pg"] = input_data_frame["pg"].map(
        lambda x: [mapper[protein] if protein in mapper.keys() else protein for protein in x]
    )
    input_data_frame["pg"] = input_data_frame["pg"].str.join(";")
    return input_data_frame


def _load_diann(input_csv: str) -> pd.DataFrame:
    """
    Load a DIA-NN output file.

    Parameters
    ----------
    input_csv : str
        The path to the DIA-NN output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    if isinstance(input_csv, str):
        filename = input_csv
    else:  # streamlit OpenedFile object
        filename = input_csv.name
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    input_data_frame["Protein.Group"] = input_data_frame["Protein.Group"].str.split(";")
    input_data_frame["Protein.Group"] = input_data_frame["Protein.Group"].map(
        lambda x: [mapper[protein] if protein in mapper.keys() else protein for protein in x]
    )
    input_data_frame["Protein.Group"] = input_data_frame["Protein.Group"].str.join(";")
    return input_data_frame


def _load_spectronaut(input_csv: str) -> pd.DataFrame:
    """
    Load a Spectronaut output file.

    Parameters
    ----------
    input_csv : str
        The path to the Spectronaut output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")

    if input_data_frame["PG.Quantity"].dtype == object:
        try:
            input_csv.seek(0)
        except AttributeError:
            # if input_csv is a PathPosix object, it does not have a seek method
            # This can occur when the io util functions are used.
            # Should probably be fixed some way in the future
            pass
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t", decimal=",")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].str.split(";")
    input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].map(
        lambda x: [mapper[protein] if protein in mapper.keys() else protein for protein in x]
    )
    input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].str.join(";")
    return input_data_frame


_LOAD_FUNCTIONS = {
    # "MaxQuant": _load_maxquant,
    # "AlphaPept": _load_alphapept,
    # "Sage": _load_sage,
    # "FragPipe": _load_fragpipe,
    # "WOMBAT": _load_wombat,
    # "ProlineStudio": _load_prolinestudio_msangel,
    # "MSAngel": _load_prolinestudio_msangel,
    # "i2MassChroQ": _load_i2masschroq,
    # "Custom": _load_custom,
    "DIA-NN": _load_diann,
    "AlphaDIA": _load_alphadia,
    # "FragPipe (DIA-NN quant)": _load_fragpipe_diann_quant,
    "Spectronaut": _load_spectronaut,
    # "MSAID": _load_msaid,
    # "PEAKS": _load_peaks,
    # "quantms": _load_quantms,
    # "MetaMorpheus": _load_metamorpheus,
}
