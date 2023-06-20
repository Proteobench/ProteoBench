import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events


# ! This class does not use any instance attributes.
class PlotDataPoint:
    def plot_bench(self, result_df: pd.DataFrame) -> go.Figure:
        """Plot results with Plotly Express."""

        hist_data = [
            np.array(result_df[result_df["YEAST"] == True]["1|2_ratio"]),
            np.array(result_df[result_df["HUMAN"] == True]["1|2_ratio"]),
            np.array(result_df[result_df["ECOLI"] == True]["1|2_ratio"]),
        ]
        group_labels = [
            "YEAST",
            "HUMAN",
            "ECOLI",
        ]

        fig = ff.create_distplot(hist_data, group_labels, show_hist=False)

        fig.update_layout(
            width=700,
            height=700,
            title="Distplot",
            xaxis=dict(
                title="1|2_ratio",
                color="white",
                gridwidth=2,
            ),
            yaxis=dict(
                title="Density",
                color="white",
                gridwidth=2,
            ),
        )
        fig.update_xaxes(range=[0, 4])

        return fig

    def plot_metric(self, benchmark_metrics_df: pd.DataFrame) -> go.Figure:
        """
        Plot mean metrics in a scatterplot with plotly.

        x = median absolute precentage error between all measured and expected ratio
        y = total number of precursors quantified in all raw files

        Input: meta_data


        Return: Plotly figure object

        """

        # Define search colors for each search engine
        search_engine_colors = {
            "MaxQuant": "midnightblue",
            "AlphaPept": "grey",
            "MSFragger": "orange",
            "WOMBAT": "firebrick",
        }

        # Color plot based on search engine
        colors = [
            search_engine_colors[engine]
            for engine in benchmark_metrics_df["search_engine"]
        ]

        # Add hover text
        hover_texts = [
            f"Search Engine: {benchmark_metrics_df.search_engine[idx]} {benchmark_metrics_df.software_version[idx]}<br>MBR: {benchmark_metrics_df.MBR[idx]}<br>Precursor Tolerance: {benchmark_metrics_df.precursor_tol[idx]} {benchmark_metrics_df.precursor_tol_unit[idx]}<br>Fragment Tolerance: {benchmark_metrics_df.fragment_tol_unit[idx]}<br>Enzyme: {benchmark_metrics_df.enzyme_name[idx]} <br>Missed Cleavages: {benchmark_metrics_df.missed_cleavages[idx]}<br>FDR psm: {benchmark_metrics_df.fdr_psm[idx]}<br>FDR Peptide: {benchmark_metrics_df.fdr_peptide[idx]}<br>FRD Protein: {benchmark_metrics_df.fdr_protein[idx]}"
            for idx, row in benchmark_metrics_df.iterrows()
        ]

        #  spellerror {meta_data.fragmnent_tol[idx]}

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=benchmark_metrics_df["weighted_sum"],
                    y=benchmark_metrics_df["nr_prec"],
                    mode="markers",
                    text=hover_texts,
                    marker=dict(color=colors, showscale=True, size=20),
                )
            ]
        )

        fig.update_layout(
            title="Metric",
            width=700,
            height=700,
            xaxis=dict(
                title="Median absolute precentage error between all measured ratios and expected ratio",
                gridcolor="white",
                gridwidth=2,
            ),
            yaxis=dict(
                title="Total number of precursors quantified in all raw files",
                gridcolor="white",
                gridwidth=2,
            ),
        )

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
