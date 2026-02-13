"""
Abstract base class for score calculation modules.
"""

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd


class ScoreBase(ABC):
    """
    Abstract base class for computing benchmark scores.

    This class defines the interface that all score calculators must implement,
    allowing for modular and extensible score computation for different benchmarking modules.
    """

    @abstractmethod
    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
        replicate_to_raw: dict,
    ) -> pd.DataFrame:
        """
        Generate intermediate data structure for scores.

        Parameters
        ----------
        filtered_df : pd.DataFrame
            DataFrame containing the filtered data.
        replicate_to_raw : dict
            Dictionary containing the replicate to raw mapping.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the intermediate data structure with computed scores.
        """
        pass
