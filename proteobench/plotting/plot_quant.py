from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class PlotDataPoint:
    @staticmethod
    def plot_fold_change_histogram(result_df: pd.DataFrame, species_ratio: Dict[str, Dict[str, str]]) -> go.Figure:
        """
        Plot a histogram of log2 fold changes using Plotly, color-coded by species.

        Args:
            result_df (pd.DataFrame): The results DataFrame containing fold changes and species data.
            species_ratio (Dict[str, Dict[str, str]]): A dictionary mapping species to their respective colors and ratios.

        Returns:
            go.Figure: A Plotly figure object representing the histogram.
        """
        # Filter data to include only known species
        result_df = result_df[result_df[["YEAST", "ECOLI", "HUMAN"]].any(axis=1)]
        result_df["kind"] = result_df[["YEAST", "ECOLI", "HUMAN"]].apply(
            lambda x: ["YEAST", "ECOLI", "HUMAN"][np.argmax(x)], axis=1
        )

        # Map colors based on species ratio
        color_map = {species: data["color"] for species, data in species_ratio.items()}

        fig = px.histogram(
            result_df,
            x="log2_A_vs_B",
            color="kind",
            histnorm="probability density",
            barmode="overlay",
            opacity=0.7,
            nbins=100,
            color_discrete_map=color_map,
        )

        fig.update_layout(
            width=700,
            height=700,
            xaxis=dict(title="log2_A_vs_B", color="white", gridwidth=2, linecolor="black"),
            yaxis=dict(linecolor="black"),
        )

        fig.update_yaxes(title="Density", color="white", gridwidth=2)
        fig.update_xaxes(range=[-4, 4])
        fig.update_xaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

        # Add vertical lines for expected ratios (log2 transformed)
        ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_ratio.items()}
        for species, ratio in ratio_map.items():
            fig.add_vline(x=ratio, line_dash="dash", line_color=color_map[species], annotation_text=species)

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text="-Beta-",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        return fig

    @staticmethod
    def plot_metric(
        benchmark_metrics_df: pd.DataFrame,
        metric: str = "Median",
        software_colors: Dict[str, str] = {
            "MaxQuant": "#377eb8",
            "AlphaPept": "#4daf4a",
            "ProlineStudio": "#5f0f40",
            "MSAngel": "#e41a1c",
            "FragPipe": "#ff7f00",
            "i2MassChroQ": "#984ea3",
            "Sage": "#a65628",
            "WOMBAT": "#f781bf",
            "DIA-NN": "#8c564b",
            "AlphaDIA": "#4daf4a",
            "Custom": "#7f7f7f",
            "Spectronaut": "#bcbd22",
            "FragPipe (DIA-NN quant)": "#ff7f00",
            "MSAID": "#afff57",
            "Proteome Discoverer": "#8c564b",
            "PEAKS": "#f781bf",
        },
        mapping: Dict[str, int] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "None",
    ) -> go.Figure:
        """
        Plot mean metrics in a scatter plot with Plotly, highlighting specific data points.

        Args:
            benchmark_metrics_df (pd.DataFrame): The DataFrame containing benchmark metrics data.
            software_colors (Dict[str, str], optional): A dictionary mapping software names to their colors. Defaults to predefined colors.
            mapping (Dict[str, int], optional): A dictionary mapping categories to scatter plot sizes. Defaults to {"old": 10, "new": 20}.
            highlight_color (str, optional): The color used for highlighting certain points. Defaults to "#d30067".
            label (str, optional): The column name for labeling data points. Defaults to "None".

        Returns:
            go.Figure: A Plotly figure object representing the scatter plot.
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
                    datapoint_text = (
                        datapoint_text + f"Comment (private submission): {benchmark_metrics_df.comments[idx]}"
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
                    datapoint_text = (
                        datapoint_text + f"Comment (public submission): {benchmark_metrics_df.submission_comments[idx]}"
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
                    name=tmp_df["software_name"].iloc[0],
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
            text="-Beta-",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        fig.update_layout(clickmode="event+select")

        return fig

    @staticmethod
    def plot_CV_violinplot(result_df: pd.DataFrame) -> go.Figure:
        """
        Plot the coefficient of variation (CV) for A and B groups using a violin plot.

        Args:
            result_df (pd.DataFrame): The DataFrame containing the CV values for A and B.

        Returns:
            go.Figure: A Plotly figure object representing the violin plot.
        """
        fig = px.violin(result_df, y=["CV_A", "CV_B"], box=True, title=None, points=False)
        fig.update_layout(
            xaxis_title="Group",
            yaxis_title="CV",
            xaxis=dict(linecolor="black"),  # Set the X axis line color to black
            yaxis=dict(linecolor="black"),  # Set the Y axis line color to black
        )

        return fig
