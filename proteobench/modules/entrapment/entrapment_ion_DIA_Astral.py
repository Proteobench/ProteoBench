"""
DIA Quantification Module for precursor level Quantification for Astral.
"""

from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.entrapment_datapoint import EntrapmentDatapoint
from proteobench.score.entrapmentscores import EntrapmentScores

from proteobench.exceptions import (
    ConvertStandardFormatError,
    DatapointAppendError,
    DatapointGenerationError,
    IntermediateFormatGenerationError,
    ParseError,
    ParseSettingsError,
    EntrapmentError,
)
from proteobench.io.parsing.load_input import load_input_file
from proteobench.io.parsing.convert_to_intermediate import ConverterBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.entrapment.entrapment_base_module import EntrapmentModule


class DIAEntrapmentIonModuleAstral(EntrapmentModule):
    """
    DIA Quantification Module for precursor level Quantification for Astral.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str, optional
        Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DIA_Astral".
    proteobench_repo_name : str, optional
        Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DIA_Astral".

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    module_id: str = "entrapment_DIA_ion_Astral"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_entrapment_ion_DIA_Astral",
        proteobench_repo_name: str = "Proteobot/Results_entrapment_ion_DIA_Astral",
        branch: Optional[str] = None,
    ):
        """
        Initialize the DIA Quantification Module for precursor level Quantification for Astral.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DIA_Astral".
        proteobench_repo_name : str, optional
            Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DIA_Astral".
        branch : Optional[str], optional
            Branch of the Proteobench repo to check out for result display.
        """
        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=MODULE_SETTINGS_DIRS[self.module_id],
            module_id=self.module_id,
            branch=branch,
        )
        self.precursor_column_name = "precursor ion"

    def is_implemented(self) -> bool:
        """
        Return whether the module is fully implemented.

        Returns
        -------
        bool
            Whether the module is fully implemented.
        """
        return False

    def benchmarking(
        self,
        input_file: str,
        input_format: str,
        user_input: dict,
        all_datapoints: Optional[pd.DataFrame],
        input_file_secondary: str = None,
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        Main workflow of the module for benchmarking workflow results.

        Parameters
        ----------
        input_file : str
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        user_input : dict
            User-provided parameters for plotting.
        all_datapoints : Optional[pd.DataFrame]
            DataFrame containing all data points from the repo.
        input_file_secondary : str, optional
            Path to a secondary input file (used for some formats like AlphaDIA).

        Returns
        -------
        Tuple[DataFrame, DataFrame, DataFrame]
            A tuple containing the intermediate data structure, all data points, and the input DataFrame.
        """
        # Parse workflow output file
        try:
            input_df = load_input_file(input_file, input_format, input_file_secondary)
        except pd.errors.ParserError as e:
            raise ParseError(
                f"Error parsing {input_format} file, please ensure the format is correct and the correct software tool is chosen: {e}"
            )
        except Exception as e:
            raise ParseSettingsError(f"Error parsing the input file: {e}")

        print("Input file parsed successfully.")
        print(input_df.head())

        # Parse settings file
        try:
            parse_settings = ConverterBuilder(
                parse_settings_dir=self.parse_settings_dir, module_id=self.module_id
            ).build_parser(input_format)
        except KeyError as e:
            raise ParseSettingsError(f"Error parsing settings file for parsing, settings missing: {e}")
        except FileNotFoundError as e:
            raise ParseSettingsError(f"Could not find the parsing settings file: {e}")
        except Exception as e:
            raise ParseSettingsError(f"Error parsing settings file for parsing: {e}")

        try:
            standard_format = parse_settings.convert_to_standard_format(input_df)
        except KeyError as e:
            raise ConvertStandardFormatError(f"Error converting to standard format, key missing: {e}")
        except Exception as e:
            raise ConvertStandardFormatError(f"Error converting to standard format: {e}")

        # Generate entrapment intermediate format
        try:
            entrapment_score = EntrapmentScores(mapping_file=self.mapping_file)
        except Exception as e:
            raise EntrapmentError(f"Error generating entrapment scores: {e}")
        try:
            intermediate_metric_structure = entrapment_score.generate_intermediate(standard_format)
        except Exception as e:
            raise IntermediateFormatGenerationError(f"Error generating intermediate data structure: {e}")

        print("Intermediate metric structure generated successfully.")
        print(intermediate_metric_structure.head())
        print(intermediate_metric_structure.columns)

        # Generate current data point
        try:
            current_datapoint = EntrapmentDatapoint.generate_datapoint(
                intermediate_metric_structure,
                input_format,
                user_input,
                entrapment_scores=entrapment_score,
            )
        except Exception as e:
            raise DatapointGenerationError(f"Error generating datapoint: {e}")

        print("Current data point generated successfully.")

        # Add current data point to all datapoints
        try:
            all_datapoints = self.add_current_data_point(current_datapoint, all_datapoints=all_datapoints)
        except Exception as e:
            raise DatapointAppendError(f"Error adding current data point: {e}")

        print("Current data point added to all datapoints successfully.")

        # Return intermediate data structure, all datapoints, and input DataFrame
        return (
            intermediate_metric_structure,
            all_datapoints,
            input_df,
        )

    def get_plot_generator(self):
        return super().get_plot_generator()
