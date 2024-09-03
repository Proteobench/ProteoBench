from __future__ import annotations

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
from proteobench.io.parsing.parse_peptidoform import load_input_file
from proteobench.io.parsing.parse_settings_peptidoform import ParseSettingsBuilder
from proteobench.modules.quant_base.quant_base_module import QuantModule
from proteobench.score.quant.quantscores import QuantScores


class QuantPeptidoformDIAModule(QuantModule):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(
        self,
        token,
        proteobot_repo_name="Proteobot/Results_quant_peptidoform_DIA",
        proteobench_repo_name="Proteobench/Results_quant_peptidoform_DIA",
    ):
        super().__init__(token, proteobot_repo_name=proteobot_repo_name, proteobench_repo_name=proteobench_repo_name)
        self.precursor_name = "peptidoform"

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return False

    def benchmarking(
        self, input_file: str, input_format: str, user_input: dict, all_datapoints, default_cutoff_min_prec: int = 3
    ) -> tuple[DataFrame, DataFrame, DataFrame]:
        """Main workflow of the module. Used to benchmark workflow results."""
        # Parse user config

        try:
            input_df = load_input_file(input_file, input_format)
        except pd.errors.ParserError as e:
            raise ParseError(
                f"Error parsing {input_format} file, please make sure the format is correct and the correct software tool is chosen: {e}"
            )
        except Exception as e:
            raise ParseSettingsError(f"Error parsing the input file: {e}")

        try:
            parse_settings = ParseSettingsBuilder().build_parser(input_format)
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

        try:
            # Get quantification data
            quant_score = QuantScores(
                self.precursor_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
            )
        except Exception as e:
            raise QuantificationError(f"Error generating quantification scores: {e}")

        try:
            intermediate_data_structure = quant_score.generate_intermediate(standard_format, replicate_to_raw)
        except Exception as e:
            raise IntermediateFormatGenerationError(f"Error generating intermediate data structure: {e}")

        try:
            current_datapoint = Datapoint.generate_datapoint(
                intermediate_data_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
            )
        except Exception as e:
            raise DatapointGenerationError(f"Error generating datapoint: {e}")

        try:
            all_datapoints = self.add_current_data_point(all_datapoints, current_datapoint)
        except Exception as e:
            raise DatapointAppendError(f"Error adding current data point: {e}")

        # TODO check why there are NA and inf/-inf values
        return (
            intermediate_data_structure,
            all_datapoints,
            input_df,
        )
