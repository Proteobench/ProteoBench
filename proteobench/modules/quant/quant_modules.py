"""
All quantification benchmark modules.

Each class is configuration for the shared pipeline in ``QuantModule.benchmarking``;
see ``QuantModule`` for the available class attributes.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from pandas import DataFrame

from proteobench.datapoint.quant_datapoint import QuantDatapointPYE
from proteobench.io.parsing.parse_peptidoform import load_input_file as load_peptidoform_input_file
from proteobench.modules.quant.quant_base_module import QuantModule
from proteobench.plotting.plot_generator_lfq_lowinput import LFQLowInputPlotGenerator
from proteobench.plotting.plot_generator_lfq_PYE import LFQPYEPlotGenerator


class DDAQuantIonModuleQExactive(QuantModule):
    """DDA quantification module, precursor ion level, QExactive."""

    module_id = "quant_lfq_DDA_ion_QExactive"
    results_repo = "Results_quant_ion_DDA"


class DDAQuantIonAstralModule(QuantModule):
    """DDA quantification module, precursor ion level, Astral."""

    module_id = "quant_lfq_DDA_ion_Astral"
    results_repo = "Results_quant_ion_DDA_Astral"


class DIAQuantIonModuleAIF(QuantModule):
    """DIA quantification module, precursor ion level, AIF."""

    module_id = "quant_lfq_DIA_ion_AIF"
    results_repo = "Results_quant_ion_DIA"


class DIAQuantIonModuleAstral(QuantModule):
    """DIA quantification module, precursor ion level, Astral."""

    module_id = "quant_lfq_DIA_ion_Astral"
    results_repo = "Results_quant_ion_DIA_Astral"


class DIAQuantIonModulediaPASEF(QuantModule):
    """DIA quantification module, precursor ion level, diaPASEF."""

    module_id = "quant_lfq_DIA_ion_diaPASEF"
    results_repo = "Results_quant_ion_DIA_diaPASEF"


class DIAQuantIonModuleZenoTOF(QuantModule):
    """DIA quantification module, precursor ion level, ZenoTOF."""

    module_id = "quant_lfq_DIA_ion_ZenoTOF"
    results_repo = "Results_quant_lfq_DIA_ion_ZenoTOF"


class DIAQuantIonModulediaSC(QuantModule):
    """DIA quantification module, precursor ion level, low input (single cell)."""

    module_id = "quant_lfq_DIA_ion_lowinput"
    results_repo = "Results_quant_ion_DIA_lowinput"


class DIAQuantIonModuleAstralLowInput(QuantModule):
    """DIA quantification module, precursor ion level, Astral low input."""

    module_id = "quant_lfq_DIA_ion_Astral_lowinput"
    results_repo = "Results_quant_ion_DIA_Astral_lowinput"
    plot_generator_cls = LFQLowInputPlotGenerator
    default_cutoff_min_feature = 6
    max_nr_observed = 12


class DIAQuantIonModuletimsTOFLowInput(QuantModule):
    """DIA quantification module, precursor ion level, timsTOF low input."""

    module_id = "quant_lfq_DIA_ion_timsTOF_lowinput"
    results_repo = "Results_quant_ion_DIA_timsTOF_lowinput"
    plot_generator_cls = LFQLowInputPlotGenerator
    default_cutoff_min_feature = 6
    max_nr_observed = 12


class DIAQuantIonModulePlasma(QuantModule):
    """DIA quantification module, precursor ion level, plasma (Plasma-Yeast-Ecoli)."""

    module_id = "quant_lfq_DIA_ion_plasma"
    results_repo = "Results_quant_ion_DIA_plasma"
    y_axis_title = "Number of quantified spike-in precursors"
    datapoint_cls = QuantDatapointPYE
    plot_generator_cls = LFQPYEPlotGenerator

    # Top-level datapoint column -> metric key in the nested results dict.
    PLASMA_COLUMN_TO_METRIC = {
        "median_abs_log2_fc_error_spike_ins": "median_abs_log2_fc_error_spike_ins",
        "nr_quantified_spike_ins": "nr_quantified_spike_ins",
        "nr_quantified_HUMAN": "nr_quantified_HUMAN",
        "nr_quantified_YEAST": "nr_quantified_YEAST",
        "nr_quantified_ECOLI": "nr_quantified_ECOLI",
        "dynamic_range_human_plasma": "dynamic_range_human_plasma_mean",
        "median_abs_epsilon_human_plasma": "median_abs_epsilon_human_plasma",
    }

    @staticmethod
    def filter_data_point(all_datapoints: pd.DataFrame, default_val_slider: int = 3) -> pd.DataFrame:
        """
        Filter the data points and refresh the plasma-specific columns at the selected cutoff.

        On top of the generic filtering, the plasma-specific top-level columns (the per-species
        identification counts, the spike-in error, the plasma dynamic range and the plasma
        accuracy) are re-read from the nested ``results`` dictionary at the selected
        ``min_nr_observed`` level. Without this, those columns would keep the value of the cutoff
        that was used at submission time and would disagree with the overview plot.

        Parameters
        ----------
        all_datapoints : pd.DataFrame
            All data points.
        default_val_slider : int, optional
            The minimum number of observations for filtering. Defaults to 3.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the filtered data points.
        """
        all_datapoints = QuantModule.filter_data_point(all_datapoints, default_val_slider)

        if len(all_datapoints) == 0 or "results" not in all_datapoints.columns:
            return all_datapoints

        for column, metric_key in DIAQuantIonModulePlasma.PLASMA_COLUMN_TO_METRIC.items():
            values = [
                DIAQuantIonModulePlasma._get_metric_at_cutoff(results, default_val_slider, metric_key)
                for results in all_datapoints["results"]
            ]
            # Only overwrite when at least one datapoint carries the metric, so datapoints
            # submitted before the metric existed keep whatever they already have.
            if any(value is not None for value in values):
                all_datapoints[column] = [
                    value if value is not None else existing
                    for value, existing in zip(values, all_datapoints.get(column, [None] * len(values)))
                ]

        return all_datapoints

    @staticmethod
    def _get_metric_at_cutoff(results: dict, cutoff: int, metric_key: str):
        """
        Read a single metric from a nested results dictionary at the given cutoff level.

        Parameters
        ----------
        results : dict
            The nested results dictionary of a datapoint. Keys may be integers (in-process) or
            strings (loaded from JSON).
        cutoff : int
            The min_nr_observed level to read.
        metric_key : str
            The name of the metric to read.

        Returns
        -------
        Any
            The metric value, or None when it is not available.
        """
        if not isinstance(results, dict):
            return None

        metrics = results.get(cutoff)
        if not isinstance(metrics, dict):
            metrics = results.get(str(cutoff))
        if not isinstance(metrics, dict):
            return None

        return metrics.get(metric_key)


class DDAQuantPeptidoformModule(QuantModule):
    """DDA quantification module, peptidoform level."""

    module_id = "quant_lfq_DDA_peptidoform"
    results_repo = "Results_quant_peptidoform_DDA"
    precursor_column_name = "peptidoform"
    y_axis_title = "Total number of peptidoforms quantified in the selected number of raw files"

    def load_input(self, input_file: str, input_format: str, input_file_secondary: Optional[str] = None) -> DataFrame:
        """
        Load the workflow output with the peptidoform parser, which takes no secondary file.

        Parameters
        ----------
        input_file : str
            Path to the workflow output file.
        input_format : str
            Format of the workflow output file.
        input_file_secondary : str, optional
            Ignored.

        Returns
        -------
        DataFrame
            The loaded workflow output.
        """
        return load_peptidoform_input_file(input_file, input_format)
