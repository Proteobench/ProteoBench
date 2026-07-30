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
from proteobench.io.parsing.parse_ion import (
    _load_alphadia_entrapment,
    _load_peaks_entrapment,
    load_input_file,
)
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.entrapment.entrapment_base_module import EntrapmentModule

DEFAULT_PRECURSOR_FDR = 0.01


def _declared_precursor_fdr(user_input: dict, default: float = DEFAULT_PRECURSOR_FDR) -> float:
    """
    Read the precursor/PSM FDR threshold declared by the user in the submission form.

    Used for tools that filter their output before export without writing a
    per-precursor q-value (PEAKS). Values of 1 or above are interpreted as
    percentages (``1`` -> ``0.01``), since an FDR of 100% is not a meaningful
    threshold. Unparseable, missing, or non-positive values fall back to ``default``.

    Parameters
    ----------
    user_input : dict
        User-provided parameters from the upload form.
    default : float, optional
        Value returned when no usable FDR was provided, by default 0.01.

    Returns
    -------
    float
        The declared FDR threshold as a fraction.
    """
    try:
        fdr = float(user_input.get("ident_fdr_psm"))
    except (TypeError, ValueError):
        return default
    if fdr <= 0:
        return default
    if fdr >= 1:
        fdr /= 100
    return fdr


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
            if input_format == "AlphaDIA":
                input_df = _load_alphadia_entrapment(input_file)
            elif input_format == "PEAKS":
<<<<<<< Updated upstream
                input_df = _load_peaks_entrapment(input_file)
=======
                # PEAKS exports precursors already filtered at the precursor FDR applied
                # during the search and reports no per-precursor q-value, so the FDR
                # declared in the submission form is used as the reported threshold.
                input_df = _load_peaks_entrapment(input_file, reported_fdr=_declared_precursor_fdr(user_input))
>>>>>>> Stashed changes
            else:
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
            parse_settings = ParseSettingsBuilder(
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

        # Apply mapping file: filter unmapped peptides, assign target/entrapment, merge pair index
        try:
            standard_format = self._apply_mapping(standard_format)
        except EntrapmentError:
            raise
        except Exception as e:
            raise IntermediateFormatGenerationError(f"Error applying entrapment mapping: {e}")

        # Generate entrapment intermediate format
        entrapment_score = EntrapmentScores()
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

    def get_plot_generator(self, y_axis_title: str = None):
        return super().get_plot_generator(y_axis_title=y_axis_title)
