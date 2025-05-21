"""
DDA Quantification Module for precursor level Quantification.
"""

from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import QuantDatapoint
from proteobench.exceptions import (
    ConvertStandardFormatError,
    IntermediateFormatGenerationError,
    ParseError,
    ParseSettingsError,
    QuantificationError,
)
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_base_module import QuantModule
from proteobench.score.quant.quantscores import QuantScores


class DDAQuantIonModule(QuantModule):
    """
    DDA Quantification Module for precursor level Quantification.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str, optional
        Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DDA".
    proteobench_repo_name : str, optional
        Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DDA".

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    module_id = "quant_lfq_DDA_ion"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_ion_DDA",
        proteobench_repo_name: str = "Proteobench/Results_quant_ion_DDA",
    ):
        """
        Initialize the DDA Quantification Module for precursor level Quantification.

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
        self.precursor_column_name = "precursor ion"

    def is_implemented(self) -> bool:
        """
        Return whether the module is fully implemented.

        Returns
        -------
        bool
            True if the module is fully implemented, False otherwise.
        """
        return True

    def benchmarking(
        self,
        input_file_loc: any,
        input_format: str,
        user_input: dict,
        all_datapoints: pd.DataFrame,
        default_cutoff_min_prec: int = 3,
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
        default_cutoff_min_prec : int
            Minimum number of runs a precursor ion has to be identified in.

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
            standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
        except KeyError as e:
            raise ConvertStandardFormatError("Error converting to standard format, key missing.") from e
        except Exception as e:
            raise ConvertStandardFormatError("Error converting to standard format.") from e

        # instantiate quantification scores
        try:
            quant_score = QuantScores(
                self.precursor_column_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
            )
        except Exception as e:
            raise QuantificationError("Error generating quantification scores.") from e

        # generate intermediate data structure
        try:
            intermediate_metric_structure = quant_score.generate_intermediate(standard_format, replicate_to_raw)
        except Exception as e:
            raise IntermediateFormatGenerationError("Error generating intermediate data structure.") from e

        # try:
        current_datapoint = QuantDatapoint.generate_datapoint(
            intermediate_metric_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
        )
        # except Exception as e:
        #    raise DatapointGenerationError(f"Error generating datapoint: {e}")

        # add current data point to all datapoints
        # try:
        all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=all_datapoints)
        # except Exception as e:
        #    raise DatapointAppendError(f"Error adding current data point: {e}")

        # return intermediate data structure, all datapoints, and input DataFrame
        # TODO check why there are NA and inf/-inf values
        return (
            intermediate_metric_structure,
            all_datapoints,
            input_df,
        )
