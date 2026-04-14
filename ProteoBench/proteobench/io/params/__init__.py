"""
This module provides the `ProteoBenchParameters` dataclass for handling parameters
related to ProteoBench. The parsing is done per data analysis software.

Classes
ProteoBenchParameters
    A dataclass for handling ProteoBench parameters.
"""

# Reference for parameter names
# https://github.com/bigbio/proteomics-sample-metadata/blob/master/sdrf-proteomics/assets/param2sdrf.yml
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class ProteoBenchParameters:
    """
    ProteoBench parameter dataclass.

    Parameters
    ----------
    filename : os.path
        Path to parameter file.
    **kwargs : dict[str, Any]
        Other keyword arguments.
    """

    def __init__(self, filename=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DDA_ion.json"), **kwargs):
        """
        Read the JSON file and initializes only the attributes present in the file.

        Parameters
        ----------
        filename : os.path
            Path to parameter file.
        **kwargs : dict[str, Any]
            Other keyword arguments.
        """
        if not os.path.isfile(filename):
            print(f"Error: File '{filename}' not found.")
            return  # No initialization happens if the file is missing

        with open(filename, "r", encoding="utf-8") as file:
            json_dict = json.load(file)

        # Initialize only the fields present in the JSON
        for key, value in json_dict.items():
            if "value" in value:
                setattr(self, key, value["value"])
            elif "placeholder" in value:
                setattr(self, key, value["placeholder"])
            else:
                setattr(self, key, None)

        for key, value in kwargs.items():
            print(key, value)
            if hasattr(self, key) and value == "None":
                setattr(self, key, np.nan)
            elif hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Custom string representation to only show initialized attributes.

        Returns
        -------
        str
            String representation to only show initialized attributes.
        """
        return str({key: value for key, value in self.__dict__.items() if value is not None})

    def fill_none(self):
        """
        Fill all None values with np.nan.
        """
        for key, value in self.__dict__.items():
            if value == "None":
                setattr(self, key, np.nan)


# Automatically initialize from fields.json if run directly
if __name__ == "__main__":
    proteo_params = ProteoBenchParameters()
    print(proteo_params)
