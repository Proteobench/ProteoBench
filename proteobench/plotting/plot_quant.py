"""
Module for plotting quantitative proteomics data.
"""

from typing import Dict

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot


class PlotDataPoint:
    """
    Class for plotting data points.
    """

    @staticmethod
    def plot_fold_change_histogram(
        result_df: pd.DataFrame, species_ratio: Dict[str, Dict[str, str]], hide_annot: bool = False
    ) -> go.Figure:
        """
        Plot smooth shaded density distributions of log2 fold changes using Plotly, color-coded by species.

        Parameters
        ----------
        result_df : pd.DataFrame
            The results DataFrame containing fold changes and species data.
        species_ratio : Dict[str, Dict[str, str]]
            A dictionary mapping species to their respective colors and ratios.

        Returns
        -------
        go.Figure
            A Plotly figure object representing the shaded density plots.
        """
        species_list = list(species_ratio.keys())

        # Filter to include only rows where any of the species columns are True
        result_df = result_df[result_df[species_list].any(axis=1)]
        result_df["kind"] = result_df[species_list].apply(lambda x: species_list[np.argmax(x)], axis=1)

        # Prepare lists for create_distplot
        data = []
        group_labels = []
        colors = []
        for species in species_list:
            data.append(result_df.loc[result_df["kind"] == species, "log2_A_vs_B"].dropna().tolist())
            group_labels.append(species)
            colors.append(species_ratio[species]["color"])

        # Create the distplot without histogram or rug
        fig = create_distplot(data, group_labels, colors=colors, show_hist=False, show_rug=False)

        # Update each density trace to fill under the curve
        for trace in fig.data:
            if trace.mode == "lines":
                trace.update(fill="tozeroy", opacity=0.4)  # adjust opacity as needed

        # Customize layout
        fig.update_layout(
            width=700,
            height=700,
            xaxis=dict(title="log2_A_vs_B", color="black", gridwidth=1, linecolor="black", range=[-4, 4]),
            yaxis=dict(title="Density", color="black", gridwidth=1, linecolor="black"),
        )

        # Add vertical lines for expected ratios
        ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_ratio.items()}
        for species, ratio in ratio_map.items():
            fig.add_vline(
                x=ratio, line_dash="dash", line_color=species_ratio[species]["color"], annotation_text=species
            )

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text="-Beta-" if not hide_annot else "",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        return fig

    @staticmethod
    def plot_metric(
        benchmark_metrics_df: pd.DataFrame,
        metric: str = "Median",
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
            "Proteome Discoverer": "#911eb4",
            "PEAKS": "#f032e6",
            "quantms": "#f5e830",
        },
        mapping: Dict[str, int] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "None",
        legend_name_map: Dict[str, str] = {
            "AlphaPept": "AlphaPept (legacy tool)",
        },
        hide_annot: bool = False,
    ) -> go.Figure:
        """
        Plot mean metrics in a scatter plot with Plotly, highlighting specific data points.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            The DataFrame containing benchmark metrics data.
        metric : str, optional
            The metric to plot, either "Median" or "Mean", by default "Median".
        software_colors : Dict[str, str], optional
            A dictionary mapping software names to their colors, by default predefined colors.
        mapping : Dict[str, int], optional
            A dictionary mapping categories to scatter plot sizes, by default {"old": 10, "new": 20}.
        highlight_color : str, optional
            The color used for highlighting certain points, by default "#d30067".
        label : str, optional
            The column name for labeling data points, by default "None".
        legend_name_map : Dict[str, str], optional
            A dictionary mapping software names to legend names, by default None.
            If None, the software names will be used as legend names.

        Returns
        -------
        go.Figure
            A Plotly figure object representing the scatter plot.
        """
        all_median_abs_epsilon = [
            v2["median_abs_epsilon"] for v in benchmark_metrics_df["results"] for v2 in v.values()
        ]
        all_mean_abs_epsilon = [v2["mean_abs_epsilon"] for v in benchmark_metrics_df["results"] for v2 in v.values()]
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

        if metric == "Median":
            layout_xaxis_range = [
                min(all_median_abs_epsilon) - min(all_median_abs_epsilon) * 0.05,
                max(all_median_abs_epsilon) + max(all_median_abs_epsilon) * 0.05,
            ]
            layout_xaxis_title = (
                "Median absolute difference between measured and expected log2-transformed fold change."
            )
        elif metric == "Mean":
            layout_xaxis_range = [
                min(all_mean_abs_epsilon) - min(all_mean_abs_epsilon) * 0.05,
                max(all_mean_abs_epsilon) + max(all_mean_abs_epsilon) * 0.05,
            ]
            layout_xaxis_title = "Mean absolute difference between measured and expected log2-transformed fold change."

        fig = go.Figure(
            layout_yaxis_range=[
                min(all_nr_prec) - min(max(all_nr_prec) * 0.05, 2000),
                max(all_nr_prec) + min(max(all_nr_prec) * 0.05, 2000),
            ],
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
            fig.add_trace(
                go.Scatter(
                    x=tmp_df["{}_abs_epsilon".format(metric.lower())],
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
                title=layout_xaxis_title,
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

    @staticmethod
    def plot_CV_violinplot(result_df: pd.DataFrame) -> go.Figure:
        """
        Plot the coefficient of variation (CV) for A and B groups using a violin plot.

        Parameters
        ----------
        result_df : pd.DataFrame
            The results DataFrame containing the CV data.

        Returns
        -------
        go.Figure:
            A Plotly figure object representing the violin plot.
        """
        fig = px.violin(result_df, y=["CV_A", "CV_B"], box=True, title=None, points=False)
        fig.update_layout(
            xaxis_title="Condition",
            yaxis_title="CV",
            xaxis=dict(linecolor="black"),  # Set the X axis line color to black
            yaxis=dict(linecolor="black"),  # Set the Y axis line color to black
        )

        return fig

    @staticmethod
    def plot_ma_plot(result_df: pd.DataFrame, species_ratio: Dict[str, Dict[str, str]]) -> go.Figure:
        """
        Plot a MA plot using Plotly.

        Parameters
        ----------
        result_df : pd.DataFrame
            The results DataFrame containing the MA plot data.
        species_ratio : Dict[str, Dict[str, str]]
            A dictionary mapping species to their respective colors and ratios.

        Returns
        -------
        go.Figure
            A Plotly figure object representing the MA plot.
        """
        color_map = {species: data["color"] for species, data in species_ratio.items()}

        # take mean of log intensity mean a and log intensity mean b
        result_df["logIntensityMean"] = (result_df["log_Intensity_mean_A"] + result_df["log_Intensity_mean_B"]) / 2

        fig = px.scatter(
            result_df,
            x="log2_A_vs_B",
            y="logIntensityMean",
            color="species",
            color_discrete_map=color_map,
            labels={"log2_A_vs_B": "log2_FC(A:B)", "logIntensityMean": "log2_Intensity_Mean", "species": "Organism"},
            title="log2FC vs logIntensityMean",
            size_max=10,
            opacity=0.6,
        )

        # Add vertical lines as shapes
        fig.add_shape(
            type="line",
            x0=0,
            x1=0,
            y0=result_df["logIntensityMean"].min(),
            y1=result_df["logIntensityMean"].max(),
            line=dict(color="green", dash="dash"),
            xref="x",
            yref="y",
            name="log2FC = 0",
        )
        fig.add_shape(
            type="line",
            x0=1,
            x1=1,
            y0=result_df["logIntensityMean"].min(),
            y1=result_df["logIntensityMean"].max(),
            line=dict(color="red", dash="dash"),
            xref="x",
            yref="y",
            name="log2FC = 1",
        )
        fig.add_shape(
            type="line",
            x0=-2,
            x1=-2,
            y0=result_df["logIntensityMean"].min(),
            y1=result_df["logIntensityMean"].max(),
            line=dict(color="blue", dash="dash"),
            xref="x",
            yref="y",
            name="log2FC = -2",
        )

        # To show vertical lines in the legend, add dummy traces
        fig.add_trace(
            go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="green", dash="dash"), name="log2FC = 0")
        )
        fig.add_trace(
            go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="red", dash="dash"), name="log2FC = 1")
        )
        fig.add_trace(
            go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="blue", dash="dash"), name="log2FC = -2")
        )

        fig.update_traces(marker=dict(size=6))  # Marker size approx. equivalent to s=10 in seaborn
        return fig
