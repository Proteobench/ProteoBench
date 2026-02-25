"""
Module containing quantification score calculators.
"""

from typing import Dict

import numpy as np
import pandas as pd

from proteobench.score.score_base import ScoreBase


class QuantScoresHYE(ScoreBase):
    """
    Class for computing quantification scores for LFQ benchmarking.

    This class implements the ScoreBase interface to compute quantification-specific metrics
    including condition statistics, fold changes, and epsilon (difference) values.

    Parameters
    ----------
    species_expected_ratio : dict
        Dictionary containing the expected ratios for each species.
    species_dict : dict
        Dictionary containing the species names and their column mappings.
    feature_column_name : str
        Name of the feature column. It could be "proteingroup", or "precursor ion" or "peptidoform". See _format_by_analysis_level in parse_settings.py for more details.
    """

    def __init__(self, feature_column_name: str, species_expected_ratio, species_dict: Dict[str, str]):
        """
        Initialize the QuantScoresHYE object.

        Parameters
        ----------
        feature_column_name : str
            Name of the feature column. It could be "proteingroup", "precursor ion", or "peptidoform". See _format_by_analysis_level in parse_settings.py for more details.
        species_expected_ratio : dict
            Dictionary containing the expected ratios for each species.
        species_dict : dict
            Dictionary containing the species names and their column mappings.
        """
        self.feature_column_name = feature_column_name
        self.species_expected_ratio = species_expected_ratio
        self.species_dict = species_dict

    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
        replicate_to_raw: dict,
    ) -> pd.DataFrame:
        """
        Generate intermediate data structure for quantification scores.

        Parameters
        ----------
        filtered_df : pd.DataFrame
            DataFrame containing the filtered data.
        replicate_to_raw : dict
            Dictionary containing the replicate to raw mapping.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the intermediate data structure.
        """

        # select columns which are relavant for the statistics
        # TODO, this should be handled different, probably in the parse settings
        print(
            f"Debug: Starting to generate intermediate data structure with filtered_df columns: {filtered_df.columns} and replicate_to_raw: {replicate_to_raw}. fealure_column_name: {self.feature_column_name}"
        )

        relevant_columns_df = filtered_df[["Raw file", self.feature_column_name, "Intensity"]].copy()
        print(
            f"Debug: After selecting relevant columns, relevant_columns_df columns: {relevant_columns_df.columns} and head: {relevant_columns_df.head()}"
        )
        print(
            f"Debug: df after filtering for feature of interest {self.feature_column_name} has shape: {relevant_columns_df.shape}"
        )
        replicate_to_raw_df = QuantScoresHYE.convert_replicate_to_raw(replicate_to_raw)
        print(
            f"Debug: After converting replicate_to_raw to DataFrame, replicate_to_raw_df columns: {replicate_to_raw_df.columns} and head: {replicate_to_raw_df.head()}"
        )
        print(
            f"Debug: checking that {replicate_to_raw.values()} are present in relevant_columns_df['Raw file']: {list(filtered_df.columns)}"
        )

        all_present = all(
            item in list(filtered_df.columns) for sublist in replicate_to_raw.values() for item in sublist
        )
        print(f"Debug: All runs from replicate_to_raw are present in filtered_df: {all_present}")

        if not all_present:
            raise Exception("Not all runs are present in the quantification file")

        print(
            f"Debug: set up relevant column df by merging with replicate_to_raw_df, relevant_columns_df columns before merge: {relevant_columns_df.columns} and head: {relevant_columns_df.head()}"
        )
        # add column "Condition" to filtered_df_p1 using inner join on "Raw file"
        relevant_columns_df = pd.merge(relevant_columns_df, replicate_to_raw_df, on="Raw file", how="inner")
        print(
            f"Debug: After merging with replicate_to_raw_df, relevant_columns_df columns: {relevant_columns_df.columns} and head: {relevant_columns_df.head()}"
        )
        quant_df = QuantScoresHYE.compute_condition_stats(
            relevant_columns_df,
            min_intensity=0,
            feature_of_interest=self.feature_column_name,
        )

        species_feature = list(self.species_dict.values())
        species_feature.append(self.feature_column_name)
        feature_to_species = filtered_df[species_feature].drop_duplicates()
        # merge dataframes quant_df and species_quant_df and feature_to_species using feature_of_interest as index
        print(
            f"Debug: Before merging with feature_to_species, quant_df columns: {quant_df.columns} and head: {quant_df.head()}"
        )
        quant_df_withspecies = pd.merge(quant_df, feature_to_species, on=self.feature_column_name, how="inner")
        print(
            f"Debug: After merging with feature_to_species, quant_df_withspecies columns: {quant_df_withspecies.columns} and head: {quant_df_withspecies.head()}"
        )
        species_expected_ratio = self.species_expected_ratio
        res = QuantScoresHYE.compute_epsilon(quant_df_withspecies, self.species_expected_ratio)
        print(f"Debug: After computing epsilon, result: {res}")
        return res

    @staticmethod
    def convert_replicate_to_raw(replicate_to_raw: dict) -> pd.DataFrame:
        """
        Convert replicate_to_raw dictionary into a dataframe.

        Parameters
        ----------
        replicate_to_raw : dict
            Dictionary containing the replicate to raw mapping.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the replicate to raw mapping.
        """
        replicate_to_raw_df = pd.DataFrame(replicate_to_raw.items(), columns=["Condition", "Raw file"])
        replicate_to_raw_df = replicate_to_raw_df.explode("Raw file")
        return replicate_to_raw_df

    @staticmethod
    def compute_condition_stats(
        relevant_columns_df: pd.DataFrame,
        min_intensity=0,
        feature_of_interest=str,
    ) -> pd.DataFrame:
        """
        Method used to compute precursor/protein group statistics, such as number of observations, CV, mean per condition etc.

        Parameters
        ----------
        relevant_columns_df : pd.DataFrame
            DataFrame containing the relevant columns for the statistics.
        min_intensity : int, optional
            Minimum intensity value to filter for. Defaults to 0.
        feature_of_interest : str
            Name of the feature column.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the feature statistics.
        """

        ## check that depending on the selected feature of interest, the corresponding column is present in the dataframe
        if feature_of_interest not in relevant_columns_df.columns:
            raise Exception(
                f"{feature_of_interest} column is not present in the dataframe, cannot compute {feature_of_interest} statistics"
            )

        # fiter for min_intensity
        relevant_columns_df = relevant_columns_df[relevant_columns_df["Intensity"] > min_intensity]

        # TODO: check if this is still needed / TODO: if we keep, shall we use mean value?
        # sum intensity values of the same feature and "Raw file" using the sum
        quant_raw_df_int = (
            relevant_columns_df.groupby([feature_of_interest, "Raw file", "Condition"])["Intensity"]
            .agg(Intensity="sum", Count="size")
            .reset_index()
        )

        # add column "log_Intensity" to quant_raw_df
        quant_raw_df_int["log_Intensity"] = np.log2(quant_raw_df_int["Intensity"])

        # compute the mean of the log_Intensity per feature_of_interest and "Condition"
        quant_raw_df_count = (quant_raw_df_int.groupby([feature_of_interest])).agg(nr_observed=("Raw file", "size"))

        # pivot filtered_df_p1 to wide where index feature_of_interest, columns Raw file and values Intensity
        intensities_wide = quant_raw_df_int.pivot(
            index=feature_of_interest, columns="Raw file", values="Intensity"
        ).reset_index()

        quant_raw_df = (
            quant_raw_df_int.groupby([feature_of_interest, "Condition"])
            .agg(
                log_Intensity_mean=("log_Intensity", "mean"),
                log_Intensity_std=("log_Intensity", "std"),
                Intensity_mean=("Intensity", "mean"),
                Intensity_std=("Intensity", "std"),
                Sum=("Intensity", "sum"),
                nr_obs_group=("Intensity", "size"),
            )
            .reset_index()
        )

        # compute coefficient of variation (CV) of the log_Intensity_mean and log_Intensity_std
        quant_raw_df["CV"] = quant_raw_df["Intensity_std"] / quant_raw_df["Intensity_mean"]
        # pivot dataframe wider so for each condition variable there is a column with log_Intensity_mean, log_Intensity_std, Intensity_mean, Intensity_std and CV
        quant_raw_df = quant_raw_df.pivot(
            index=feature_of_interest,
            columns="Condition",
            values=[
                "log_Intensity_mean",
                "log_Intensity_std",
                "Intensity_mean",
                "Intensity_std",
                "CV",
            ],
        ).reset_index()

        quant_raw_df.columns = [f"{x[0]}_{x[1]}" if len(str(x[1])) > 0 else x[0] for x in quant_raw_df.columns]

        quant_raw_df["log2_A_vs_B"] = quant_raw_df["log_Intensity_mean_A"] - quant_raw_df["log_Intensity_mean_B"]

        quant_raw_df = pd.merge(quant_raw_df, intensities_wide, on=feature_of_interest, how="inner")
        quant_raw_df = pd.merge(quant_raw_df, quant_raw_df_count, on=feature_of_interest, how="inner")
        return quant_raw_df

    @staticmethod
    def compute_epsilon(withspecies, species_expected_ratio) -> pd.DataFrame:
        """
        Compute epsilon for each species in species_expected_ratio.

        Parameters
        ----------
        withspecies : pd.DataFrame
            DataFrame containing the species columns and the log2_A_vs_B column.
        species_expected_ratio : dict
            Dictionary containing the expected ratios for each species.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the epsilon values.
        """
        # for all columns named parse_settings.species_dict.values() compute the sum over the rows and add it to a new column "unique"
        withspecies["unique"] = withspecies[species_expected_ratio.keys()].sum(axis=1)

        # now remove all rows with withspecies["unique"] > 1
        withspecies_unique = withspecies[withspecies["unique"] == 1].copy()
        # for species in parse_settings.species_dict.values(), set all values in new column "species" to species if withe species is True
        for species in species_expected_ratio.keys():
            withspecies_unique.loc[withspecies_unique[species] == True, "species"] = species
            withspecies_unique.loc[withspecies_unique[species] == True, "log2_expectedRatio"] = np.log2(
                species_expected_ratio[species]["A_vs_B"]
            )

        withspecies_unique["epsilon"] = withspecies_unique["log2_A_vs_B"] - withspecies_unique["log2_expectedRatio"]

        # Compute per-species empirical centers for precision metrics
        withspecies_unique["log2_empirical_median"] = withspecies_unique.groupby("species")["log2_A_vs_B"].transform(
            "median"
        )
        withspecies_unique["log2_empirical_mean"] = withspecies_unique.groupby("species")["log2_A_vs_B"].transform(
            "mean"
        )

        # Epsilon precision: deviation from empirical center (measures consistency, not accuracy)
        withspecies_unique["epsilon_precision_median"] = (
            withspecies_unique["log2_A_vs_B"] - withspecies_unique["log2_empirical_median"]
        )
        withspecies_unique["epsilon_precision_mean"] = (
            withspecies_unique["log2_A_vs_B"] - withspecies_unique["log2_empirical_mean"]
        )

        return withspecies_unique
