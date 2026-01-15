from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot

from proteobench.plotting.plot_generator_base import PlotGeneratorBase


class LFQHYEPlotGenerator(PlotGeneratorBase):
    """
    Plot generator for LFQ HYE (Human-Yeast-Ecoli) quantification modules.
    Used by DIA/DDA ion modules that use the HYE benchmark dataset.
    """

    def generate_in_depth_plots(
        self, performance_data: pd.DataFrame, parse_settings: any, **kwargs
    ) -> Dict[str, go.Figure]:
        """
        Generate standard LFQ HYE plots.

        Parameters
        ----------
        performance_data : pd.DataFrame
            The performance data to plot
        parse_settings : ParseSettings
            The parse settings for the module
        recalculate : bool
            Whether to recalculate or use cached plots
        **kwargs : dict
            Additional module-specific parameters

        Returns
        -------
        Dict[str, go.Figure]
            Dictionary mapping plot names to plotly figures
        """
        plots = {}

        # Get expected ratios from parse settings
        species_expected_ratio = parse_settings.species_expected_ratio()

        # Generate fold change histogram
        plots["logfc"] = self._plot_fold_change_histogram(performance_data, species_expected_ratio)

        # Generate CV violin plot
        plots["cv"] = self._plot_cv_violinplot(performance_data)

        # Generate MA plot
        plots["ma_plot"] = self._plot_ma_plot(performance_data, species_expected_ratio)

        return plots

    def get_in_depth_plot_layout(self) -> list:
        """
        Define layout for LFQ HYE plots.

        Returns
        -------
        list
            List of in-depth plot configurations defining how plots should be displayed
        """
        return [
            {
                "plots": ["logfc", "cv"],
                "columns": 2,
                "titles": {
                    "logfc": "Log2 Fold Change distributions by species.",
                    "cv": "Coefficient of variation distribution in Condition A and B.",
                },
            },
            {
                "plots": ["ma_plot"],
                "columns": 1,
                "titles": {"ma_plot": "MA plot"},
            },
        ]

    def get_in_depth_plot_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for each plot.

        Returns
        -------
        Dict[str, str]
            Dictionary mapping plot names to their descriptions
        """
        return {
            "logfc": "log2 fold changes calculated from the performance data",
            "cv": "CVs calculated from the performance data",
            "ma_plot": "MA plot calculated from the performance data",
        }

    def plot_main_metric(
        self,
        benchmark_metrics_df: pd.DataFrame,
        metric: str = "Median",
        mode: str = "Species-weighted",
        software_colors: Dict[str, str] = {
            "MaxQuant": "#8bc6fd",
            "AlphaPept": "#17212b",
            "ProlineStudio": "#8b26ff",
            "MSAngel": "#C0FA7D",
            "FragPipe": "#F89008",
            "i2MassChroQ": "#108E2E",
            "Sage": "#E43924",
            "WOMBAT": "#663200",
            "DIA-NN": "#d42f2f",
            "AlphaDIA": "#1D2732",
            "Custom": "#000000",
            "Spectronaut": "#007548",
            "FragPipe (DIA-NN quant)": "#F89008",
            "MSAID": "#bfef45",
            "MetaMorpheus": "#637C7A",
            "Proteome Discoverer": "#911eb4",
            "PEAKS": "#f032e6",
            "quantms": "#f5e830",
        },
        mapping: Dict[str, str] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "",
        legend_name_map: Dict[str, str] = {"AlphaPept": "AlphaPept (legacy tool)"},
        hide_annot: bool = False,
        **kwargs,
    ) -> go.Figure:
        """
        Generate the main performance metric plot for LFQ HYE modules.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            DataFrame containing the results to plot.
        metric : str, optional
            Metric to plot, either "Median" or "Mean".
        mode : str, optional
            Mode of calculation, either, "Species-weighted" or "Global". Case-insensitive.
        software_colors : Dict[str, str]
            Mapping of software names to colors.
        mapping : Dict[str, str]
            Mapping for renaming software versions.
        highlight_color : str
            Color to use for highlighting a specific software/tool.
        label : str
            Label for the highlighted software/tool.
        legend_name_map : Dict[str, str]
            Mapping for legend names.
        hide_annot : bool
            Whether to hide annotations on the plot.
        **kwargs : dict
            Additional module-specific parameters.
        Returns
        -------
        go.Figure
            Plotly figure with the main performance metric plot.
        """
        # Get metric column names and plot_title based on selected metric and mode
        metric_lower, mode_suffix, plot_title = self._get_metric_column_name(metric, mode)

        # ROC-AUC is a special case - uses direct column name without mode suffix
        if metric == "ROC-AUC":
            metric_col_name = "roc_auc"
            legacy_metric_col_name = None  # No legacy column for ROC-AUC
            # Filter to only datapoints that have ROC-AUC calculated
            benchmark_metrics_df = self._filter_datapoints_with_metric(benchmark_metrics_df, metric_col_name)
        else:
            metric_col_name = f"{metric_lower}_abs_epsilon_{mode_suffix}"
            legacy_metric_col_name = f"{metric_lower}_abs_epsilon"

            # Filter based on mode
            # If user selects "Species-weighted" mode, only show datapoints that have the new metrics
            if mode == "Species-weighted":
                benchmark_metrics_df = self._filter_datapoints_with_metric(benchmark_metrics_df, metric_col_name)

        # Extract all values for the selected metric mode
        # Handle mixed old/new datapoints by trying the new key first, then falling back to legacy
        all_metric_values = []
        for v in benchmark_metrics_df["results"]:
            for v2 in v.values():
                # Try new metric name first, fall back to legacy if not present
                value = v2.get(metric_col_name)
                if value is None and legacy_metric_col_name is not None:
                    value = v2.get(legacy_metric_col_name)
                if value is not None:
                    all_metric_values.append(value)

        all_nr_prec = [v2["nr_prec"] for v in benchmark_metrics_df["results"] for v2 in v.values()]

        # Add hover text with detailed information for each data point
        hover_texts = []
        for idx, _ in benchmark_metrics_df.iterrows():
            datapoint_text = ""
            if benchmark_metrics_df.is_temporary[idx] == True:
                datapoint_text = (
                    f"ProteoBench ID: {benchmark_metrics_df.id[idx]}<br>"
                    + f"Software tool: {benchmark_metrics_df.software_name[idx]} {benchmark_metrics_df.software_version[idx]}<br>"
                )
                if "comments" in benchmark_metrics_df.columns:
                    comment = benchmark_metrics_df.comments[idx]
                    if isinstance(comment, str):
                        datapoint_text = (
                            datapoint_text
                            + f"Comment (private submission): {comment[:10] + '...' if len(comment) > 10 else comment}..."
                        )
            else:
                # TODO: Determine parameters based on module
                datapoint_text = (
                    f"ProteoBench ID: {benchmark_metrics_df.id[idx]}<br>"
                    + f"Software tool: {benchmark_metrics_df.software_name[idx]} {benchmark_metrics_df.software_version[idx]}<br>"
                    + f"Search engine: {benchmark_metrics_df.search_engine[idx]} {benchmark_metrics_df.search_engine_version[idx]}<br>"
                    + f"FDR psm: {benchmark_metrics_df.ident_fdr_psm[idx]}<br>"
                    + f"MBR: {benchmark_metrics_df.enable_match_between_runs[idx]}<br>"
                    + f"Precursor Tolerance: {benchmark_metrics_df.precursor_mass_tolerance[idx]}<br>"
                    + f"Fragment Tolerance: {benchmark_metrics_df.fragment_mass_tolerance[idx]}<br>"
                    + f"Enzyme: {benchmark_metrics_df.enzyme[idx]} <br>"
                    + f"Missed Cleavages: {benchmark_metrics_df.allowed_miscleavages[idx]}<br>"
                    + f"Min peptide length: {benchmark_metrics_df.min_peptide_length[idx]}<br>"
                    + f"Max peptide length: {benchmark_metrics_df.max_peptide_length[idx]}<br>"
                )
                if "submission_comments" in benchmark_metrics_df.columns:
                    comment = benchmark_metrics_df.submission_comments[idx]
                    if isinstance(comment, str):
                        datapoint_text = (
                            datapoint_text
                            + f"Comment (public submission): {comment[:10] + '...' if len(comment) > 10 else comment}..."
                        )

            hover_texts.append(datapoint_text)

        scatter_size = [mapping[item] for item in benchmark_metrics_df["old_new"]]
        if "Highlight" in benchmark_metrics_df.columns:
            scatter_size = [
                item * 2 if highlight else item
                for item, highlight in zip(scatter_size, benchmark_metrics_df["Highlight"])
            ]

        # Color plot based on software tool
        colors = [software_colors[software] for software in benchmark_metrics_df["software_name"]]
        if "Highlight" in benchmark_metrics_df.columns:
            colors = [
                highlight_color if highlight else item
                for item, highlight in zip(colors, benchmark_metrics_df["Highlight"])
            ]

        benchmark_metrics_df["color"] = colors
        benchmark_metrics_df["hover_text"] = hover_texts
        benchmark_metrics_df["scatter_size"] = scatter_size

        if all_metric_values:
            layout_xaxis_range = [
                min(all_metric_values) - min(all_metric_values) * 0.05,
                max(all_metric_values) + max(all_metric_values) * 0.05,
            ]
        else:
            layout_xaxis_range = [0, 1]

        if all_nr_prec:
            layout_yaxis_range = [
                min(all_nr_prec) - min(max(all_nr_prec) * 0.05, 2000),
                max(all_nr_prec) + min(max(all_nr_prec) * 0.05, 2000),
            ]
        else:
            layout_yaxis_range = [0, 1000]

        fig = go.Figure(
            layout_yaxis_range=layout_yaxis_range,
            layout_xaxis_range=layout_xaxis_range,
        )

        # Get all unique color-software combinations (necessary for highlighting)
        color_software_combinations = benchmark_metrics_df[["color", "software_name"]].drop_duplicates()
        benchmark_metrics_df["enable_match_between_runs"] = benchmark_metrics_df["enable_match_between_runs"].astype(
            str
        )
        # plot the data points, one trace per software tool
        for _, row in color_software_combinations.iterrows():
            color = row["color"]
            software = row["software_name"]

            tmp_df = benchmark_metrics_df[
                (benchmark_metrics_df["color"] == color) & (benchmark_metrics_df["software_name"] == software)
            ]
            # to do: remove this line as soon as parameters are homogeneous, see #380
            # tmp_df["enable_match_between_runs"] = tmp_df["enable_match_between_runs"].astype(str)

            if metric_col_name in tmp_df.columns and tmp_df[metric_col_name].notna().any():
                # use new column, but fill null values with legacy if available
                if legacy_metric_col_name is not None and legacy_metric_col_name in tmp_df.columns:
                    x_values = tmp_df[metric_col_name].fillna(tmp_df[legacy_metric_col_name])
                else:
                    x_values = tmp_df[metric_col_name]
            elif legacy_metric_col_name is not None:
                # fall back to legacy column if new not available
                x_values = tmp_df[legacy_metric_col_name]
            else:
                # No fallback available (e.g. ROC-AUC case)
                x_values = tmp_df[metric_col_name]

            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=tmp_df["nr_prec"],
                    mode="markers" if label == "None" else "markers+text",
                    hovertext=tmp_df["hover_text"],
                    text=tmp_df[label] if label != "None" else None,
                    marker=dict(color=tmp_df["color"], showscale=False),
                    marker_size=tmp_df["scatter_size"],
                    name=legend_name_map.get(tmp_df["software_name"].iloc[0], tmp_df["software_name"].iloc[0]),
                )
            )

        fig.update_layout(
            width=700,
            height=700,
            xaxis=dict(
                title=plot_title,
                gridcolor="white",
                gridwidth=2,
                linecolor="black",
            ),
            yaxis=dict(
                title="Total number of precursor ions quantified in the selected number of raw files",
                gridcolor="white",
                gridwidth=2,
                linecolor="black",
            ),
        )
        fig.update_xaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text="-Beta-" if not hide_annot else "",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        fig.update_layout(clickmode="event+select")

        return fig

    def _plot_fold_change_histogram(
        self, performance_data: pd.DataFrame, species_expected_ratio: Dict[str, Dict[str, Union[float, str]]]
    ) -> go.Figure:
        """
        Generate fold change histogram plot.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing log2_A_vs_B column
        species_expected_ratio : Dict[str, Dict[str, Union[float, str]]]
            Dictionary with expected ratios for each species, and colors

        Returns
        -------
        go.Figure
            Plotly figure with fold change distributions
        """
        species_list = list(species_expected_ratio.keys())

        # Filter to rows where at least one species is present
        performance_data = performance_data[performance_data[species_list].any(axis=1)]
        performance_data["species"] = performance_data[species_list].apply(lambda x: species_list[np.argmax(x)], axis=1)

        # Prepare plot data
        hist_data = []
        group_labels = []
        colors = []

        for species in species_list:
            hist_data.append(
                performance_data.loc[performance_data["species"] == species, "log2_A_vs_B"].dropna().tolist()
            )
            group_labels.append(species)
            colors.append(species_expected_ratio[species].get("color", "#000000"))

        # Create distribution plot
        if hist_data:
            fig = create_distplot(
                hist_data,
                group_labels,
                show_hist=False,
                show_rug=False,
                colors=colors,
            )

            for trace in fig.data:
                if trace.mode == "lines":
                    trace.update(fill="tozeroy", opacity=0.4)

            fig.update_layout(
                xaxis=dict(
                    title="Log2(Condition A / Condition B)",
                    color="black",
                    gridwidth=1,
                    gridcolor="lightgray",
                    range=[-4, 4],
                ),
                yaxis=dict(title="Density", color="black", gridwidth=1, gridcolor="lightgray"),
            )

            ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_expected_ratio.items()}
            for species, ratio in ratio_map.items():
                fig.add_vline(
                    x=ratio,
                    line_dash="dash",
                    line_color=species_expected_ratio[species].get("color", "#000000"),
                    annotation_text=f"Expected {species}",
                )

        else:
            # Create empty figure if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for fold change plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

        return fig

    def _plot_cv_violinplot(self, performance_data: pd.DataFrame) -> go.Figure:
        """
        Generate coefficient of variation violin plot.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing CV_A and CV_B columns

        Returns
        -------
        go.Figure
            Plotly figure with CV violin plots
        """
        # Prepare data for violin plot
        cv_data = []
        conditions = []

        # Add CV data for Condition A
        if "CV_A" in performance_data.columns:
            cv_a = performance_data["CV_A"].replace([np.inf, -np.inf], np.nan).dropna()
            cv_data.extend(cv_a)
            conditions.extend(["Condition A"] * len(cv_a))

        # Add CV data for Condition B
        if "CV_B" in performance_data.columns:
            cv_b = performance_data["CV_B"].replace([np.inf, -np.inf], np.nan).dropna()
            cv_data.extend(cv_b)
            conditions.extend(["Condition B"] * len(cv_b))

        # Create violin plot
        if cv_data:
            df_plot = pd.DataFrame({"CV": cv_data, "Condition": conditions})

            fig = px.violin(df_plot, y="CV", x="Condition", box=True, points=False)
        else:
            # Create empty figure if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No CV data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

        return fig

    def _plot_ma_plot(
        self, performance_data: pd.DataFrame, species_expected_ratio: Dict[str, Dict[str, Union[float, str]]]
    ) -> go.Figure:
        """
        Generate MA plot (M vs A plot) but with A on the y-axis and M on the x-axis.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing log2_A_vs_B and mean abundance columns
        species_expected_ratio : Dict[str, Dict[str, Union[float, str]]]
            Expected ratios for each species and their colors

        Returns
        -------
        go.Figure
            Plotly figure with MA plot (M on x, A on y)
        """

        # Define colors for species
        color_map = {species: data["color"] for species, data in species_expected_ratio.items()}

        performance_data["logIntensityMean"] = (
            performance_data["log_Intensity_mean_A"] + performance_data["log_Intensity_mean_B"]
        ) / 2

        fig = px.scatter(
            performance_data,
            x="log2_A_vs_B",
            y="logIntensityMean",
            color="species",
            color_discrete_map=color_map,
            labels={"log2_A_vs_B": "M (Log2 Fold Change(A:B))", "logIntensityMean": "A (Mean Abundance)"},
            title="MA Plot",
            size_max=10,
            opacity=0.2,
        )

        # Add vertical lines for expected M values (since M is on x-axis) across the A range
        if fig.data:
            ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_expected_ratio.items()}
            for species, ratio in ratio_map.items():
                fig.add_vline(
                    x=ratio,
                    line_dash="dash",
                    line_color=species_expected_ratio[species].get("color", "#000000"),
                    annotation_text=f"Expected {species}",
                )

            fig.update_traces(marker=dict(size=6))
        else:
            fig.add_annotation(
                text="No data available for MA plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        return fig

    def _get_metric_column_name(self, metric: str, mode: str) -> Tuple[str, str, str]:
        """
        Get the appropriate metric column names based on the specified metric and mode.

        Parameters
        ----------
        metric : str
            The metric to plot: "Median", "Mean", or "ROC-AUC".
        mode : str
            The mode for filtering, either "global" or "eq_species". Ignored for ROC-AUC.

        Returns
        -------
        Tuple[str, str, str]
            A tuple containing the metric_lower, mode_suffix, and plot_title
        """
        # ROC-AUC is a special case - no mode suffix, single column name
        if metric == "ROC-AUC":
            return "roc_auc", None, "ROC-AUC score for distinguishing changed from unchanged species"

        metric_lower = metric.lower()
        mode_suffix = "global" if mode.lower() == "global" else "eq_species"
        mode_description = "globally" if mode.lower() == "global" else "using equally weighted species averages"

        plot_title = f"{metric} absolute difference between measured and expected log2-transformed fold change (calculated {mode_description})"

        return metric_lower, mode_suffix, plot_title

    def _filter_datapoints_with_metric(self, benchmark_metrics_df: pd.DataFrame, metric_col_name: str) -> pd.DataFrame:
        """
        Filter datapoints to only include those that have the specified metric calculated.

        This is used when the user selects "Species-weighted" or "ROC-AUC" mode to ensure only datapoints
        with the new metric calculation are displayed (avoiding visual confusion with legacy metric
        calucations).

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            DataFrame containing benchmark metrics for datapoints.
        metric_col_name : str
            The name of the metric column to filter on.

        Returns
        -------
        pd.DataFrame
            Filtered DataFrame containing only datapoints with the specified metric.
        """

        def has_metric(results_dict):
            """Check if the results dictionary contains the specified metric."""
            try:
                for threshold_dict in results_dict.values():
                    if metric_col_name in threshold_dict:
                        return True
            except (TypeError, AttributeError):
                pass
            return False

        # Filter to only datapoints that have the specified metric calculated
        return benchmark_metrics_df[benchmark_metrics_df["results"].apply(has_metric)].copy()
