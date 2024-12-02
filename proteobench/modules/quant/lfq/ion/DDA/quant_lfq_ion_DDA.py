from __future__ import annotations

import os

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import Datapoint
from proteobench.exceptions import (
    ConvertStandardFormatError,
    DatapointAppendError,
    DatapointGenerationError,
    IntermediateFormatGenerationError,
    ParseError,
    ParseSettingsError,
    QuantificationError,
)
from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_base.quant_base_module import QuantModule
from proteobench.score.quant.quantscores import QuantScores


class DDAQuantIonModule(QuantModule):
    """DDA Quantification Module for Ion level Quantification."""

    def __init__(
        self,
        token: str,
        proteobench_repo_name: str = "Proteobench/Results_Module2_quant_DDA",
        proteobot_repo_name: str = "Proteobot/Results_Module2_quant_DDA",
        # TODO: Figure out how to do nicer relative calls
        parse_settings_dir: str = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "..",
                "io",
                "parsing",
                "io_parse_settings",
                "Quant",
                "lfq",
                "ion",
                "DDA",
            )
        ),
        module_id="quant_lfq_ion_DDA",
    ):
        """
        DDA Quantification Module for Ion level Quantification.

        Parameters
        ----------
        token
            GitHub token for the user.
        proteobot_repo_name
            Name of the repository for pull requests and where new points are added.
        proteobench_repo_name
            Name of the repository where the benchmarking results will be stored.

        Attributes
        ----------
        precursor_name: str
            Level of quantification.

        """
        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=parse_settings_dir,
            module_id=module_id,
        )
        self.precursor_name = "precursor ion"
        self.module_id = module_id

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    def benchmarking(
        self, input_file_loc: any, input_format: str, user_input: dict, all_datapoints, default_cutoff_min_prec: int = 3
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """
        Main workflow of the module. Used to benchmark workflow results.

        Parameters
        ----------
        input_file
            Path to the workflow output file.
        input_format
            Format of the workflow output file.
        user_input
            User provided parameters for plotting.
        all_datapoints
            DataFrame containing all datapoints from the proteobench repo.
        default_cutoff_min_prec
            Minimum number of runs an ion has to be identified in.

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
            )
        except Exception as e:
            raise ParseSettingsError(f"Error parsing the input file: {e}")

        # Parse settings file
        try:
            parse_settings = ParseSettingsBuilder(
                parse_settings_dir=self.parse_settings_dir, module_id=self.module_id
            ).build_parser(input_format)
        except KeyError as e:
            raise ParseSettingsError(f"Error parsing settings file for parsing, settings seem to be missing: {e}")
        except FileNotFoundError as e:
            raise ParseSettingsError(f"Could not find the parsing settings file: {e}")
        except Exception as e:
            raise ParseSettingsError(f"Error parsing settings file for parsing: {e}")

        try:
            standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
        except KeyError as e:
            raise ConvertStandardFormatError(f"Error converting to standard format, key missing: {e}")
        except Exception as e:
            raise ConvertStandardFormatError(f"Error converting to standard format: {e}")

        # calculate quantification scores
        try:
            quant_score = QuantScores(
                self.precursor_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
            )
        except Exception as e:
            raise QuantificationError(f"Error generating quantification scores: {e}")

        # generate intermediate data structure
        try:
            intermediate_data_structure = quant_score.generate_intermediate(standard_format, replicate_to_raw)
        except Exception as e:
            raise IntermediateFormatGenerationError(f"Error generating intermediate data structure: {e}")

        # try:
        current_datapoint = Datapoint.generate_datapoint(
            intermediate_data_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
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
            intermediate_data_structure,
            all_datapoints,
            input_df,
        )
