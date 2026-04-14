"""
Module containing plasma quantification score calculators (PYE - Plasma Year Edition).
"""

from typing import Dict

import pandas as pd

from proteobench.score.quantscoresHYE import QuantScoresHYE


class QuantScoresPYE(QuantScoresHYE):
    """
    Class for computing quantification scores for plasma benchmarking (PYE module).

    This class inherits from QuantScoresHYE and extends it with plasma-specific metrics
    and calculations. It follows the same ScoreBase interface pattern but adds custom
    logic tailored for plasma quantification benchmarking.

    Parameters
    ----------
    precursor_column_name : str
        Name of the precursor column.
    species_expected_ratio : dict
        Dictionary containing the expected ratios for each species.
    species_dict : dict
        Dictionary containing the species names and their column mappings.
    """

    def __init__(self, precursor_column_name: str, species_expected_ratio, species_dict: Dict[str, str]):
        """
        Initialize the QuantScoresPYE object.

        Parameters
        ----------
        precursor_column_name : str
            Name of the precursor.
        species_expected_ratio : dict
            Dictionary containing the expected ratios for each species.
        species_dict : dict
            Dictionary containing the species names.
        """
        super().__init__(precursor_column_name, species_expected_ratio, species_dict)

    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
        replicate_to_raw: dict,
    ) -> pd.DataFrame:
        """
        Generate intermediate data structure for plasma quantification scores.

        This method extends the parent class implementation with plasma-specific
        metric calculations.

        Parameters
        ----------
        filtered_df : pd.DataFrame
            DataFrame containing the filtered data.
        replicate_to_raw : dict
            Dictionary containing the replicate to raw mapping.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the intermediate data structure with plasma-specific metrics.
        """
        # Call parent class implementation to get base metrics
        intermediate_df = super().generate_intermediate(filtered_df, replicate_to_raw)
        return intermediate_df
