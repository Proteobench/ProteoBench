import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np


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
    precursor_mass_tolerance: int = 0
    precursor_mass_tolerance_unit: str = "Da"
    fragment_mass_tolerance: int = 0
    fragment_mass_tolerance_unit: str = "Da"
    enzyme: str = None
    allowed_miscleavages: int = 0
    min_peptide_length: int = 0
    max_peptide_length: int = 0
    weighted_sum: int = 0
    nr_prec: int = 0
    is_temporary: bool = True
    intermediate_hash: str = ""
    # TODO do we want to save these values in the json?
    # fixed_mods: [],
    # variable_mods: [],
    # max_mods: int = 0,
    # min_precursor_charge: int = 0,
    # max_precursor_charge: int = 0,
    # reproducibility: int = 0,
    # mean_reproducibility: int = 0,

    def calculate_missing_quan_prec(self, df, nr_missing_0):
        nr_quan_prec_missing = []

        return nr_quan_prec_missing

    def calculate_plot_data(self, df):
        # compute mean of epsilon column in df
        # take abs value of df["epsilon"]
        self.weighted_sum = round(df["epsilon"].abs().mean(), ndigits=3)
        self.nr_prec = len(df)

    def generate_id(self):
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = self.search_engine + "_" + str(self.software_version) + "_" + str(time_stamp)
        logging.info(f"Assigned the following ID to this run: {self.id}")

    def dump_json_object(self, file_name):
        f = open(file_name, "a")
        f.write(json.dumps(asdict(self)))
        f.close()
