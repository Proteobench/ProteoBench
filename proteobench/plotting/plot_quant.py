import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class PlotDataPoint:
    """
    A utility class for creating various plots to visualize benchmark results using Plotly.

    This class contains static methods for generating histograms, scatter plots, and violin plots
    to analyze and visualize data related to precursor ions, species ratios, and benchmark metrics.
    """

    @staticmethod
    def plot_fold_change_histogram(result_df: pd.DataFrame, species_ratio: dict) -> go.Figure:
        """
        Plots a histogram of log2 fold changes for different species.

        Parameters:
            result_df (pd.DataFrame): DataFrame containing the results, including log2 fold changes
                                      and species information.
            species_ratio (dict): Dictionary with expected species ratios and colors for plotting.

        Returns:
            go.Figure: A Plotly figure object with the histogram.
        """
        # Filter out precursors not associated with known species
        result_df = result_df[result_df[["YEAST", "ECOLI", "HUMAN"]].any(axis=1)]
        result_df["kind"] = result_df[["YEAST", "ECOLI", "HUMAN"]].apply(
            lambda x: ["YEAST", "ECOLI", "HUMAN"][np.argmax(x)], axis=1
        )

        # Map species to colors
        color_map = {species: data["color"] for species, data in species_ratio.items()}

        # Create the histogram
        fig = px.histogram(
            result_df,
            x=result_df["log2_A_vs_B"],
            color="kind",
            histnorm="probability density",
            barmode="overlay",
            opacity=0.7,
            nbins=100,
            color_discrete_map=color_map,
        )

        # Update figure layout
        fig.update_layout(
            width=700,
            height=700,
            xaxis=dict(title="log2_A_vs_B", color="white", gridwidth=2, linecolor="black"),
            yaxis=dict(linecolor="black"),
        )

        fig.update_yaxes(title="Density", color="white", gridwidth=2)
        fig.update_xaxes(range=[-4, 4], showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

        # Add vertical lines for expected ratios (log2-transformed)
        ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_ratio.items()}
        for species, log2_ratio in ratio_map.items():
            fig.add_vline(x=log2_ratio, line_dash="dash", line_color=color_map[species], annotation_text=species)

        # Add watermark annotation
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
        software_colors: dict = {
            "MaxQuant": "#377eb8",
            "AlphaPept": "#4daf4a",
            "ProlineStudio": "#e41a1c",
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
        },
        mapping={"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "None",
    ) -> go.Figure:
        """
        Plots a scatter plot of benchmark metrics.

        The x-axis represents the mean absolute difference between measured and expected log2 fold changes,
        and the y-axis represents the total number of quantified precursor ions.

        Parameters:
            benchmark_metrics_df (pd.DataFrame): DataFrame containing benchmark metrics.
            software_colors (dict): Mapping of software tools to their respective colors for plotting.
            mapping (dict): Mapping for point sizes based on the "old_new" column.
            highlight_color (str): Color used for highlighting specific points.
            label (str): Column name for labels to display on the scatter plot. Default is "None".

        Returns:
            go.Figure: A Plotly figure object with the scatter plot.
        """
        # Extract data for scatter plot ranges
        all_median_abs_epsilon = [
            v2["median_abs_epsilon"] for v in benchmark_metrics_df["results"] for v2 in v.values()
        ]
        all_nr_prec = [v2["nr_prec"] for v in benchmark_metrics_df["results"] for v2 in v.values()]

        # Add hover text for points
        hover_texts = []
        for idx, _ in benchmark_metrics_df.iterrows():
            datapoint_text = f"ProteoBench ID: {benchmark_metrics_df.id[idx]}<br>"
            datapoint_text += f"Software tool: {benchmark_metrics_df.software_name[idx]} {benchmark_metrics_df.software_version[idx]}<br>"
            if benchmark_metrics_df.is_temporary[idx]:
                datapoint_text += f"Comment (private submission): {benchmark_metrics_df.comments[idx]}"
            else:
                datapoint_text += f"Search engine: {benchmark_metrics_df.search_engine[idx]} {benchmark_metrics_df.search_engine_version[idx]}<br>"
            hover_texts.append(datapoint_text)

        # Define scatter sizes and colors
        scatter_size = [mapping[item] for item in benchmark_metrics_df["old_new"]]
        colors = [software_colors[software] for software in benchmark_metrics_df["software_name"]]

        # Assign updated data
        benchmark_metrics_df["color"] = colors
        benchmark_metrics_df["hover_text"] = hover_texts
        benchmark_metrics_df["scatter_size"] = scatter_size

        fig = go.Figure()

        # Plot data points grouped by software tool
        color_software_combinations = benchmark_metrics_df[["color", "software_name"]].drop_duplicates()
        for _, row in color_software_combinations.iterrows():
            tmp_df = benchmark_metrics_df[
                (benchmark_metrics_df["color"] == row["color"])
                & (benchmark_metrics_df["software_name"] == row["software_name"])
            ]
            fig.add_trace(
                go.Scatter(
                    x=tmp_df["median_abs_epsilon"],
                    y=tmp_df["nr_prec"],
                    mode="markers" if label == "None" else "markers+text",
                    hovertext=tmp_df["hover_text"],
                    text=tmp_df[label] if label != "None" else None,
                    marker=dict(color=tmp_df["color"], showscale=False),
                    marker_size=tmp_df["scatter_size"],
                    name=row["software_name"],
                )
            )

        fig.update_layout(
            xaxis=dict(
                title="Mean absolute difference between measured and expected log2-transformed fold change",
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
            ),
            yaxis=dict(
                title="Total number of precursor ions quantified in the selected raw files",
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
            ),
        )

        return fig

    @staticmethod
    def plot_CV_violinplot(result_df: pd.DataFrame) -> go.Figure:
        """
        Plots a violin plot for the coefficient of variation (CV) of groups A and B.

        Parameters:
            result_df (pd.DataFrame): DataFrame containing CV data for groups A and B.

        Returns:
            go.Figure: A Plotly figure object with the violin plot.
        """
        fig = px.violin(result_df, y=["CV_A", "CV_B"], box=True, title=None, points=False)
        fig.update_layout(
            xaxis_title="Group",
            yaxis_title="CV",
            xaxis=dict(linecolor="black"),  # Set the X axis line color to black
            yaxis=dict(linecolor="black"),  # Set the Y axis line color to black
        )

        return fig
