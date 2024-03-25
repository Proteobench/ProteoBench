from __future__ import annotations

import dataclasses
import hashlib
import logging
from collections import ChainMap
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

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame, input_format: str, user_input: dict, default_cutoff_min_prec: int = 3
    ) -> pd.Series:
        """Method used to compute metadata for the provided result."""
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        if "comments_for_submission" not in user_input.keys():
            user_input["comments_for_submission"] = ""

        result_datapoint = Datapoint(
            id=input_format + "_" + user_input["software_version"] + "_" + formatted_datetime,
            software_name=input_format,
            software_version=user_input["software_version"],
            search_engine=user_input["search_engine"],
            search_engine_version=user_input["search_engine_version"],
            ident_fdr_psm=user_input["ident_fdr_psm"],
            ident_fdr_peptide=user_input["ident_fdr_peptide"],
            ident_fdr_protein=user_input["ident_fdr_protein"],
            enable_match_between_runs=user_input["enable_match_between_runs"],
            precursor_mass_tolerance=user_input["precursor_mass_tolerance"],
            fragment_mass_tolerance=user_input["fragment_mass_tolerance"],
            enzyme=user_input["enzyme"],
            allowed_miscleavages=user_input["allowed_miscleavages"],
            min_peptide_length=user_input["min_peptide_length"],
            max_peptide_length=user_input["max_peptide_length"],
            intermediate_hash=str(hashlib.sha1(intermediate.to_string().encode("utf-8")).hexdigest()),
            comments=user_input["comments_for_submission"],
        )

        result_datapoint.generate_id()
        results = dict(ChainMap(*[Datapoint.get_metrics(intermediate, nr_observed) for nr_observed in range(1, 7)]))
        result_datapoint.results = results
        result_datapoint.median_abs_epsilon = result_datapoint.results[default_cutoff_min_prec]["median_abs_epsilon"]

        results_series = pd.Series(dataclasses.asdict(result_datapoint))

        return results_series

    @staticmethod
    def get_metrics(df, min_nr_observed=1):
        # compute mean of epsilon column in df
        # take abs value of df["epsilon"]
        # TODO use nr_missing to filter df before computing stats.
        df_slice = df[df["nr_observed"] >= min_nr_observed]
        nr_prec = len(df_slice)
        # median abs unafected by outliers
        median_abs_epsilon = df_slice["epsilon"].abs().mean()
        # variance affected by outliers
        variance_epsilon = df_slice["epsilon"].var()
        # TODO more concise way to describe distribution of CV's
        cv_median = (df_slice["CV_A"].median() + df_slice["CV_B"].median()) / 2
        cv_q75 = (df_slice["CV_A"].quantile(0.75) + df_slice["CV_B"].quantile(0.75)) / 2
        cv_q90 = (df_slice["CV_A"].quantile(0.9) + df_slice["CV_B"].quantile(0.9)) / 2
        cv_q95 = (df_slice["CV_A"].quantile(0.95) + df_slice["CV_B"].quantile(0.95)) / 2

        return {
            min_nr_observed: {
                "median_abs_epsilon": median_abs_epsilon,
                "variance_epsilon": variance_epsilon,
                "nr_prec": nr_prec,
                "CV_median": cv_median,
                "CV_q90": cv_q90,
                "CV_q75": cv_q75,
                "CV_q95": cv_q95,
            }
        }
