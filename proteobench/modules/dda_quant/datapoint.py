import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np


@dataclass
class Datapoint:
    """Data used to stored the"""

    id: str = None
    search_engine: str = None
    software_version: int = 0
    fdr_psm: int = 0
    fdr_peptide: int = 0
    fdr_protein: int = 0
    MBR: bool = False
    precursor_tol: int = 0
    precursor_tol_unit: str = "Da"
    fragment_tol: int = 0
    fragment_tol_unit: str = "Da"
    enzyme_name: str = None
    missed_cleavages: int = 0
    min_pep_length: int = 0
    max_pep_length: int = 0
    weighted_sum: int = 0
    nr_prec: int = 0
    is_temporary: bool = True
    intermediate_hash: str = ""
    # TODO add threshold value used for presence ion/peptidoform
    nr_missing: int = 0
    # fixed_mods: [],
    # variable_mods: [],
    # max_number_mods_pep: int = 0,
    # precursor_charge: int = 0,
    # reproducibility: int = 0,
    # mean_reproducibility: int = 0,

    def calculate_missing_quan_prec(self, df, nr_missing_0):
        # TODO: unclear what this function does
        # should we compute ratio of removed features when filtering for nr_missing?
        nr_quan_prec_missing = []

        return nr_quan_prec_missing

    # TODO rename to be more specific what function computes?
    def calculate_plot_data(self, df):
        # compute mean of epsilon column in df
        # take abs value of df["epsilon"]
        # TODO use nr_missing to filter df before computing stats.
        self.weighted_sum = round(df["epsilon"].abs().mean(), ndigits=3)
        self.nr_prec = len(df)

    def generate_id(self):
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = (
            self.search_engine
            + "_"
            + str(self.software_version)
            + "_"
            + str(time_stamp)
        )
        logging.info(f"Assigned the following ID to this run: {self.id}")

    def dump_json_object(self, file_name):
        f = open(file_name, "a")
        f.write(json.dumps(asdict(self)))
        f.close()
