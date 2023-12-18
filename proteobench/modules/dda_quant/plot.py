import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events


# ! This class does not use any instance attributes.
class PlotDataPoint:
    def plot_bench(self, result_df: pd.DataFrame) -> go.Figure:
        """Plot results with Plotly Express."""

        # Remove any precursors not arising from a known organism... contaminants?
        result_df = result_df[result_df[["YEAST", "ECOLI", "HUMAN"]].any(axis=1)]
        result_df["kind"] = result_df[["YEAST", "ECOLI", "HUMAN"]].apply(
            lambda x: ["YEAST", "ECOLI", "HUMAN"][np.argmax(x)], axis=1
        )
        fig = px.histogram(
            result_df,
            x=result_df["log2_A_vs_B"],
            color="kind",
            marginal="rug",
            histnorm="probability density",
            barmode="overlay",
            opacity=0.7,
            nbins=100,
        )

        fig.update_layout(
            width=700,
            height=700,
            # title="Distplot",
            xaxis=dict(title="log2_A_vs_B", color="white", gridwidth=2),
        )

        fig.update_yaxes(title="Density", color="white", gridwidth=2)

        fig.update_layout(width=700, height=700)

        fig.update_xaxes(range=[-4, 4])
        fig.update_xaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

        return fig

    def plot_metric(self, benchmark_metrics_df: pd.DataFrame) -> go.Figure:
        """
        Plot mean metrics in a scatterplot with plotly.

        x = Mean absolute difference between measured and expected log2-transformed fold change
        y = total number of precursors quantified in all raw files

        Input: meta_data


        Return: Plotly figure object

        """

        # Define search colors for each search engine
        software_colors = {
            "MaxQuant": "#1f77b4",
            "AlphaPept": "#2ca02c",
            "FragPipe": "#ff7f0e",
            "WOMBAT": "#7f7f7f",
            "Proline": "#d62728",
            "Sage": "#f74c00",
            "Custom": "#9467bd",
        }

        # Color plot based on software tool
        colors = [software_colors[software] for software in benchmark_metrics_df["software_name"]]

        # Add hover text
        hover_texts = [
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
            + f"Max peptide length: {benchmark_metrics_df.max_peptide_length[idx]}"
            for idx, row in benchmark_metrics_df.iterrows()
        ]

        mapping = {"old": 10, "new": 20}

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=benchmark_metrics_df["median_abs_epsilon"],
                    y=benchmark_metrics_df["nr_prec"],
                    mode="markers",
                    text=hover_texts,
                    marker=dict(color=colors, showscale=False, size=20),
                    marker_size=[mapping[item] for item in benchmark_metrics_df["old_new"]],
                )
            ]
        )

        fig.update_layout(
            # title="Metric",
            width=700,
            height=700,
            xaxis=dict(
                title="Mean absolute difference between measured and expected log2-transformed fold change",
                gridcolor="white",
                gridwidth=2,
            ),
            yaxis=dict(
                title="Total number of precursors quantified in all raw files",
                gridcolor="white",
                gridwidth=2,
            ),
            # paper_bgcolor='rgb(243, 243, 243)',
            # plot_bgcolor="rgb(243, 243, 243)",
        )
        fig.update_xaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        # selected_points = plotly_events(
        #    fig,
        #    select_event=True,
        #    key='Smth'
        # )

        # if len(selected_points) == 0:
        #    st.warning('Please select a data point')
        # else:
        #    st.write(selected_points)

        return fig
