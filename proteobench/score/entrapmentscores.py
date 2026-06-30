"""
Module containing plasma quantification score calculators (PYE - Plasma Year Edition).
"""

from typing import Dict

import numpy as np
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
        """Initialize the EntrapmentScores object."""
        pass

    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate intermediate data structure for entrapment scores.

        The input DataFrame must already have ``"Target or Entrapment"`` and
        ``"peptide_pair_index"`` columns populated by the caller (i.e. the
        benchmarking module applies the mapping file before this step).

        Parameters
        ----------
        filtered_df : pd.DataFrame
            DataFrame containing the filtered data with target/entrapment labels
            and peptide pair indices already assigned.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the intermediate data structure.
        """
        necessary_columns = [
            "Peptide",
            "Sequence",
            "Charge",
            "Q-Value",
            "Protein Group",
            "Target or Entrapment",
            "peptide_pair_index",
        ]
        for col in necessary_columns:
            if col not in filtered_df.columns:
                raise ParseError(f"Necessary column '{col}' not found in the input DataFrame.")

        if "Raw file" not in filtered_df.columns:
            filtered_df = filtered_df.copy()
            filtered_df["Raw file"] = ""

        scores_to_sort_by = ["Q-Value", "PEP"]
        if "PEP" not in filtered_df.columns:
            if "Expectation" in filtered_df.columns:
                filtered_df = filtered_df.copy()
                filtered_df["PEP"] = 1 - filtered_df["Expectation"]
            else:
                scores_to_sort_by.remove("PEP")

        precursor_group_columns = ["Peptide", "Sequence", "Charge"]

        # Deduplicate to one row per precursor: keep the hit with the lowest Q-Value (and PEP).
        # Then re-rank by the same sort order to assign a monotone Score column.
        filtered_df = (
            filtered_df.sort_values(scores_to_sort_by, kind="mergesort")
            .groupby(precursor_group_columns, as_index=False, sort=False)
            .head(1)
            .reset_index(drop=True)
        )
        filtered_df = filtered_df.sort_values(scores_to_sort_by, kind="mergesort").reset_index(drop=True)
        filtered_df["Score"] = filtered_df.index + 1

        return filtered_df[
            [
                "Raw file",
                "Peptide",
                "Sequence",
                "Charge",
                "Q-Value",
                "Score",
                "PEP",
                "Protein Group",
                "Target or Entrapment",
                "peptide_pair_index",
            ]
        ]

    @staticmethod
    def calculate_upper_bound_combined_fdp(
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
        # calculate the upper (combined method) bound (eq. 1 in Wen et al 2025)
        entr_fold = 1
        entr_ratio = 1 + 1 / entr_fold

        nr_entrapments = df[df["Target or Entrapment"] == "entrapment"].shape[0]
        nr_targets = df[df["Target or Entrapment"] == "target"].shape[0]

        fdp_ub = (nr_entrapments * entr_ratio) / (nr_targets + nr_entrapments)

        return fdp_ub

    @staticmethod
    def calculate_lower_bound_fdp(
        df: pd.DataFrame,
    ) -> Dict[int, float]:
        """
        Compute the lower bound false discovery proportion (FDP) for the given DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate file for which to compute the lower bound FDP.

        Returns
        -------
        Float
            The computed lower bound FDP value.
        """

        nr_entrapments = df[df["Target or Entrapment"] == "entrapment"].shape[0]
        print(f"Number of entrapments: {nr_entrapments}")
        nr_targets = df[df["Target or Entrapment"] == "target"].shape[0]
        print(f"Number of targets: {nr_targets}")

        fdp_lower_bound = nr_entrapments / (nr_targets + nr_entrapments)
        print(f"Lower bound FDP: {fdp_lower_bound}")

        return fdp_lower_bound

    @staticmethod
    def calculate_paired_fdp(
        df: pd.DataFrame,
    ) -> float:
        """
        Compute the paired false discovery proportion (FDP) for the given DataFrame.

        Requires ``peptide_pair_index`` to already be present in ``df`` (populated
        by the benchmarking module when applying the mapping file).

        Parameters
        ----------
        df : pd.DataFrame
            Intermediate DataFrame with ``peptide_pair_index`` already present.

        Returns
        -------
        float
            The computed paired FDP value.
        """
        return EntrapmentScores._paired_fdp_from_merged(df)

    @staticmethod
    def _paired_fdp_from_merged(df: pd.DataFrame) -> float:
        """
        Compute paired FDP from a DataFrame that already has a ``peptide_pair_index`` column.

        The numerator accumulates three terms (Wen et al. 2025 eq. 2):

        - ``Nr_E``: all identified entrapments.
        - ``Nr_E_s_T``: identified entrapments whose paired target is *not* identified
          in ``df`` (entrapment present, target absent — unambiguous false positive).
        - ``Nr_E_T_s``: identified pairs where the entrapment has a *better* score
          (lower rank) than its paired target — the entrapment out-competed the target,
          signalling FDR inflation; counted twice to reflect the pair's symmetric
          contribution.

        A left join from entrapments to targets is used so that unmatched entrapments
        (no identified paired target) contribute to ``Nr_E_s_T``.

        Parameters
        ----------
        df : pd.DataFrame
            Intermediate DataFrame with ``peptide_pair_index`` already merged in.
            Must contain ``Target or Entrapment``, ``Score``, and
            ``peptide_pair_index`` columns.

        Returns
        -------
        float
            Paired FDP estimate in [0, 1] (may exceed combined FDP in extreme cases).
        """
        df_targets = df[df["Target or Entrapment"] == "target"]
        df_entraps = df[df["Target or Entrapment"] == "entrapment"]

        Nr_E = len(df_entraps)
        Nr_T = len(df_targets)

        if (Nr_T + Nr_E) == 0:
            return 0.0

        # Pandas treats NaN == NaN as True in merge keys, which would spuriously join
        # all unmapped entrapments (pair_index=NaN) to all unmapped targets.
        # Drop rows with no pair index before joining, and collapse multiple PSMs per
        # peptide to the best (maximum) score to avoid many-to-many fan-out.
        entraps_best = (
            df_entraps.dropna(subset=["peptide_pair_index"]).groupby("peptide_pair_index", sort=False)["Score"].max()
        )
        targets_best = (
            df_targets.dropna(subset=["peptide_pair_index"]).groupby("peptide_pair_index", sort=False)["Score"].max()
        )

        # Left join: keep all mapped entrapment peptides; attach paired target score
        # when the target is also identified.  Unmatched rows have NaN Score_target.
        entrap_target = (
            entraps_best.rename("Score_entrap").to_frame().join(targets_best.rename("Score_target"), how="left")
        )

        # Nr_E_s_T: mapped entrapments with no identified paired target
        Nr_E_s_T = int(entrap_target["Score_target"].isna().sum())

        # Nr_E_T_s: pairs where entrapment has a better (higher) score than target
        paired = entrap_target.dropna(subset=["Score_target"])
        Nr_E_T_s = int((paired["Score_entrap"] > paired["Score_target"]).sum())

        return (Nr_E + Nr_E_s_T + 2 * Nr_E_T_s) / (Nr_T + Nr_E)

    def calculate_fdp_at_fdr_thresholds(
        self,
        df: pd.DataFrame,
        n_intervals: int = 10,
    ) -> Dict[float, Dict[str, float]]:
        """
        Compute lower-bound, combined, and paired FDP at Q-value thresholds.

        Thresholds are the union of ``n_intervals`` evenly-spaced values from
        ``max_q / n_intervals`` to ``max_q`` and the fixed set
        ``{0.001, 0.01, 0.05, 0.1, 1.0}`` capped at ``max_q``.
        The mapping file is loaded once and the pair-index merge is performed
        once; only the Q-value filter varies per step.

        Parameters
        ----------
        df : pd.DataFrame
            Intermediate DataFrame produced by ``generate_intermediate`` and
            produced by ``generate_intermediate``.
        n_intervals : int
            Number of evenly-spaced thresholds. Defaults to 10.

        Returns
        -------
        Dict[float, Dict[str, float]]
            Mapping of ``{threshold: {lower_bound_FDP, combined_FDP, paired_FDP, nr_id_features}}``.
            Thresholds where no targets are identified are omitted.
        """
        max_q = float(df["Q-Value"].max())
        fixed_thresholds = [t for t in (0.001, 0.01, 0.05, 0.1, 1.0) if t <= max_q]
        linspace_thresholds = list(np.linspace(max_q / n_intervals, max_q, n_intervals))
        thresholds = sorted(set(fixed_thresholds + linspace_thresholds))

        result: Dict[float, Dict[str, float]] = {}
        for threshold in thresholds:
            subset = df[df["Q-Value"] <= threshold]
            if subset.empty or (subset["Target or Entrapment"] == "target").sum() == 0:
                continue
            key = round(float(threshold), 8)
            lower = EntrapmentScores.calculate_lower_bound_fdp(subset)
            combined = EntrapmentScores.calculate_upper_bound_combined_fdp(subset)
            paired = EntrapmentScores._paired_fdp_from_merged(subset)
            result[key] = {
                "lower_bound_FDP": lower,
                "combined_FDP": combined,
                "paired_FDP": paired,
                "nr_id_features": int(subset.shape[0]),
                "category_combined": EntrapmentScores.categorise_metric(lower, combined, threshold),
                "category_paired": EntrapmentScores.categorise_metric(lower, paired, threshold),
            }

        return result

    @staticmethod
    def categorise_metric(
        lower_bound: float,
        upper_bound: float,
        fdr: float,
    ) -> str:
        """
        Categorise the FDR into
            valid: Upper bound lower than reported FDR
            invalid: Lower bound higher than reported FDR
            inconclusive: Lower bound lower than reported FDR but upper bound higher than reported FDR

        Parameters
        ----------
        lower_bound : float
            The lower bound for categorisation.
        upper_bound : float
            The upper bound for categorisation.
        fdr : float
            The false discovery rate for categorisation.

        Returns
        -------
        str
            The category of the metric value ("valid", "invalid", or "inconclusive").
        """

        if upper_bound <= fdr:
            return "valid"
        elif lower_bound > fdr:
            return "invalid"
        elif lower_bound <= fdr < upper_bound:
            return "inconclusive"
        else:
            raise ValueError("Invalid categorisation logic. Check the bounds and FDR values.")

    @staticmethod
    def calculate_reported_fdr(
        df: pd.DataFrame,
        score_col: str = "Q-Value",
    ) -> float:
        """
        Estimate the FDR threshold applied by the search engine from the output data.

        The reported FDR is inferred as the maximum score value in the DataFrame for
        the given score column. For Q-value-based outputs this equals the least
        significant accepted Q-value, which corresponds to the FDR cutoff the search
        engine applied. The ``score_col`` parameter makes the method applicable to
        different entrapment levels: use ``"Q-Value"`` for PSM/precursor level,
        or the appropriate column name for peptide- or protein-level outputs.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate data for one entrapment run.
            Must contain the column specified by ``score_col``.
        score_col : str, optional
            Name of the Q-value (or equivalent score) column. Defaults to
            ``"Q-Value"``.

        Returns
        -------
        float
            The maximum value found in ``score_col``, interpreted as the applied
            FDR threshold.
        """
        return float(df[score_col].max())

    def calculate_metrics(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, float]:
        """
        Handle the calculation of all entrapment metrics for the given DataFrame.

        The input ``df`` must already contain ``"Target or Entrapment"`` and
        ``"peptide_pair_index"`` columns (populated by the benchmarking module).

        Parameters
        ----------
        df : pd.DataFrame
            Intermediate DataFrame produced by ``generate_intermediate``.

        Returns
        -------
        Dict[str, float]
            A dictionary containing all computed metric values.
        """
        reported_fdr = EntrapmentScores.calculate_reported_fdr(df)

        combined_fdp = EntrapmentScores.calculate_upper_bound_combined_fdp(df)
        lower_bound_fdp = EntrapmentScores.calculate_lower_bound_fdp(df)
        paired_fdp = EntrapmentScores.calculate_paired_fdp(df)

        category_combined = EntrapmentScores.categorise_metric(lower_bound_fdp, combined_fdp, reported_fdr)
        category_paired = EntrapmentScores.categorise_metric(lower_bound_fdp, paired_fdp, reported_fdr)

        fdp_curve = self.calculate_fdp_at_fdr_thresholds(df)

        return {
            "nr_id_features": df.shape[0],
            "reported_fdr_parsed_from_input": reported_fdr,
            "combined_FDP": combined_fdp,
            "lower_bound_FDP": lower_bound_fdp,
            "paired_FDP": paired_fdp,
            "category_combined": category_combined,
            "category_paired": category_paired,
            "fdp_curve": fdp_curve,
        }
