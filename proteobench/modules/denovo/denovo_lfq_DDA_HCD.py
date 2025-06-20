"""
De Novo Module DDA-HCD spectra.
"""

from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.denovo_datapoint import DenovoDatapoint
from proteobench.exceptions import (
    ConvertStandardFormatError,
    IntermediateFormatGenerationError,
    ParseError,
    ParseSettingsError,
    QuantificationError,
)
from proteobench.io.parsing.parse_denovo import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.denovo.denovo_base import DeNovoModule
from proteobench.score.denovo.denovoscores import DenovoScores


class DDAHCDDeNovoModule(DeNovoModule):
    """
    De Novo Module.
    """

    module_id = "denovo_lfq_DDA_HCD"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_denovo_lfq_DDA_HCD",
        proteobench_repo_name: str = "Proteobench/Results_denovo_lfq_DDA_HCD",
    ):
        """
        Initialize the DDA Quantification Module for Ion level Quantification.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DDA".
        proteobench_repo_name : str, optional
            Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DDA".
        """

        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=MODULE_SETTINGS_DIRS[self.module_id],
            module_id=self.module_id,
        )

    def is_implemented(self) -> bool:
        """
        Return whether the module is fully implemented.

        Returns
        -------
        bool
            Always returns True in this implementation.
        """
        return False

    def benchmarking(
        self,
        input_file_loc: any,
        input_format: str,
        user_input: dict,
        all_datapoints: pd.DataFrame,
        level: str = "peptide",
        evaluation_type: str = "mass",
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """
        Main workflow of the module. Used to benchmark workflow results.

        Parameters
        ----------
        input_file_loc : any
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        user_input : dict
            User provided parameters for plotting.
        all_datapoints : pd.DataFrame
            DataFrame containing all datapoints from the proteobench repo.
        level : str
            The level precision and recall is calculated. Either `peptide` or `aa`
        evaluation_type : str
            The evaluation type for precision calculation. Either `exact` or `mass`-based

        Returns
        -------
        tuple[DataFrame, DataFrame, DataFrame]
            Tuple containing the intermediate data structure, all datapoints, and the input DataFrame.
        """
        # Parse workflow output file
        try:
            input_df = load_input_file(input_file_loc, input_format)
        except pd.errors.ParserError as e:
            raise ParseError(
                f"Error parsing {input_format} file, please make sure the format is correct and the correct software tool is chosen: {e}"
            ) from e
        except Exception as e:
            raise ParseSettingsError("Error parsing the input file.") from e

        msg = f"Folder: {self.parse_settings_dir}, Module: {self.module_id}"

        # Parse settings file
        try:
            parse_settings = ParseSettingsBuilder(
                parse_settings_dir=self.parse_settings_dir, module_id=self.module_id
            ).build_parser(input_format)
        except KeyError as e:
            raise ParseSettingsError(
                f"Error parsing settings file for parsing, settings seem to be missing: {msg}"
            ) from e
        except FileNotFoundError as e:
            raise ParseSettingsError(f"Could not find the parsing settings file: {msg}") from e
        except Exception as e:
            raise ParseSettingsError(f"Error parsing settings file for parsing: {msg}") from e

        try:
            standard_format = parse_settings.convert_to_standard_format(input_df)
        except KeyError as e:
            raise ConvertStandardFormatError("Error converting to standard format, key missing.") from e
        except Exception as e:
            raise ConvertStandardFormatError("Error converting to standard format.") from e

        # Instantiate de novo scores
        denovo_score = DenovoScores()

        # generate intermediate data structure (Calculate the scores)
        try:
            intermediate_metric_structure = denovo_score.generate_intermediate(
                standard_format
            )
        except Exception as e:
            raise IntermediateFormatGenerationError("Error generating intermediate data structure.") from e

        # try:
        current_datapoint = DenovoDatapoint.generate_datapoint(
            intermediate=intermediate_metric_structure,
            input_format=input_format,
            user_input=user_input,
            level=level,
            evaluation_type=evaluation_type
        )
        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=all_datapoints)

        return (
            intermediate_metric_structure,
            all_datapoints,
            input_df,
        )
