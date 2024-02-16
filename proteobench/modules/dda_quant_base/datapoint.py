import logging
from dataclasses import dataclass
from datetime import datetime

import pandas as pd


def filter_df_numquant_median_abs_epsilon(row, min_quant=3):
    if isinstance(list(row.keys())[0], str):
        min_quant = str(min_quant)
    if isinstance(row, dict) and min_quant in row and isinstance(row[min_quant], dict):
        return row[min_quant].get("median_abs_epsilon")
    return None


def filter_df_numquant_nr_prec(row: pd.Series, min_quant=3):
    if isinstance(list(row.keys())[0], str):
        min_quant = str(min_quant)
    if isinstance(row, dict) and min_quant in row and isinstance(row[min_quant], dict):
        return row[min_quant].get("nr_prec")
    return None


@dataclass
class Datapoint:
    """Data used to stored the"""

    # TODO add threshold value used for presence ion/peptidoform
    id: str = None
    software_name: str = None
    software_version: int = 0
    search_engine: str = None
    search_engine_version: int = 0
    ident_fdr_psm: int = 0
    ident_fdr_peptide: int = 0
    ident_fdr_protein: int = 0
    enable_match_between_runs: bool = False
    precursor_mass_tolerance: str = None
    fragment_mass_tolerance: str = None
    enzyme: str = None
    allowed_miscleavages: int = 0
    min_peptide_length: int = 0
    max_peptide_length: int = 0
    is_temporary: bool = True
    intermediate_hash: str = ""
    results: dict = None
    median_abs_epsilon: int = 0
    nr_prec: int = 0
    comments: str = ""

    # TODO do we want to save these values in the json?
    # fixed_mods: [],
    # variable_mods: [],
    # max_mods: int = 0,
    # min_precursor_charge: int = 0,
    # max_precursor_charge: int = 0,
    # reproducibility: int = 0,
    # mean_reproducibility: int = 0,

    def generate_id(self):
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = self.software_name + "_" + str(self.software_version) + "_" + str(time_stamp)
        logging.info(f"Assigned the following ID to this run: {self.id}")
