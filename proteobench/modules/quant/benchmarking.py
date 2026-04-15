"""
Benchmarking functionality for quantification modules.

This module owns the scoring/datapoint pipeline. It receives already-parsed data
(standard_format + replicate_to_raw) and module settings — it knows nothing about
file formats, TOML configs, or parse settings.
"""

from functools import wraps
from typing import Callable, Optional, Tuple, Type

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import QuantDatapointHYE
from proteobench.exceptions import (
    DatapointAppendError,
    DatapointGenerationError,
    IntermediateFormatGenerationError,
    QuantificationError,
)
from proteobench.io.parsing.new_parse_input import ModuleSettings, process_species
from proteobench.score.quantscoresHYE import QuantScoresHYE


def handle_benchmarking_error(error_type: Type[Exception], error_message: str):
    """
    Decorator to handle benchmarking errors with custom error messages.

    Parameters
    ----------
    error_type : Type[Exception]
        The type of exception to catch
    error_message : str
        The error message to raise if the exception occurs
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                raise error_type(f"{error_message}: {e}")
            except Exception as e:
                raise error_type(f"Unexpected error in {func.__name__}: {e}")

        return wrapper

    return decorator


@handle_benchmarking_error(QuantificationError, "Error generating quantification scores")
def _create_quant_scores(precursor_column_name: str, module_settings, quant_score_class=QuantScoresHYE):
    """Create quantification scores."""
    return quant_score_class(
        precursor_column_name, module_settings.species_expected_ratio, module_settings.species_dict
    )


@handle_benchmarking_error(IntermediateFormatGenerationError, "Error generating intermediate data structure")
def _generate_intermediate(quant_score, standard_format, replicate_to_raw):
    """Generate intermediate data structure."""
    return quant_score.generate_intermediate(standard_format, replicate_to_raw)


@handle_benchmarking_error(DatapointGenerationError, "Error generating datapoint")
def _generate_datapoint(
    intermediate_metric_structure,
    input_format,
    user_input,
    default_cutoff_min_prec,
    max_nr_observed=None,
    datapoint_class=QuantDatapointHYE,
):
    """Generate datapoint."""
    return datapoint_class.generate_datapoint(
        intermediate_metric_structure,
        input_format,
        user_input,
        default_cutoff_min_prec=default_cutoff_min_prec,
        max_nr_observed=max_nr_observed,
    )


@handle_benchmarking_error(DatapointAppendError, "Error adding current data point")
def _append_datapoint(add_datapoint_func, current_datapoint, all_datapoints):
    """Append datapoint to all datapoints."""
    return add_datapoint_func(current_datapoint, all_datapoints=all_datapoints)


def run_benchmarking(
    standard_format: pd.DataFrame,
    replicate_to_raw: dict,
    module_settings: ModuleSettings,
    input_format: str,
    user_input: dict,
    precursor_column_name: str,
    all_datapoints: Optional[pd.DataFrame] = None,
    default_cutoff_min_prec: int = 3,
    add_datapoint_func=None,
    max_nr_observed: int = None,
    quant_score_class=QuantScoresHYE,
    datapoint_class=QuantDatapointHYE,
) -> Tuple[DataFrame, DataFrame]:
    """
    Run the benchmarking workflow on already-parsed data.

    Parameters
    ----------
    standard_format : pd.DataFrame
        Parsed and standardized input data (from parse_input()).
    replicate_to_raw : dict
        Mapping from conditions to raw file names (from parse_input()).
    module_settings : ModuleSettings
        Module-level configuration (species, ratios, thresholds).
    input_format : str
        Format of the workflow output file (e.g., "MaxQuant").
    user_input : dict
        User-provided parameters for plotting.
    precursor_column_name : str
        Name of the precursor column.
    all_datapoints : Optional[pd.DataFrame]
        DataFrame containing all data points from the repo.
    default_cutoff_min_prec : int, optional
        Minimum number of runs a precursor ion must be identified in. Defaults to 3.
    add_datapoint_func : callable, optional
        Function to add the current datapoint to all datapoints.
    max_nr_observed : int, optional
        Maximum number of observed values for datapoint generation.
    quant_score_class : type, optional
        Score class to use. Defaults to QuantScoresHYE.
    datapoint_class : type, optional
        Datapoint class to use. Defaults to QuantDatapointHYE.

    Returns
    -------
    Tuple[DataFrame, DataFrame]
        A tuple containing the intermediate data structure and all data points.
    """
    # Process species
    standard_format = process_species(standard_format, module_settings)

    # Create quantification scores
    quant_score = _create_quant_scores(precursor_column_name, module_settings, quant_score_class)

    # Generate intermediate structure
    intermediate_metric_structure = _generate_intermediate(quant_score, standard_format, replicate_to_raw)

    # Generate datapoint
    current_datapoint = _generate_datapoint(
        intermediate_metric_structure,
        input_format,
        user_input,
        default_cutoff_min_prec,
        max_nr_observed=max_nr_observed,
        datapoint_class=datapoint_class,
    )

    # Add datapoint if function provided
    if add_datapoint_func is not None:
        all_datapoints = _append_datapoint(add_datapoint_func, current_datapoint, all_datapoints)

    return (
        intermediate_metric_structure,
        all_datapoints,
    )
