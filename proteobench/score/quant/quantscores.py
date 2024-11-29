from typing import Dict, List

import numpy as np
import pandas as pd


class QuantScores:
    """
    A class for computing quantitative scores and statistics on precursor ions
    and their associated species in proteomics data.

    Attributes:
        precursor_name (str): The column name representing precursor ions.
        species_expected_ratio (dict): Expected ratios for species across conditions.
        species_dict (Dict[str, str]): Mapping of species flags to species names.
    """

    def __init__(self, precursor_name: str, species_expected_ratio: Dict[str, dict], species_dict: Dict[str, str]):
        """
        Initializes the QuantScores object.

        Parameters:
            precursor_name (str): The column name representing precursor ions.
            species_expected_ratio (dict): Expected ratios for species across conditions.
            species_dict (Dict[str, str]): Mapping of species flags to species names.
        """
        self.precursor_name = precursor_name
        self.species_expected_ratio = species_expected_ratio
        self.species_dict = species_dict

    def generate_intermediate(self, filtered_df: pd.DataFrame, replicate_to_raw: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Generates an intermediate DataFrame with computed statistics and epsilon values.

        Parameters:
            filtered_df (pd.DataFrame): Input DataFrame containing filtered data.
            replicate_to_raw (dict): Mapping of experimental conditions (replicates) to raw files.

        Returns:
            pd.DataFrame: A DataFrame with computed statistics and epsilon values.
        """
        # Extract relevant columns
        relevant_columns_df = filtered_df[["Raw file", self.precursor_name, "Intensity"]].copy()
        replicate_to_raw_df = QuantScores.convert_replicate_to_raw(replicate_to_raw)

        # Add the "Group" column by joining on "Raw file"
        relevant_columns_df = pd.merge(relevant_columns_df, replicate_to_raw_df, on="Raw file", how="inner")

        # Compute group-level statistics
        quant_df = QuantScores.compute_group_stats(
            relevant_columns_df,
            min_intensity=0,
            precursor=self.precursor_name,
        )

        # Map species to precursors and merge with quant_df
        species_prec_ion = list(self.species_dict.values())
        species_prec_ion.append(self.precursor_name)
        prec_ion_to_species = filtered_df[species_prec_ion].drop_duplicates()
        quant_df_withspecies = pd.merge(quant_df, prec_ion_to_species, on=self.precursor_name, how="inner")

        # Compute epsilon values
        res = QuantScores.compute_epsilon(quant_df_withspecies, self.species_expected_ratio)
        return res

    @staticmethod
    def convert_replicate_to_raw(replicate_to_raw: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Converts a replicate-to-raw mapping into a DataFrame.

        Parameters:
            replicate_to_raw (Dict[str, List[str]]): Mapping of replicates to raw files.

        Returns:
            pd.DataFrame: A DataFrame with "Group" and "Raw file" columns.
        """
        replicate_to_raw_df = pd.DataFrame(replicate_to_raw.items(), columns=["Group", "Raw file"])
        replicate_to_raw_df = replicate_to_raw_df.explode("Raw file")
        return replicate_to_raw_df

    @staticmethod
    def compute_group_stats(
        relevant_columns_df: pd.DataFrame, min_intensity: int = 0, precursor: str = "precursor ion"
    ) -> pd.DataFrame:
        """
        Computes statistics for precursor ions grouped by conditions.

        Parameters:
            relevant_columns_df (pd.DataFrame): Input DataFrame with precursor, raw file, and intensity columns.
            min_intensity (int): Minimum intensity threshold for filtering.
            precursor (str): Column name for precursor ions.

        Returns:
            pd.DataFrame: A DataFrame with group-level statistics.
        """
        # Filter by minimum intensity
        relevant_columns_df = relevant_columns_df[relevant_columns_df["Intensity"] > min_intensity]

        # Aggregate intensities and counts by precursor, raw file, and group
        quant_raw_df_int = (
            relevant_columns_df.groupby([precursor, "Raw file", "Group"])["Intensity"]
            .agg(Intensity="sum", Count="size")
            .reset_index()
        )

        # Add log-transformed intensities
        quant_raw_df_int["log_Intensity"] = np.log2(quant_raw_df_int["Intensity"])

        # Count observations per precursor
        quant_raw_df_count = quant_raw_df_int.groupby([precursor]).agg(nr_observed=("Raw file", "size"))

        # Pivot intensities to wide format
        intensities_wide = quant_raw_df_int.pivot(index=precursor, columns="Raw file", values="Intensity").reset_index()

        # Compute group-level statistics
        quant_raw_df = (
            quant_raw_df_int.groupby([precursor, "Group"])
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

        # Add coefficient of variation (CV)
        quant_raw_df["CV"] = quant_raw_df["Intensity_std"] / quant_raw_df["Intensity_mean"]

        # Pivot to wide format for each group
        quant_raw_df = quant_raw_df.pivot(
            index=precursor,
            columns="Group",
            values=[
                "log_Intensity_mean",
                "log_Intensity_std",
                "Intensity_mean",
                "Intensity_std",
                "CV",
            ],
        ).reset_index()

        quant_raw_df.columns = [f"{x[0]}_{x[1]}" if len(str(x[1])) > 0 else x[0] for x in quant_raw_df.columns]

        # Compute log2 fold change between groups A and B
        quant_raw_df["log2_A_vs_B"] = quant_raw_df["log_Intensity_mean_A"] - quant_raw_df["log_Intensity_mean_B"]

        # Merge with wide format intensities and observation counts
        quant_raw_df = pd.merge(quant_raw_df, intensities_wide, on=precursor, how="inner")
        quant_raw_df = pd.merge(quant_raw_df, quant_raw_df_count, on=precursor, how="inner")
        return quant_raw_df

    @staticmethod
    def compute_epsilon(withspecies: pd.DataFrame, species_expected_ratio: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Computes epsilon values based on observed and expected log2 ratios.

        Parameters:
            withspecies (pd.DataFrame): DataFrame with species and observed ratios.
            species_expected_ratio (Dict[str, Dict[str, float]]): Expected log2 ratios for species.

        Returns:
            pd.DataFrame: DataFrame with epsilon values and species assignments.
        """
        # Compute unique species occurrences
        withspecies["unique"] = withspecies[species_expected_ratio.keys()].sum(axis=1)

        # Filter for unique species rows
        withspecies_unique = withspecies[withspecies["unique"] == 1].copy()

        # Assign species and expected ratios
        for species in species_expected_ratio.keys():
            withspecies_unique.loc[withspecies_unique[species], "species"] = species
            withspecies_unique.loc[withspecies_unique[species], "log2_expectedRatio"] = np.log2(
                species_expected_ratio[species]["A_vs_B"]
            )

        # Compute epsilon as the difference between observed and expected log2 ratios
        withspecies_unique["epsilon"] = withspecies_unique["log2_A_vs_B"] - withspecies_unique["log2_expectedRatio"]
        return withspecies_unique
