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

        # The following steps are performed to generate the intermediate data structure:
        # 1. Group the DataFrame by the specified precursor group columns (Peptide,
        #    Sequence, Charge).
        # 2. Within each group, sort the entries by Q-Value and PEP in ascending order.
        # 3. Filter the groups to retain only the top entry (the one with the lowest Q-Value and PEP) for each group.
        # 4. After filtering, sort the resulting DataFrame again by Q-Value and PEP in ascending order.
        # 5. Assign a score to each entry based on its rank in the sorted DataFrame

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

        # assign 'entrapment' or 'target': if at least one protein in the group is target, the whole group is target, otherwise it is entrapment

        def assign_target_entrapment(protein_group: str) -> str:
            proteins = protein_group.split(";")
            for protein in proteins:
                if not protein.endswith("_p_target"):
                    return "target"
            return "entrapment"

        filtered_df["Target or Entrapment"] = filtered_df["Protein Group"].apply(assign_target_entrapment)

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
        nr_targets = df[df["Target or Entrapment"] == "target"].shape[0]

        fdp_lower_bound = nr_entrapments / (nr_targets + nr_entrapments)

        return fdp_lower_bound

    @staticmethod
    def calculate_paired_fdp(
        df: pd.DataFrame,
        filepath_paired: str = "../proteobench/score/static_files/ProteoBenchFASTA_Entrapment_Human_with_contaminants_entrapment_pep.txt",
    ) -> Dict[int, float]:
        """
        Compute the paired false discovery proportion (FDP) for the given DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate file for which to compute the paired FDP.
        filepath_paired : str
            File path to the paired mapping file for computing the paired FDP.

        Returns
        -------
        Float
            The computed paired FDP value.
        """

        # return 0.01

        mapping_df = pd.read_csv(filepath_paired, sep="\t", index_col=False)
        # print(mapping_df.head())
        # print(mapping_df.columns)

        # safety check: are all identified peptides in the mapping file?
        missing_peptides = set(df["Peptide"]) - set(mapping_df["sequence"])
        if missing_peptides:
            # raise ValueError(f"The following peptides are missing in the mapping file: {missing_peptides}")
            print(f"Warning: The following peptides are missing in the mapping file: {missing_peptides}")
            # remove missing peptides from the df
            df = df[~df["Peptide"].isin(missing_peptides)]

        # add peptide pair index from the mapping file
        df = df.merge(
            mapping_df[["sequence", "peptide_pair_index"]],
            how="left",
            left_on="Peptide",
            right_on="sequence",
        )
        # print(df)
        # print(df.columns)

        # sort by score (probably already sorted, but just to be sure)
        df = df.sort_values("Score", ascending=True).reset_index(drop=True)  # The lower the better, so ascending order

        # pre-calculate some dataframes
        df["nr_targets"] = (df["Target or Entrapment"] == "target").cumsum()
        df["nr_entrapments"] = (df["Target or Entrapment"] == "entrapment").cumsum()

        # print(df.head())

        # get identification where we have targets and entrapments
        df_targets_only = df[df["Target or Entrapment"] == "target"]
        df_entraps_only = df[df["Target or Entrapment"] == "entrapment"]

        # print(df_targets_only.head())

        target_entrap_ids = df_targets_only[["Peptide", "Score", "Q-Value", "peptide_pair_index"]].merge(
            df_entraps_only[["Peptide", "Score", "Q-Value", "peptide_pair_index"]],
            how="inner",
            on="peptide_pair_index",
            suffixes=("_target", "_entrap"),
        )

        # print(target_entrap_ids.head())

        # calculate the FDP by paired method

        Nr_E = df["nr_entrapments"].iloc[-1]  # total number of entrapments
        Nr_T = df["nr_targets"].iloc[-1]  # total number of targets

        s = df["Score"].iloc[-1]  # score threshold (score of the last identified feature)
        # EsT: number of discovered entrapment peptides whose paired target peptide has not been discovered
        Nr_E_s_T = target_entrap_ids[
            (target_entrap_ids["Score_entrap"] <= s) & (target_entrap_ids["Score_target"] > s)
        ].shape[0]

        # ETs: number of discovered entrapment peptides whose paired target peptide has also been discovered, but with worse score (here: higher)
        Nr_E_T_s = target_entrap_ids[
            (target_entrap_ids["Score_entrap"] > target_entrap_ids["Score_target"])
            & (target_entrap_ids["Score_target"] >= s)
        ].shape[0]

        fdp_estimation = (Nr_E + Nr_E_s_T + 2 * Nr_E_T_s) / (Nr_T + Nr_E)

        # print(df.head())
        # print(df.columns)

        return fdp_estimation

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

    @staticmethod
    def calculate_metrics(
        df: pd.DataFrame,
    ) -> Dict[str, float]:
        """
        Handle the calculation of all entrapment metrics for the given DataFrame.
        Ensures 1% FDR filtering for the main plot metrics.
        Handles categorisation into valid, invalid, and inconclusive based on bound values.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the intermediate file for which to compute the metrics.

        Returns
        -------
        Dict[str, float]
            A dictionary containing all computed metric values.
        """

        reported_fdr = EntrapmentScores.calculate_reported_fdr(df)
        fdr_ensured_df = df[df["Q-Value"] <= 0.01]

        combined_fdp = EntrapmentScores.calculate_upper_bound_combined_fdp(fdr_ensured_df)
        lower_bound_fdp = EntrapmentScores.calculate_lower_bound_fdp(fdr_ensured_df)
        paired_fdp = EntrapmentScores.calculate_paired_fdp(fdr_ensured_df)

        category_combined = EntrapmentScores.categorise_metric(lower_bound_fdp, combined_fdp, 0.01)
        category_paired = EntrapmentScores.categorise_metric(lower_bound_fdp, paired_fdp, 0.01)

        return {
            "nr_id_features": fdr_ensured_df.shape[0],
            "reported_fdr_parsed_from_input": reported_fdr,
            "combined_FDP": combined_fdp,
            "lower_bound_FDP": lower_bound_fdp,
            "paired_FDP": paired_fdp,
            "category_combined": category_combined,
            "category_paired": category_paired,
        }
