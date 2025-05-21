"""
This module provides functionality for storing the de novo metrics.
"""
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
class DenovoDatapoint:
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
        median_abs_epsilon (float): Median absolute epsilon value for the benchmark.
        mean_abs_epsilon (float): Mean absolute epsilon value for the benchmark.
        nr_prec (int): Number of precursors identified.
        comments (str): Any additional comments.
        proteobench_version (str): Version of the Proteobench tool used.
    """

    id: str = None
    software_name: str = None
    software_version: int = 0
    checkpoint: str = None
    n_beams: int = None
    n_peaks: int = None
    precursor_mass_tolerance: str = None
    min_peptide_length: int = 0
    max_peptide_length: int = 0
    min_mz: int = 0
    max_mz: int = 50000
    min_intensity: int = 0
    max_intensity: int = 1
    tokens: str = None
    min_precursor_charge: int = 1
    max_precursor_charge: int = None
    remove_precursor_charge: str = None
    isotope_error_range: str = None
    decoding_strategy: str = None
    is_temporary: bool = True
    intermediate_hash: str = ""
    results: dict = None
    # Add other elements here
    accuracy: int = 0
    recall: int = 0
    comments: str = ""
    proteobench_version: str = ""

    def generate_id(self) -> None:
        """
        Generate a unique ID for the benchmark run by combining the software name and a timestamp.

        This ID is used to uniquely identify each run of the benchmark.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = "_".join([self.software_name, str(time_stamp)])
        logging.info(f"Assigned the following ID to this run: {self.id}")

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame,
        input_format: str,
        user_input: dict
        # Maybe add here aa/peptide precision
        # And also type of match required (exact/mass-based)
    ) -> pd.Series:
        """
         Generate a Datapoint object containing metadata and results from the benchmark run.
        """
        # Call get_metrics here
        pass

    @staticmethod
    def get_metrics(df: pd.DataFrame):
        """
        Compute various statistical metrics from the provided DataFrame for the benchmark.
        """
        pass