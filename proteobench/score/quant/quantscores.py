from typing import Dict

import numpy as np
import pandas as pd


class QuantScores:
    def __init__(self, precursor_name: str, species_expected_ratio, species_dict: Dict[str, str]):
        self.precursor_name = precursor_name
        self.species_expected_ratio = species_expected_ratio
        self.species_dict = species_dict

    def generate_intermediate(
        self,
        filtered_df: pd.DataFrame,
        replicate_to_raw: dict,
    ) -> pd.DataFrame:
        # select columns which are relavant for the statistics
        # TODO, this should be handled different, probably in the parse settings
        relevant_columns_df = filtered_df[["Raw file", self.precursor_name, "Intensity"]].copy()
        replicate_to_raw_df = QuantScores.convert_replicate_to_raw(replicate_to_raw)

        # add column "Group" to filtered_df_p1 using inner join on "Raw file"
        relevant_columns_df = pd.merge(relevant_columns_df, replicate_to_raw_df, on="Raw file", how="inner")
        quant_df = QuantScores.compute_group_stats(
            relevant_columns_df,
            min_intensity=0,
            precursor=self.precursor_name,
        )

        species_prec_ion = list(self.species_dict.values())
        species_prec_ion.append(self.precursor_name)
        prec_ion_to_species = filtered_df[species_prec_ion].drop_duplicates()
        # merge dataframes quant_df and species_quant_df and prec_ion_to_species using pepdidoform as index
        quant_df_withspecies = pd.merge(quant_df, prec_ion_to_species, on=self.precursor_name, how="inner")
        species_expected_ratio = self.species_expected_ratio
        res = QuantScores.compute_epsilon(quant_df_withspecies, species_expected_ratio)
        return res

    @staticmethod
    def convert_replicate_to_raw(replicate_to_raw: dict) -> pd.DataFrame:
        """Converts replicate_to_raw dictionary into a dataframe."""
        replicate_to_raw_df = pd.DataFrame(replicate_to_raw.items(), columns=["Group", "Raw file"])
        replicate_to_raw_df = replicate_to_raw_df.explode("Raw file")
        return replicate_to_raw_df

    @staticmethod
    def compute_group_stats(
        relevant_columns_df: pd.DataFrame,
        min_intensity=0,
        precursor="precursor ion",
    ) -> pd.DataFrame:
        """Method used to precursor statistics, such as number of observations, CV, mean per group etc."""

        # fiter for min_intensity
        relevant_columns_df = relevant_columns_df[relevant_columns_df["Intensity"] > min_intensity]

        # TODO: check if this is still needed
        # sum intensity values of the same precursor and "Raw file" using the sum
        quant_raw_df_int = (
            relevant_columns_df.groupby([precursor, "Raw file", "Group"])["Intensity"]
            .agg(Intensity="sum", Count="size")
            .reset_index()
        )

        # add column "log_Intensity" to quant_raw_df
        quant_raw_df_int["log_Intensity"] = np.log2(quant_raw_df_int["Intensity"])

        # compute the mean of the log_Intensity per precursor and "Group"
        quant_raw_df_count = (quant_raw_df_int.groupby([precursor])).agg(nr_observed=("Raw file", "size"))

        # pivot filtered_df_p1 to wide where index peptide ion, columns Raw file and values Intensity

        intensities_wide = quant_raw_df_int.pivot(index=precursor, columns="Raw file", values="Intensity").reset_index()

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

        # compute coefficient of variation (CV) of the log_Intensity_mean and log_Intensity_std
        quant_raw_df["CV"] = quant_raw_df["Intensity_std"] / quant_raw_df["Intensity_mean"]
        # pivot dataframe wider so for each Group variable there is a column with log_Intensity_mean, log_Intensity_std, Intensity_mean, Intensity_std and CV
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

        quant_raw_df["log2_A_vs_B"] = quant_raw_df["log_Intensity_mean_A"] - quant_raw_df["log_Intensity_mean_B"]

        quant_raw_df = pd.merge(quant_raw_df, intensities_wide, on=precursor, how="inner")
        quant_raw_df = pd.merge(quant_raw_df, quant_raw_df_count, on=precursor, how="inner")
        return quant_raw_df

    @staticmethod
    def compute_epsilon(withspecies, species_expected_ratio):
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
        return withspecies_unique
