import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class Datapoint:
    """Data used to stored the"""

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
    # TODO add threshold value used for presence ion/peptidoform
    # nr_missing: int = 0
    results: dict = None
    # fixed_mods: [],
    # variable_mods: [],
    # max_mods: int = 0,
    # min_precursor_charge: int = 0,
    # max_precursor_charge: int = 0,
    # reproducibility: int = 0,
    # mean_reproducibility: int = 0,

    def generate_id(self):
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = self.search_engine + "_" + str(self.software_version) + "_" + str(time_stamp)
        logging.info(f"Assigned the following ID to this run: {self.id}")

    def to_plot_df(self):
        """Converts the datapoint to a pandas dataframe for plotting"""
        results_pd = pd.DataFrame(self.results).transpose()
        results_pd["nr_observed"] = results_pd.index
        results_pd = results_pd.reset_index(drop=True)

        df = pd.DataFrame([asdict(self)])
        xx = pd.concat([df] * len(results_pd))
        xx = xx.reset_index(drop=True)

        res = pd.concat([xx, results_pd], axis=1)
        return res
