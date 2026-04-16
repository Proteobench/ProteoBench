"""
Converters that transform raw vendor DataFrames into the intermediate format.

Contains IntermediateFormatConverter (quant), ModificationConverter, ConverterBuilder,
and ParseSettingsDeNovo (de novo). The ConverterBuilder reads per-tool TOML configs
and instantiates the appropriate converter.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import toml
from psm_utils import Peptidoform

from .proforma import get_proforma_bracketed

# IMPORTANT: it is defined here, but filled in after defining the classes
# new classes need to be filled in there too!!!
MODULE_TO_CLASS = {}
GROUND_TRUTH_DIR_SERVER = "/mnt/data/proteobench/module_data/"

GROUND_TRUTH_DIR_LOCAL_DENOVO = os.path.join(
    Path(__file__).resolve().parent,
    "io_parse_settings",
    "denovo",
    "DDA",
    "HCD",
)

GROUND_TRUTH_FILENAME = "De_Novo_module_ground_truth.csv.gz"
GROUND_TRUTH_URL = "https://proteobench.cubimed.rub.de/datasets/module_data/De_Novo_module_ground_truth.csv.gz"


class ConverterBuilder:
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
        Initialize the ConverterBuilder object.

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
        IntermediateFormatConverter
            The parser for the specified input format.
        """
        toml_file = self.PARSE_SETTINGS_FILES[input_format]
        parse_settings = toml.load(toml_file)
        parse_settings_module = toml.load(self.PARSE_SETTINGS_FILES_MODULE)

        parser = MODULE_TO_CLASS[self.MODULE_ID](parse_settings, parse_settings_module)
        if "modifications_parser" in parse_settings.keys():
            parser.add_modification_parser(ModificationConverter(parse_settings))

        return parser


class IntermediateFormatConverter:
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
        Initialize the converter with parameters from the TOML files.

        The condition_mapper is resolved in this order:
        1. Per-tool TOML ``[condition_mapper]`` (if present — wide-format tools need this)
        2. Module-level ``[[samples]]`` from module_settings.toml (long-format tools)

        Parameters
        ----------
        parse_settings : Dict[str, Any]
            The settings for parsing, typically loaded from a TOML file.
        parse_settings_module : Dict[str, Any]
            Module-specific settings, typically loaded from a TOML file.
        """
        self.mapper = parse_settings["mapper"]
        if "condition_mapper" in parse_settings:
            self.condition_mapper = parse_settings["condition_mapper"]
        elif "samples" in parse_settings_module:
            self.condition_mapper = {s["raw_file"]: s["condition"] for s in parse_settings_module["samples"]}
        else:
            raise ValueError("No condition_mapper found in per-tool TOML or [[samples]] in module_settings.toml")
        self.decoy_flag = parse_settings["general"]["decoy_flag"]
        self.contaminant_flag = parse_settings["general"]["contaminant_flag"]
        self.analysis_level = parse_settings_module["general"]["level"]
        self.modification_parser = None

        # Regex pattern for cleaning run names (strips extensions, suffixes, paths)
        # Can be overridden per-tool in the TOML [general] section
        cleanup_pattern = parse_settings["general"].get("run_name_cleanup", "")
        if cleanup_pattern:
            try:
                self._run_name_cleanup = re.compile(cleanup_pattern)
            except re.error as exc:
                raise ValueError(
                    f"Invalid regex in [general].run_name_cleanup: {cleanup_pattern!r}. "
                    f"Please fix the pattern in the TOML configuration. Details: {exc}"
                ) from exc
        else:
            # Default: strip common MS file extensions and known suffixes
            self._run_name_cleanup = re.compile(r"(?:\.mzML\.gz|\.mzML|\.raw|\.RAW|\.d|\.wiff|_uncalibrated)$")

        # Normalize the condition_mapper keys using the same cleanup
        # so that keys like "file.mzML" and column names like "file.mzML" both
        # resolve to "file" after cleaning (see #827, #876)
        self.condition_mapper = {self._clean_run_name(k): v for k, v in self.condition_mapper.items()}

    def add_modification_parser(self, parser: ModificationConverter):
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

    def _clean_run_name(self, name: str) -> str:
        """
        Clean a run/file name by removing extensions and known suffixes.

        Strips path prefixes (e.g., ``/path/to/file.mzML`` -> ``file``)
        and applies the run_name_cleanup regex to remove extensions like
        ``.raw``, ``.mzML``, ``.mzML.gz``, ``.d``, ``.wiff``, and
        tool-specific suffixes like ``_uncalibrated`` (FragPipe DIA-NN, see #827).

        Parameters
        ----------
        name : str
            The raw file name or column name to clean.

        Returns
        -------
        str
            The cleaned name.
        """
        if not isinstance(name, str):
            return name
        # Strip path prefix (some tools include full paths)
        name = name.replace("\\", "/")
        if "/" in name:
            name = name.rsplit("/", 1)[-1]
        # Apply the cleanup regex
        name = self._run_name_cleanup.sub("", name)
        return name

    def _fix_colnames(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fix column names in the DataFrame by cleaning run names.

        Applies run name cleanup (extension stripping, path removal) to all
        column names so they match the keys in condition_mapper.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame with original column names.

        Returns
        -------
        pd.DataFrame
            DataFrame with standardized column names.
        """
        df.columns = [self._clean_run_name(c) for c in df.columns]
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
        df_no_contaminants = df[df["contaminant"] == False].copy()
        return df_no_contaminants

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

    def create_replicate_mapping(self) -> Dict[int, List[str]]:
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
        # If "Raw file" is in mapper values, data is already in long format - skip melting
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

        # Clean run names in the "Raw file" column (strip extensions, paths, suffixes)
        # so they match the condition_mapper keys (see #827, #876)
        df_melted["Raw file"] = df_melted["Raw file"].apply(self._clean_run_name)

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
                df["precursor ion"] = df["proforma"] + "/" + df["Charge"].astype(str)
            return df
        elif self.analysis_level == "peptidoform":
            if "proforma" in df.columns:
                df["peptidoform"] = df["proforma"]
            return df
        else:
            raise ValueError(f"Analysis level '{self.analysis_level}' not supported.")

    def convert_to_standard_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert a software tool output into a generic format supported by the module.

        Steps:
        1. Validate and rename columns
        2. Fix column names (clean run names)
        3. Handle data format (melt wide to long if needed)
        4. Filter decoys
        5. Mark contaminants
        6. Process modifications if needed
        7. Filter zero intensities
        8. Format based on analysis level

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame to convert.

        Returns
        -------
        pd.DataFrame
            The converted DataFrame in standard format.
        """
        df = self._validate_and_rename_columns(df)
        df = self._fix_colnames(df)
        df = self._handle_data_format(df)
        df = self._filter_decoys(df)
        df = self._mark_contaminants(df)
        df = self._process_modifications(df)
        df = self._filter_zero_intensities(df)
        return self._format_by_analysis_level(df)


class ModificationConverter:
    """
    Settings for parsing modifications in protein data.

    Parameters
    ----------
    parse_settings : Dict[str, Any]
        Dictionary containing modification-specific parsing settings.
    """

    def __init__(self, parse_settings: Dict[str, Any]):
        """
        Initialize ModificationConverter.

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
                df["precursor ion"] = df["proforma"] + "/" + df["Charge"].astype(str)
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
    """
    Parse settings and converter for de novo sequencing tool outputs.

    Parameters
    ----------
    parse_settings : Dict[str, Any]
        Tool-specific settings loaded from TOML.
    parse_settings_module : Dict[str, Any]
        Module-level settings loaded from TOML.
    """

    def __init__(self, parse_settings: Dict[str, Any], parse_settings_module: Dict[str, Any]):  # numpydoc ignore=PR01
        """Initialize with tool-specific and module-level settings."""
        self.mapper = parse_settings["mapper"]
        self.spectrum_id_mapper = parse_settings["spectrum_id_mapper"]
        self.sequence_mapper = parse_settings["sequence_mapper"]
        self.modification_parser = None
        self.analysis_level = "peptidoform"

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

    def format_scores(self, aa_scores: Any, peptidoform: Peptidoform, fix_aa_length: bool = False) -> List[float]:
        """
        Format the amino acid scores into a list of float numbers.

        Parameters
        ----------
        aa_scores : Any
            The input list of scores.
        peptidoform : Peptidoform
            The peptidoform object for length correction.
        fix_aa_length : bool, optional
            Whether to fix AA score length for collapsed N-term modifications.

        Returns
        -------
        List[float]
            The formatted list of scores.
        """
        # Fix aa_score length as this modification is collapsed from 2 tokens to 1
        if (
            fix_aa_length
            and isinstance(peptidoform.properties["n_term"], list)
            and peptidoform.properties["n_term"][0].value == "H-2C1O1"
        ):
            aa_scores = list(np.mean(aa_scores[0:2])) + aa_scores[2:]

        if isinstance(aa_scores, list) and all(isinstance(i, float) for i in aa_scores):
            return aa_scores

        if isinstance(aa_scores, str):
            aa_scores = eval(aa_scores)
            # aa_scores = aa_scores.split(",")  # TODO: make it cofigurable separator?
            # aa_scores = [float(score) for score in aa_scores]
        return aa_scores

    def add_modification_parser(self, parser: ModificationConverter):
        """
        Add a modification parser to the settings.

        Parameters
        ----------
        parser : ModificationConverter
            The modification parser to add.
        """
        self.modification_parser = parser

    def get_length_peptidoform_with_nterm(self, peptidoform: Peptidoform):
        """
        Get peptidoform length including N-terminal modifications.

        Parameters
        ----------
        peptidoform : Peptidoform
            The peptidoform object.

        Returns
        -------
        int
            Length of peptidoform including N-terminal modifications.
        """
        if peptidoform.properties["n_term"] is None:
            return len(peptidoform)
        return len(peptidoform) + len(peptidoform.properties["n_term"])

    def add_features(self, df: pd.DataFrame):
        """
        Add PTM and peptide length features to the DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with peptidoform columns.

        Returns
        -------
        pd.DataFrame
            DataFrame with added feature columns.
        """
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
            "collection",
        ]

        # PTM-features
        df["M-Oxidation"] = df.peptidoform_ground_truth.apply(lambda x: "M[UNIMOD:35]" in x)
        df["Q-Deamidation"] = df.peptidoform_ground_truth.apply(lambda x: "Q[UNIMOD:7]" in x)
        df["N-Deamidation"] = df.peptidoform_ground_truth.apply(lambda x: "N[UNIMOD:7]" in x)
        df["N-term Acetylation"] = df.peptidoform_ground_truth.apply(lambda x: "[UNIMOD:1]-" in x)
        df["N-term Carbamylation"] = df.peptidoform_ground_truth.apply(lambda x: "[UNIMOD:5]-" in x)
        df["N-term Ammonia-loss"] = df.peptidoform_ground_truth.apply(lambda x: "[UNIMOD:385]-" in x)

        df["M-Oxidation (denovo)"] = df.peptidoform.apply(
            lambda x: "M[UNIMOD:35]" in x.modified_sequence if isinstance(x, Peptidoform) else None
        )
        df["Q-Deamidation (denovo)"] = df.peptidoform.apply(
            lambda x: "Q[UNIMOD:7]" in x.modified_sequence if isinstance(x, Peptidoform) else None
        )
        df["N-Deamidation (denovo)"] = df.peptidoform.apply(
            lambda x: "N[UNIMOD:7]" in x.modified_sequence if isinstance(x, Peptidoform) else None
        )
        df["N-term Acetylation (denovo)"] = df.peptidoform.apply(
            lambda x: "[UNIMOD:1]-" in x.modified_sequence if isinstance(x, Peptidoform) else None
        )
        df["N-term Carbamylation (denovo)"] = df.peptidoform.apply(
            lambda x: "[UNIMOD:5]-" in x.modified_sequence if isinstance(x, Peptidoform) else None
        )
        df["N-term Ammonia-loss (denovo)"] = df.peptidoform.apply(
            lambda x: "[UNIMOD:385]-" in x.modified_sequence if isinstance(x, Peptidoform) else None
        )

        df["peptidoform_ground_truth"] = df.peptidoform_ground_truth.apply(
            lambda x: Peptidoform(Peptidoform(x).modified_sequence)
        )  # Removing precursor charge from peptidoform

        # Peptide length
        df["peptide_length"] = df.peptidoform_ground_truth.apply(lambda x: self.get_length_peptidoform_with_nterm(x))

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

        def convert_to_peptidoform(proforma):  # numpydoc ignore=GL08
            try:
                return Peptidoform(proforma)
            except:  # noqa: E722
                return None

        if "proforma" in df.columns:
            df["peptidoform"] = df["proforma"].apply(lambda x: convert_to_peptidoform(x))
            df = df.dropna(subset="peptidoform")

        # If AA scores are not provided, simulate them from peptide score
        if "aa_scores" not in df.columns:
            df["aa_scores"] = df.apply(
                lambda row: [row["score"]] * self.get_length_peptidoform_with_nterm(row["peptidoform"]), axis=1
            )

        df["aa_scores"] = df.apply(lambda x: self.format_scores(x["aa_scores"], x["peptidoform"]), axis=1)

        columns_to_keep = ["spectrum_id", "proforma", "peptidoform", "score", "aa_scores"]
        df = df[columns_to_keep]

        # Load ground truth PSMs
        # Determine the path to the ground truth file
        if os.path.isfile(os.path.join(GROUND_TRUTH_DIR_SERVER, GROUND_TRUTH_FILENAME)):
            ground_truth_path = os.path.join(GROUND_TRUTH_DIR_SERVER, GROUND_TRUTH_FILENAME)
        elif os.path.isfile(os.path.join(GROUND_TRUTH_DIR_LOCAL_DENOVO, GROUND_TRUTH_FILENAME)):
            ground_truth_path = os.path.join(GROUND_TRUTH_DIR_LOCAL_DENOVO, GROUND_TRUTH_FILENAME)
        else:
            # Download from server URL
            from proteobench.utils.server_io import download_file

            ground_truth_path = os.path.join(GROUND_TRUTH_DIR_LOCAL_DENOVO, GROUND_TRUTH_FILENAME)
            download_file(GROUND_TRUTH_URL, ground_truth_path)

        df_ground_truth = pd.read_csv(ground_truth_path, compression="gzip")

        df = pd.merge(df_ground_truth, df, on=["spectrum_id"], how="left", suffixes=("_ground_truth", ""))
        df = self.add_features(df=df)

        return df


MODULE_TO_CLASS = {
    "quant_lfq_DDA_ion_Astral": IntermediateFormatConverter,
    "quant_lfq_DDA_ion_QExactive": IntermediateFormatConverter,
    "quant_lfq_DDA_peptidoform": IntermediateFormatConverter,
    "quant_lfq_DDA_ion_Astral": IntermediateFormatConverter,
    "quant_lfq_DIA_ion_AIF": IntermediateFormatConverter,
    "quant_lfq_DIA_ion_diaPASEF": IntermediateFormatConverter,
    "quant_lfq_DIA_ion_singlecell": IntermediateFormatConverter,
    "quant_lfq_DIA_ion_Astral": IntermediateFormatConverter,
    "denovo_DDA_HCD": ParseSettingsDeNovo,
    "quant_lfq_DIA_ion_ZenoTOF": IntermediateFormatConverter,
    "quant_lfq_DIA_ion_plasma": IntermediateFormatConverter,
}

# Deprecated aliases for backward compatibility during transition
ParseSettingsQuant = IntermediateFormatConverter
ParseModificationSettings = ModificationConverter
ParseSettingsBuilder = ConverterBuilder
