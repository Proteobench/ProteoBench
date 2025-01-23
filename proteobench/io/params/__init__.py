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
    Parameters for a proteomics search engine.

    Attributes
    ----------
    software_name : Optional[str]
        Name of the software tool / pipeline used for this benchmark run
        (examples: "MaxQuant", "AlphaPept", "Proline", ...).
    software_version : Optional[str]
        Version of the software tool / pipeline used for this benchmark run
    search_engine: Optional[str]
        Search engine used for this benchmark run
        (examples: "Andromeda", "Mascot", ...).
    search_engine_version : Optional[str]
        Version of the search engine used for this benchmark run.
    ident_fdr_psm : Optional[str]
        False discovery rate (FDR) threshold for peptide-spectrum match
        (PSM) validation ("0.01" = 1%).
    ident_fdr_peptide : Optional[str]
        False discovery rate (FDR) threshold for peptide validation ("0.01" = 1%).
    ident_fdr_protein : Optional[str]
        False discovery rate (FDR) threshold for protein validation ("0.01" = 1%).
    enable_match_between_runs : Optional[bool]
        Match between run (also named cross assignment) is enabled.
    precursor_mass_tolerance : Optional[str]
       Precursor mass tolerance used for the search.
       Given as an interval of upper and lower tolerance, e.g. [-20 ppm, 20 ppm].
    fragment_mass_tolerance : Optional[str]
        Precursor mass tolerance used for the search:
        Given as an interval of upper and lower tolerance, e.g. [-0.02 Da, 0.02 Da].
    enzyme : Optional[str]
        Enzyme used as parameter for the search. If several, use "|".
    allowed_miscleavages : Optional[int]
        Maximal number of missed cleavages allowed.
    min_peptide_length : Optional[str]
        Minimum peptide length (number of residues) allowed for the search.
    max_peptide_length : Optional[str]
        Maximum peptide length (number of residues) allowed for the search.
    fixed_mods : Optional[str]
        Fixed modifications searched for in the search. If several, separate with "|".
    variable_mods : Optional[str]
        Variable modifications searched for in the search. If several, separate with "|".
    max_mods : Optional[int]
        Maximal number of modifications per peptide
        (including fixed and variable modifications).
    min_precursor_charge : Optional[int]
        Minimum precursor charge allowed.
    max_precursor_charge : Optional[int]
        Maximum precursor charge allowed.
    spectral_library_generation : Optional[dict]
        Models used to generate spectral library (DIA-specific).
    scan_window : Optional[int]
        Scan window radius. Ideally corresponds to approximate
        average number of data points per peak (DIA-specific).
    quantification_method_DIANN : Optional[str]
        Quantification strategy used in the DIA-NN engine (DIANN-specific).
    second_pass : Optional[bool]
        Whether second pass search is enabled (DIANN-specific).
    protein_inference : Optional[str]
        Protein inference method used.
    """

    def __init__(
        self, filename=os.path.join(os.path.dirname(__file__), "json/Quant/lfq/ion/DDA/fields.json"), **kwargs
    ):
        """
        Reads the JSON file and initializes only the attributes present in the file.
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
        """
        return str({key: value for key, value in self.__dict__.items() if value is not None})

    def fill_none(self):
        """
        Fill all None values with np.nan
        """
        for key, value in self.__dict__.items():
            if value == "None":
                setattr(self, key, np.nan)


# Automatically initialize from fields.json if run directly
if __name__ == "__main__":
    proteo_params = ProteoBenchParameters()
    print(proteo_params)
