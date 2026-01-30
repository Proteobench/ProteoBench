"""
Abstract base class for datapoint modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd


@dataclass
class DatapointBase(ABC):
    """
    Abstract base class for benchmark datapoints.

    This class defines the interface that all datapoint types must implement,
    allowing for modular and extensible datapoint handling for different benchmarking modules.

    Subclasses should define their own attributes specific to their benchmarking module.
    """

    @abstractmethod
    def generate_id(self) -> None:
        """
        Generate a unique ID for the benchmark run.

        This ID should uniquely identify each run of the benchmark.
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_datapoint(intermediate: pd.DataFrame, input_format: str, user_input: dict, **kwargs) -> pd.Series:
        """
        Generate a datapoint object containing metadata and results from the benchmark run.

        Parameters
        ----------
        intermediate : pd.DataFrame
            The intermediate DataFrame containing benchmark results.
        input_format : str
            The format of the input data (e.g., software tool name).
        user_input : dict
            User-defined input values for the benchmark.
        **kwargs : dict
            Additional module-specific parameters.

        Returns
        -------
        pd.Series
            A Pandas Series containing the datapoint's attributes as key-value pairs.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_metrics(df: pd.DataFrame, **kwargs) -> Dict[int, Dict[str, float]]:
        """
        Compute statistical metrics from the provided DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate results.
        **kwargs : dict
            Additional module-specific parameters.

        Returns
        -------
        Dict[int, Dict[str, float]]
            Dictionary mapping quantification cutoffs to their computed metrics.
        """
        pass
