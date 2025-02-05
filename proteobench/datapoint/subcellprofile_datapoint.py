from __future__ import annotations

import dataclasses
import hashlib
import logging
from collections import ChainMap, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pandas as pd

import proteobench

@dataclass
class SubcellprofileDatapoint:
    """
    A data structure used to store the results of a benchmark run.

    Attributes:
        id (str): Unique identifier for the benchmark run.
        software_name (str): Name of the software used in the benchmark.
        software_version (str): Version of the software.
        search_engine (str): Name of the search engine used.
        search_engine_version (str): Version of the search engine.
        ident_fdr_psm (float): False discovery rate for PSMs.
        ident_fdr_peptide (float): False discovery rate for peptides.
        ident_fdr_protein (float): False discovery rate for proteins.
        enable_match_between_runs (bool): Whether matching between runs is enabled.
        precursor_mass_tolerance (str): Mass tolerance for precursor ions.
        fragment_mass_tolerance (str): Mass tolerance for fragment ions.
        enzyme (str): Enzyme used for digestion.
        allowed_miscleavages (int): Number of allowed miscleavages.
        min_peptide_length (int): Minimum peptide length.
        max_peptide_length (int): Maximum peptide length.
        is_temporary (bool): Whether the data is temporary.
        intermediate_hash (str): Hash of the intermediate result.
        results (dict): A dictionary of metrics for the benchmark run.
        comments (str): Any additional comments.
        proteobench_version (str): Version of the Proteobench tool used.

    """

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
    results: dict = None # TODO: discuss what exactly is going in here
    comments: str = ""
    proteobench_version: str = ""
    depth_id_1: int = 0
    depth_profile_1: int = 0
    depth_id_3: int = 0
    depth_profile_3: int = 0


    def generate_id(self) -> None:
        """
        Generates a unique ID for the benchmark run by combining the software name and a timestamp.

        This ID is used to uniquely identify each run of the benchmark.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = "_".join([self.software_name, str(time_stamp)])
        logging.info(f"Assigned the following ID to this run: {self.id}")

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame, input_format: str, user_input: dict, default_cutoff_min_prec: int = 3
    ) -> pd.Series:
        """
        Generates a Datapoint object containing metadata and results from the benchmark run.

        Args:
            intermediate (pd.DataFrame): The intermediate DataFrame containing benchmark results.
            input_format (str): The format of the input data (e.g., file format).
            user_input (dict): User-defined input values for the benchmark.
            default_cutoff_min_prec (int, optional): The default minimum precursor cutoff value. Defaults to 3.

        Returns:
            pd.Series: A Pandas Series containing the Datapoint's attributes as key-value pairs.
        """
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        if "comments_for_plotting" not in user_input.keys():
            user_input["comments_for_plotting"] = ""

        try:
            user_input = defaultdict(
                user_input.default_factory,  # Preserve the default factory
                {key: ("" if value is None else value) for key, value in user_input.items()},
            )
        except AttributeError:
            user_input = {key: ("" if value is None else value) for key, value in user_input.items()}

        result_datapoint = SubcellprofileDatapoint(
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
            comments=user_input["comments_for_plotting"],
            proteobench_version=proteobench.__version__,
        )

        result_datapoint.generate_id()


        # calculate depth, reproducibility and profiling precision
        results = dict(ChainMap(*[SubcellprofileDatapoint.get_metrics(intermediate, nr_observed) for nr_observed in range(1, 7)]))
        result_datapoint.results = results
        results_series = pd.Series(dataclasses.asdict(result_datapoint))

        return results_series

    @staticmethod
    def get_metrics(df: pd.DataFrame, min_nr_observed: int = 4) -> Dict[int, Dict[str, float]]:
        """
        Computes various statistical metrics from the provided DataFrame for the benchmark.

        Args:
            df (pd.DataFrame): The DataFrame containing the benchmark results.
            min_nr_observed (int, optional): The minimum number of consecutive observed values for a valid computation. Defaults to 4.

        Returns:
            dict: A dictionary containing computed metrics such as 'depth_id', 'depth_profile', etc.
        """
        # Filter DataFrame by the minimum number of observations
        # TODO