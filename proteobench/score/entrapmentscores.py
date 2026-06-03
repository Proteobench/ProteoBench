"""
Module containing plasma quantification score calculators (PYE - Plasma Year Edition).
"""

from typing import Dict

import pandas as pd

from proteobench.exceptions import ParseError
from proteobench.score.score_base import ScoreBase


class EntrapmentScores(ScoreBase):
    """
    Class for computing entrapment scores for entrapment benchmarking.

    This class inherits from ScoreBase and extends it with entrapment metrics
    and calculations.

    Parameters
    ----------
    precursor_column_name : str
        Name of the precursor column.
    """

    def __init__(self):
        """
        Initialize the EntrapmentScores object.
        """

    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate intermediate data structure for entrapment scores.

        Parameters
        ----------
        filtered_df : pd.DataFrame
            DataFrame containing the filtered data.
        Returns
        -------
        pd.DataFrame
            DataFrame containing the intermediate data structure.
        """

        # select columns which are relevant for the statistics
        # TODO, this should be handled different, probably in the parse settings

        necessary_columns = ["Raw file", "Peptide", "Sequence", "Charge", "Q-Value", "PEP", "Protein Group"]
        for col in necessary_columns:
            if col not in filtered_df.columns:
                raise ParseError(f"Necessary column '{col}' not found in the input DataFrame.")

        precursor_group_columns = ["Peptide", "Sequence", "Charge"]

        # R equivalent:
        # b <- b %>% group_by(peptide, mod_peptide, charge) %>%
        #   arrange(q_value, PEP) %>%
        #   filter(row_number() == 1) %>%
        #   ungroup()
        filtered_df = (
            filtered_df.sort_values(["Q-Value", "PEP"], kind="mergesort")
            .groupby(precursor_group_columns, as_index=False, sort=False)
            .head(1)
            .reset_index(drop=True)
        )

        # R equivalent:
        # b <- b %>% arrange(q_value, PEP) %>% mutate(score=row_number())
        filtered_df = filtered_df.sort_values(["Q-Value", "PEP"], kind="mergesort").reset_index(drop=True)
        filtered_df["Score"] = filtered_df.index + 1

        return filtered_df[["Raw file", "Peptide", "Sequence", "Charge", "Q-Value", "Score", "PEP", "Protein Group"]]

    def calculate_combined_fdp(
        df: pd.DataFrame,
    ) -> Dict[int, float]:
        """
        Compute the false discovery proportion (FDP) for the given DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate file for which to compute the FDP.

        Returns
        -------
        Float
            The computed FDP value.
        """

        fdp = 0.01

        return fdp

    def calculate_paired_fdp(
        df: pd.DataFrame,
    ) -> Dict[int, float]:
        """
        Compute the paired false discovery proportion (FDP) for the given DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate file for which to compute the paired FDP.

        Returns
        -------
        Float
            The computed paired FDP value.
        """

        paired_fdp = 0.01

        return paired_fdp
