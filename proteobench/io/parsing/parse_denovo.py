"""
Module for parsing results data from various de novo sequencing engines.
"""

import pandas as pd

def load_input_file(input_path: str, input_format: str) -> pd.DataFrame:
    try:
        load_function = _LOAD_FUNCTIONS[input_format]
    except KeyError as e:
        raise ValueError(f"Invalid input format: {input_format}") from e

    return load_function(input_path)


def _load_adanovo(input_path: str) -> pd.DataFrame:
    """
    Load an AdaNovo output file.

    Parameters
    ----------
    input_path: str
        The path to the AdaNovo output file.
    
    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    pass

def _load_casanovo(input_path: str) -> pd.DataFrame:
    """
    Load a Casanovo output file.

    Parameters
    ----------
    input_path: str
        The path to the Casanovo output file.
    
    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    pass

def _load_instanovo(input_path: str) -> pd.DataFrame:
    """
    Load an InstaNovo output file.

    Parameters
    ----------
    input_path: str
        The path to the InstaNovo output file.
    
    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    pass

def _load_pihelixnovo(input_path: str) -> pd.DataFrame:
    """
    Load a Pi-HelixNovo output file.

    Parameters
    ----------
    input_path: str
        The path to the Pi-HelixNovo output file.
    
    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    pass

def _load_piprimenovo(input_path: str) -> pd.DataFrame:
    """
    Load a Pi-PrimeNovo output file.

    Parameters
    ----------
    input_path: str
        The path to the Pi-PrimeNovo output file.
    
    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    pass

_LOAD_FUNCTIONS = {
    "AdaNovo": _load_adanovo,
    "Casanovo": _load_casanovo,
    "InstaNovo": _load_instanovo,
    "Pi-HelixNovo": _load_pihelixnovo,
    "Pi-PrimeNovo": _load_piprimenovo
}