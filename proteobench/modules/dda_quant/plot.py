import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
            x=np.log2(result_df["1|2_ratio"]),
            color="kind",
            marginal="rug",
            histnorm="probability density",
            barmode="overlay",
            opacity=0.7,
            nbins=100
        )

        fig.update_layout(
            width=700,
            height=700,
            # title="Distplot",
            xaxis=dict(
                title="1|2_ratio",
                color="white",
                gridwidth=2))
          
        fig.update_yaxes(title="Density",
                color="white",
                gridwidth=2)
        
        fig.update_layout(
            width=700,
            height=700
        )

        fig.update_xaxes(range=[-4, 4])
        fig.update_xaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

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
            "MaxQuant": "#1f77b4",
            "AlphaPept": "#2ca02c",
            "MSFragger": "#ff7f0e",
            "WOMBAT": "#7f7f7f",
            "Proline": "#d62728",
            "Sage": "#f74c00",
            "Custom": "#9467bd",
        }

        # Color plot based on search engine
        colors = [
            search_engine_colors[engine]
            for engine in benchmark_metrics_df["search_engine"]
        ]

        # Add hover text
        hover_texts = [
            f"Search Engine: {benchmark_metrics_df.search_engine[idx]} {benchmark_metrics_df.software_version[idx]}<br>"
            + f"FDR psm: {benchmark_metrics_df.fdr_psm[idx]}<br>"
            + f"FDR Peptide: {benchmark_metrics_df.fdr_peptide[idx]}<br>"
            + f"FRD Protein: {benchmark_metrics_df.fdr_protein[idx]}<br>"
            + f"MBR: {benchmark_metrics_df.MBR[idx]}<br>"
            + f"Precursor Tolerance: {benchmark_metrics_df.precursor_tol[idx]} {benchmark_metrics_df.precursor_tol_unit[idx]}<br>"
            + f"Fragment Tolerance: {benchmark_metrics_df.fragment_tol_unit[idx]}<br>"
            + f"Enzyme: {benchmark_metrics_df.enzyme_name[idx]} <br>"
            + f"Missed Cleavages: {benchmark_metrics_df.missed_cleavages[idx]}<br>"
            + f"Min peptide length: {benchmark_metrics_df.min_pep_length[idx]}<br>"
            + f"Max peptide length: {benchmark_metrics_df.max_pep_length[idx]}"
            for idx, row in benchmark_metrics_df.iterrows()
        ]


        mapping = {"old": 10, "new": 20}

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=benchmark_metrics_df["weighted_sum"],
                    y=benchmark_metrics_df["nr_prec"],
                    mode="markers",
                    text=hover_texts,
                    marker=dict(color=colors, showscale=False, size=20),
                    marker_size=[
                        mapping[item] for item in benchmark_metrics_df["old_new"]
                    ],
                )
            ]
        )

        fig.update_layout(
            # title="Metric",
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
