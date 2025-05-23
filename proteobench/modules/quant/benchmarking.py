"""
Benchmarking functionality for quantification modules.
"""

from typing import Optional, Tuple, Dict, List, Callable, Type
import pandas as pd
from pandas import DataFrame
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial, wraps

from proteobench.datapoint.quant_datapoint import QuantDatapoint
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
from proteobench.score.quant.quantscores import QuantScores


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


@handle_benchmarking_error(ParseError, "Error parsing input file")
def _load_input(input_file: str, input_format: str) -> DataFrame:
    """Load and parse the input file."""
    return load_input_file(input_file, input_format)


@handle_benchmarking_error(ParseSettingsError, "Error parsing settings")
def _load_settings(parse_settings_dir: str, module_id: str, input_format: str):
    """Load and parse the settings file."""
    return ParseSettingsBuilder(parse_settings_dir=parse_settings_dir, module_id=module_id).build_parser(input_format)


@handle_benchmarking_error(ConvertStandardFormatError, "Error converting to standard format")
def _convert_format(parse_settings, input_df: DataFrame):
    """Convert input to standard format."""
    return parse_settings.convert_to_standard_format(input_df)


@handle_benchmarking_error(QuantificationError, "Error generating quantification scores")
def _create_quant_scores(precursor_column_name: str, parse_settings):
    """Create quantification scores."""
    return QuantScores(precursor_column_name, parse_settings.species_expected_ratio(), parse_settings.species_dict())


@handle_benchmarking_error(IntermediateFormatGenerationError, "Error generating intermediate data structure")
def _generate_intermediate(quant_score, standard_format, replicate_to_raw):
    """Generate intermediate data structure."""
    return quant_score.generate_intermediate(standard_format, replicate_to_raw)


@handle_benchmarking_error(DatapointGenerationError, "Error generating datapoint")
def _generate_datapoint(intermediate_metric_structure, input_format, user_input, default_cutoff_min_prec):
    """Generate datapoint."""
    return QuantDatapoint.generate_datapoint(
        intermediate_metric_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
    )


@handle_benchmarking_error(DatapointAppendError, "Error adding current data point")
def _append_datapoint(add_datapoint_func, current_datapoint, all_datapoints):
    """Append datapoint to all datapoints."""
    return add_datapoint_func(current_datapoint, all_datapoints=all_datapoints)


def run_benchmarking(
    input_file: str,
    input_format: str,
    user_input: dict,
    all_datapoints: Optional[pd.DataFrame],
    parse_settings_dir: str,
    module_id: str,
    precursor_column_name: str,
    default_cutoff_min_prec: int = 3,
    add_datapoint_func=None,
) -> Tuple[DataFrame, DataFrame, DataFrame]:
    """
    Run the benchmarking workflow.

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
    parse_settings_dir : str
        Directory containing parse settings.
    module_id : str
        Module identifier for configuration.
    precursor_column_name : str
        Name of the precursor column.
    default_cutoff_min_prec : int, optional
        Minimum number of runs a precursor ion must be identified in. Defaults to 3.
    add_datapoint_func : callable, optional
        Function to add the current datapoint to all datapoints. If None, the datapoint won't be added.

    Returns
    -------
    Tuple[DataFrame, DataFrame, DataFrame]
        A tuple containing the intermediate data structure, all data points, and the input DataFrame.
    """
    # Load and parse input file
    input_df = _load_input(input_file, input_format)

    # Load and parse settings
    parse_settings = _load_settings(parse_settings_dir, module_id, input_format)

    # Convert to standard format
    standard_format, replicate_to_raw = _convert_format(parse_settings, input_df)

    # Create quantification scores
    quant_score = _create_quant_scores(precursor_column_name, parse_settings)

    # Generate intermediate structure
    intermediate_metric_structure = _generate_intermediate(quant_score, standard_format, replicate_to_raw)

    # Generate datapoint
    current_datapoint = _generate_datapoint(
        intermediate_metric_structure, input_format, user_input, default_cutoff_min_prec
    )

    # Add datapoint if function provided
    if add_datapoint_func is not None:
        all_datapoints = _append_datapoint(add_datapoint_func, current_datapoint, all_datapoints)

    return (
        intermediate_metric_structure,
        all_datapoints,
        input_df,
    )


def run_benchmarking_with_timing(
    input_file: str,
    input_format: str,
    user_input: dict,
    all_datapoints: Optional[pd.DataFrame],
    parse_settings_dir: str,
    module_id: str,
    precursor_column_name: str,
    default_cutoff_min_prec: int = 3,
    add_datapoint_func=None,
) -> Tuple[DataFrame, DataFrame, DataFrame, Dict[str, float]]:
    """
    Run the benchmarking workflow with timing information.

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
    parse_settings_dir : str
        Directory containing parse settings.
    module_id : str
        Module identifier for configuration.
    precursor_column_name : str
        Name of the precursor column.
    default_cutoff_min_prec : int, optional
        Minimum number of runs a precursor ion must be identified in. Defaults to 3.
    add_datapoint_func : callable, optional
        Function to add the current datapoint to all datapoints. If None, the datapoint won't be added.

    Returns
    -------
    Tuple[DataFrame, DataFrame, DataFrame, Dict[str, float]]
        A tuple containing the intermediate data structure, all data points, the input DataFrame,
        and a dictionary of timing information.
    """
    from contextlib import contextmanager
    import time

    timings: Dict[str, float] = {}

    @contextmanager
    def time_block(label: str):
        t0 = time.perf_counter()
        yield
        timings[label] = time.perf_counter() - t0

    with time_block("load_input_file"):
        input_df = load_input_file(input_file, input_format)

    with time_block("parse_settings"):
        parse_settings = ParseSettingsBuilder(parse_settings_dir=parse_settings_dir, module_id=module_id).build_parser(
            input_format
        )

    with time_block("convert_to_standard_format"):
        standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

    with time_block("instantiate_quant_scores"):
        quant_score = QuantScores(
            precursor_column_name, parse_settings.species_expected_ratio(), parse_settings.species_dict()
        )

    with time_block("generate_intermediate"):
        intermediate_metric_structure = quant_score.generate_intermediate(standard_format, replicate_to_raw)

    with time_block("generate_datapoint"):
        current_datapoint = QuantDatapoint.generate_datapoint(
            intermediate_metric_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
        )

    if add_datapoint_func is not None:
        with time_block("append_datapoint"):
            all_datapoints = add_datapoint_func(current_datapoint, all_datapoints=all_datapoints)

    return (
        intermediate_metric_structure,
        all_datapoints,
        input_df,
        timings,
    )
