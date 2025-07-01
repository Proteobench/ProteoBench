"""All formats available for the module."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from typing import Any, Dict, List

import pandas as pd
import toml
from psm_utils import Peptidoform
import numpy as np

from .parse_ion import get_proforma_bracketed

# IMPORTANT: it is defined here, but filled in after defining the classes
# new classes need to be filled in there too!!!
MODULE_TO_CLASS = {}


class ParseSettingsBuilder:
    """
    Class to build the parser settings for a given input format.

    Parameters
    ----------
    parse_settings_dir : str
        The directory containing the parse settings files, by default None.
    module_id : str
        The ID of the module used to fetch the specific parse settings.
    """

    def __init__(self, parse_settings_dir: str, module_id: str):
        """
        Initialize the ParseSettingsBuilder object.

        Parameters
        ----------
        parse_settings_dir : str
            The directory containing the parse settings files.
        module_id : str
            The ID of the module used to fetch the specific parse settings.
        """

        self.PARSE_SETTINGS_TOMLS = toml.load(
            os.path.join(os.path.dirname(__file__), "io_parse_settings", "parse_settings_files.toml")
        )

        try:
            self.PARSE_SETTINGS_FILES = {
                key: os.path.join(parse_settings_dir, value)
                for key, value in self.PARSE_SETTINGS_TOMLS[module_id].items()
            }
        except KeyError:
            raise KeyError(
                f"Invalid module ID: {module_id}. Valid modules with configured parse settings are: {self.PARSE_SETTINGS_TOMLS.keys()}"
            )

        self.PARSE_SETTINGS_FILES_MODULE = os.path.join(parse_settings_dir, "module_settings.toml")
        self.INPUT_FORMATS = list(self.PARSE_SETTINGS_FILES.keys())
        self.MODULE_ID = module_id

        # Check if all files are present
        missing_files = [file for file in self.PARSE_SETTINGS_FILES.values() if not os.path.isfile(file)]
        if not os.path.isfile(self.PARSE_SETTINGS_FILES_MODULE):
            missing_files.append(self.PARSE_SETTINGS_FILES_MODULE)

        if missing_files:
            raise FileNotFoundError(f"The following parse settings files are missing: {missing_files}")

    def build_parser(self, input_format: str) -> object:
        """
        Build the parser for a given input format using the corresponding TOML files.

        Parameters
        ----------
        input_format : str
            The input format to build the parser for (e.g., "MaxQuant", "Sage").

        Returns
        -------
        ParseSettings
            The parser for the specified input format.
        """
        toml_file = self.PARSE_SETTINGS_FILES[input_format]
        parse_settings = toml.load(toml_file)
        parse_settings_module = toml.load(self.PARSE_SETTINGS_FILES_MODULE)

        parser = MODULE_TO_CLASS[self.MODULE_ID](parse_settings, parse_settings_module)
        if "modifications_parser" in parse_settings.keys():
            parser.add_modification_parser(ParseModificationSettings(parse_settings))

        return parser


class ParseSettingsQuant:
    """
    Structure that contains all the parameters used to parse
    the given benchmark run output depending on the software tool used.

    Parameters
    ----------
    parse_settings : Dict[str, Any]
        The settings for parsing, typically loaded from a TOML file.
    parse_settings_module : Dict[str, Any]
        Module-specific settings, typically loaded from a TOML file.
    """

    def __init__(self, parse_settings: Dict[str, Any], parse_settings_module: Dict[str, Any]):
        """
        Initialize the ParseSettings object with the parameters from the TOML files.

        Parameters
        ----------
        parse_settings : Dict[str, Any]
            The settings for parsing, typically loaded from a TOML file.
        parse_settings_module : Dict[str, Any]
            Module-specific settings, typically loaded from a TOML file.
        """
        self.mapper = parse_settings["mapper"]
        self.condition_mapper = parse_settings["condition_mapper"]
        self.run_mapper = parse_settings["run_mapper"]
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self._species_dict = parse_settings["species_mapper"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]
        self.min_count_multispec = parse_settings_module["general"]["min_count_multispec"]
        self.analysis_level = parse_settings_module["general"]["level"]
        self._species_expected_ratio = parse_settings_module["species_expected_ratio"]
        self.modification_parser = None

    def species_dict(self) -> Dict[str, str]:
        """
        Get the species dictionary.

        Returns
        -------
        Dict[str, str]
            A dictionary of species mappings.
        """
        return self._species_dict

    def species_expected_ratio(self) -> float:
        """
        Get the expected species ratio.

        Returns
        -------
        float
            The expected ratio of species.
        """
        return self._species_expected_ratio

    def add_modification_parser(self, parser: ParseModificationSettings):
        """
        Add a modification parser to the settings.

        Parameters
        ----------
        parser : object
            The modification parser to add.
        """
        self.modification_parser = parser

    def _filter_decoys(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out decoy proteins from the DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing protein data.

        Returns
        -------
        pd.DataFrame
            DataFrame with decoy proteins removed.
        """
        if "Reverse" in self.mapper:
            df_filtered = df[df["Reverse"] != self.decoy_flag].copy()
        else:
            df_filtered = df.copy()
        return df_filtered

    def _fix_colnames(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fix column names in the DataFrame according to the mapper.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame with original column names.

        Returns
        -------
        pd.DataFrame
            DataFrame with standardized column names.
        """
        df.columns = [c.replace(".mzML.gz", ".mzML") for c in df.columns]
        return df

    def _mark_contaminants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Mark contaminant proteins in the DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing protein data.

        Returns
        -------
        pd.DataFrame
            DataFrame with marked contaminants.
        """
        df["contaminant"] = df["Proteins"].str.contains(self.contaminant_flag)
        return df

    def _process_species_information(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate species information from the DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing protein data.

        Returns
        -------
        pd.DataFrame
            DataFrame with processed species information.
        """
        # Process species flags
        for flag, species in self._species_dict.items():
            df[species] = df["Proteins"].str.contains(flag)

        # Filter multi-species
        df["MULTI_SPEC"] = df[list(self._species_dict.values())].sum(axis=1) > self.min_count_multispec
        return df[df["MULTI_SPEC"] == False]

    def _validate_and_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and rename columns according to the mapper.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame with original column names.

        Returns
        -------
        pd.DataFrame
            DataFrame with validated and renamed columns.
        """
        if not all(k in df.columns for k in self.mapper.keys()):
            raise ValueError(
                f"Columns {set(self.mapper.keys()).difference(set(df.columns))} not found in input dataframe."
                " Please check input file and selected software tool."
            )
        df.rename(columns=self.mapper, inplace=True)
        return df

    def _create_replicate_mapping(self) -> Dict[int, List[str]]:
        """
        Create replicate mapping for the DataFrame.

        Returns
        -------
        Dict[int, List[str]]
            A dictionary mapping replicates to raw data.
        """
        replicate_to_raw = defaultdict(list)
        for k, v in self.condition_mapper.items():
            replicate_to_raw[v].append(k)
        return replicate_to_raw

    def _handle_data_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle different data formats and convert to standard format.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame in either long or short format.

        Returns
        -------
        pd.DataFrame
            DataFrame converted to standard format.
        """
        if "Raw file" not in self.mapper.values():
            melt_vars = self.condition_mapper.keys()
            df_melted = df.melt(
                id_vars=list(set(df.columns).difference(set(melt_vars))),
                value_vars=melt_vars,
                var_name="Raw file",
                value_name="Intensity",
            )
        else:
            df_melted = df.copy()

        df_melted["replicate"] = df_melted["Raw file"].map(self.condition_mapper)
        return pd.concat([df_melted, pd.get_dummies(df_melted["Raw file"])], axis=1)

    def _process_modifications(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate modified sequences using the modification parser.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing modification data.

        Returns
        -------
        pd.DataFrame
            DataFrame with processed modifications.
        """
        if self.modification_parser is not None:
            return self.modification_parser.convert_to_proforma(df, self.analysis_level)
        return df

    def _filter_zero_intensities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out rows with zero or negative intensities.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing intensity data.

        Returns
        -------
        pd.DataFrame
            DataFrame with zero/negative intensities removed.
        """
        zero_intensity_count = len(df[df["Intensity"] <= 0])
        if zero_intensity_count > 0:
            print(f"WARNING: {zero_intensity_count} rows with 0 intensity were removed.")
        return df[df["Intensity"] > 0]

    def _format_by_analysis_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format DataFrame according to the analysis level.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame to be formatted.

        Returns
        -------
        pd.DataFrame
            Formatted DataFrame according to analysis level.
        """
        if self.analysis_level == "ion":
            if "proforma" in df.columns and "Charge" in df.columns:
                df["precursor ion"] = df["proforma"] + "|Z=" + df["Charge"].astype(str)
            return df
        elif self.analysis_level == "peptidoform":
            if "proforma" in df.columns:
                df["peptidoform"] = df["proforma"]
            return df
        else:
            raise ValueError(f"Analysis level '{self.analysis_level}' not supported.")

    def convert_to_standard_format(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """
        Convert a software tool output into a generic format supported by the module.

        Steps:
        1. Validate and rename columns
        2. Create replicate mapping
        3. Filter decoys
        4. Fix column names
        5. Mark contaminants
        6. Process species information
        7. Handle data format (long vs short)
        8. Process modifications if needed
        9. Filter zero intensities
        10. Format based on analysis level

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame to convert.

        Returns
        -------
        tuple[pd.DataFrame, Dict[int, List[str]]]
            The converted DataFrame and a dictionary mapping replicates to raw data.
        """
        df = self._validate_and_rename_columns(df)
        replicate_to_raw = self._create_replicate_mapping()
        df = self._filter_decoys(df)
        df = self._fix_colnames(df)
        df = self._mark_contaminants(df)
        df = self._process_species_information(df)
        df = self._process_modifications(df)
        df_melted = self._handle_data_format(df)
        df_melted = self._filter_zero_intensities(df_melted)
        return self._format_by_analysis_level(df_melted), replicate_to_raw


class ParseModificationSettings:
    """
    Settings for parsing modifications in protein data.

    Parameters
    ----------
    parse_settings : Dict[str, Any]
        Dictionary containing modification-specific parsing settings.
    """

    def __init__(self, parse_settings: Dict[str, Any]):
        """
        Initialize ParseModificationSettings.

        Parameters
        ----------
        parse_settings : Dict[str, Any]
            Dictionary containing modification-specific parsing settings.
        """
        self.modifications_mapper = parse_settings["modifications_parser"]["modification_dict"]
        self.modifications_isalpha = parse_settings["modifications_parser"]["isalpha"]
        self.modifications_isupper = parse_settings["modifications_parser"]["isupper"]
        self.modifications_before_aa = parse_settings["modifications_parser"]["before_aa"]
        self.modifications_pattern = parse_settings["modifications_parser"]["pattern"]
        self.modifications_pattern = rf"{self.modifications_pattern}"
        self.modifications_parse_column = parse_settings["modifications_parser"]["parse_column"]

    def convert_to_proforma(self, df: pd.DataFrame, analysis_level: str) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """
        Convert modifications to ProForma format.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing modification data.
        analysis_level : str
            The level of analysis to perform.

        Returns
        -------
        tuple[pd.DataFrame, Dict[int, List[str]]]
            The converted DataFrame and a dictionary mapping replicates to raw data.
        """
        df["proforma"] = df[self.modifications_parse_column].apply(
            get_proforma_bracketed,
            before_aa=self.modifications_before_aa,
            isalpha=self.modifications_isalpha,
            isupper=self.modifications_isupper,
            pattern=self.modifications_pattern,
            modification_dict=self.modifications_mapper,
        )

        if analysis_level == "ion":
            try:
                df["precursor ion"] = df["proforma"] + "|Z=" + df["Charge"].astype(str)
            except KeyError as e:
                raise KeyError(
                    "Not all columns required for making the precursor ion are available."
                    " Is the charge available in the input file?"
                ) from e

            return df

        elif analysis_level == "peptidoform":
            if "proforma" in df.columns:
                df["peptidoform"] = df["proforma"]
            return df


class ParseSettingsDeNovo:
    def __init__(self, parse_settings: Dict[str, Any], parse_settings_module: Dict[str, Any]):
        self.mapper = parse_settings["mapper"]
        self.spectrum_id_mapper = parse_settings["spectrum_id_mapper"]
        self.sequence_mapper = parse_settings["sequence_mapper"]
        self.modification_parser = None
        self.analysis_level = "peptidoform"

        module_settings_dir = os.path.join(
            os.path.dirname(__file__),
            "io_parse_settings",
            "denovo",
            "lfq",
            "DDA",
            "HCD",
        )
        self.path_to_ground_truth = os.path.join(
            module_settings_dir, parse_settings_module["ground_truth"]["path_to_ground_truth"]
        )

    def extract_scan_id(self, spectrum_id: str) -> int:
        """
        Extract the scan ID from the spectrum ID string.

        Parameters
        ----------
        spectrum_id : str
            The input spectrum ID string.

        Returns
        -------
        int
            The extracted scan ID (a number).
        """
        scan_id_match = re.search(self.spectrum_id_mapper["pattern"], spectrum_id)
        if scan_id_match is None:
            raise ValueError(
                f"Scan id not found in the spectrum_id string {spectrum_id}."
                f" Spectrum id pattern is {self.spectrum_id_mapper['pattern']}."
            )

        scan_id = scan_id_match.group(1)
        return int(scan_id)

    def format_sequence(self, sequence: str) -> str:
        """
        Format the sequence string.

        Parameters
        ----------
        sequence : str
            The input sequence string.

        Returns
        -------
        str
            The formatted sequence string.
        """
        if not isinstance(sequence, str):
            return ""

        if "replacement_dict" in self.sequence_mapper:
            for key, value in self.sequence_mapper["replacement_dict"].items():
                sequence = sequence.replace(key, value)
        return sequence

    def format_scores(self, aa_scores: Any, peptidoform: Peptidoform, fix_aa_length=False) -> List[float]:
        """
        Format the amino acid scores into a list of float numbers.

        Parameters
        ----------
        aa_scores : List[float]
            The input list of scores.

        Returns
        -------
        List[float]
            The formatted list of scores.
        """
        # Fix aa_score length as this modification is collapsed from 2 tokens to 1
        if (
            fix_aa_length and
            isinstance(peptidoform.properties['n_term'], list) and
            peptidoform.properties['n_term'][0].value == 'H-2C1O1'
        ):
            aa_scores = list(np.mean(aa_scores[0:2])) + aa_scores[2:]

        if isinstance(aa_scores, list) and all(isinstance(i, float) for i in aa_scores):
            return aa_scores

        if isinstance(aa_scores, str):
            aa_scores = eval(aa_scores)
            # aa_scores = aa_scores.split(",")  # TODO: make it cofigurable separator?
            # aa_scores = [float(score) for score in aa_scores]
        return aa_scores

    def add_modification_parser(self, parser: ParseModificationSettings):
        self.modification_parser = parser

    def get_length_peptidoform_with_nterm(self, peptidoform: Peptidoform):
        if peptidoform.properties['n_term'] is None:
            return len(peptidoform)
        return len(peptidoform) + len(peptidoform.properties['n_term'])

    def add_features(self, df: pd.DataFrame):
        columns_to_keep_gt = [
            "spectrum_id",
            "peptidoform",
            "peptidoform_ground_truth",
            "proforma",
            "precursor_mz",
            "retention_time",
            "title",
            "score",
            "aa_scores",
            ### FEATURES
            # 1. MFR
            "missing_frag_sites",
            "missing_frag_pct",
            # 2. Explained intensity
            "explained_y_pct",
            "explained_b_pct",
            "explained_by_pct",
            "explained_all_pct",
            # 3. peptide length
            "peptide_length",
            # 4. cosine similarity with MS2PIP
            "cos",
            "cos_ionb",
            "cos_iony",
            "spec_pearson",
            "dotprod",
            ### PTM-features
            # GT
            "M-Oxidation",
            "Q-Deamidation",
            "N-Deamidation",
            "N-term Acetylation",
            "N-term Carbamylation",
            "N-term Ammonia-loss",
            # Predicted
            "M-Oxidation (denovo)",
            "Q-Deamidation (denovo)",
            "N-Deamidation (denovo)",
            "N-term Acetylation (denovo)",
            "N-term Carbamylation (denovo)",
            "N-term Ammonia-loss (denovo)",
            ### SPECIES
            'collection',
        ]
        
        # PTM-features
        df['M-Oxidation'] = df.peptidoform_ground_truth.apply(lambda x: "M[UNIMOD:35]" in x)
        df['Q-Deamidation'] = df.peptidoform_ground_truth.apply(lambda x: "Q[UNIMOD:7]" in x)
        df['N-Deamidation'] = df.peptidoform_ground_truth.apply(lambda x: "N[UNIMOD:7]" in x)
        df['N-term Acetylation'] = df.peptidoform_ground_truth.apply(lambda x: "[UNIMOD:1]-" in x)
        df['N-term Carbamylation'] = df.peptidoform_ground_truth.apply(lambda x: "[UNIMOD:385]-" in x)
        df['N-term Ammonia-loss'] = df.peptidoform_ground_truth.apply(lambda x: "[UNIMOD:5]-" in x)

        df['M-Oxidation (denovo)'] = df.peptidoform.apply(lambda x: "M[UNIMOD:35]" in x.modified_sequence if isinstance(x, Peptidoform) else None)
        df['Q-Deamidation (denovo)'] = df.peptidoform.apply(lambda x: "Q[UNIMOD:7]" in x.modified_sequence if isinstance(x, Peptidoform) else None)
        df['N-Deamidation (denovo)'] = df.peptidoform.apply(lambda x: "N[UNIMOD:7]" in x.modified_sequence if isinstance(x, Peptidoform) else None)
        df['N-term Acetylation (denovo)'] = df.peptidoform.apply(lambda x: "[UNIMOD:1]-" in x.modified_sequence if isinstance(x, Peptidoform) else None)
        df['N-term Carbamylation (denovo)'] = df.peptidoform.apply(lambda x: "[UNIMOD:385]-" in x.modified_sequence if isinstance(x, Peptidoform) else None)
        df['N-term Ammonia-loss (denovo)'] = df.peptidoform.apply(lambda x: "[UNIMOD:5]-" in x.modified_sequence if isinstance(x, Peptidoform) else None)

        df['peptidoform_ground_truth'] = df.peptidoform_ground_truth.apply(lambda x: Peptidoform(Peptidoform(x).modified_sequence)) # Removing precursor charge from peptidoform
        
        # Peptide length
        df['peptide_length'] = df.peptidoform_ground_truth.apply(lambda x: self.get_length_peptidoform_with_nterm(x))

        return df[columns_to_keep_gt]

    def convert_to_standard_format(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[int, List[str]]]:
        """
        Convert a software tool output into a generic format supported by the module.

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame to convert.

        Returns
        -------
        tuple[pd.DataFrame, Dict[int, List[str]]]
            The converted DataFrame and a dictionary mapping replicates to raw data.
        """
        # TODO: Add functionality/steps in docstring.
        if not all(k in df.columns for k in self.mapper.keys()):
            raise ValueError(
                f"Columns {set(self.mapper.keys()).difference(set(df.columns))} not found in input dataframe."
                " Please check input file and selected de novo tool."
            )

        df = df.rename(columns=self.mapper, inplace=False)

        if self.spectrum_id_mapper:
            df["spectrum_id"] = df["spectrum_id"].apply(self.extract_scan_id)

        if self.sequence_mapper:
            df["sequence"] = df["sequence"].apply(self.format_sequence)

        if self.modification_parser is not None:
            df = self.modification_parser.convert_to_proforma(df, self.analysis_level)
        else:
            df["proforma"] = df["sequence"]


        def convert_to_peptidoform(proforma):
            try:
                return Peptidoform(proforma)
            except:
                return None
        if "proforma" in df.columns:
            df["peptidoform"] = df["proforma"].apply(lambda x: convert_to_peptidoform(x))
            df = df.dropna(subset='peptidoform')

        # If AA scores are not provided, simulate them from peptide score
        if "aa_scores" not in df.columns:
            df["aa_scores"] = df.apply(
                lambda row: [row["score"]] * self.get_length_peptidoform_with_nterm(row["peptidoform"]),
                axis=1
            )
        
        df["aa_scores"] = df.apply(
            lambda x: self.format_scores(x['aa_scores'], x['peptidoform']),
            axis=1
        )

        columns_to_keep = ["spectrum_id", "proforma", "peptidoform", "score", "aa_scores"]
        df = df[columns_to_keep]

        # Load ground truth PSMs

        df_ground_truth = pd.read_csv(self.path_to_ground_truth)

        df = pd.merge(df_ground_truth, df, on=["spectrum_id"], how="left", suffixes=("_ground_truth", ""))
        df = self.add_features(df=df)

        return df


MODULE_TO_CLASS = {
    "quant_lfq_DDA_ion_QExactive": ParseSettingsQuant,
    "quant_lfq_DDA_peptidoform": ParseSettingsQuant,
    "quant_lfq_DIA_ion_AIF": ParseSettingsQuant,
    "quant_lfq_DIA_ion_diaPASEF": ParseSettingsQuant,
    "quant_lfq_DIA_ion_singlecell": ParseSettingsQuant,
    "quant_lfq_DIA_ion_Astral": ParseSettingsQuant,
    "denovo_lfq_DDA_HCD": ParseSettingsDeNovo,
}
