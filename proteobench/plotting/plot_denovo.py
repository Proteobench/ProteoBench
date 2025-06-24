"""
Module for plotting results of de novo models
"""

from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def flatten_results_column(df):

    results = {
        "engine": [],
        "peptide_mass_precision": [],
        "peptide_mass_recall": [],
        "peptide_mass_coverage": [],
        "peptide_exact_precision": [],
        "peptide_exact_recall": [],
        "peptide_exact_coverage": [],
        "aa_mass_precision": [],
        "aa_mass_recall": [],
        "aa_mass_coverage": [],
        "aa_exact_precision": [],
        "aa_exact_recall": [],
        "aa_exact_coverage": [],
    }
    for i, row in df.iterrows():
        results['engine'].append(row['software_name'])

        results['peptide_mass_precision'].append(row['results']['peptide']['mass']['precision'])
        results['peptide_mass_recall'].append(row['results']['peptide']['mass']['recall'])
        results['peptide_mass_coverage'].append(row['results']['peptide']['mass']['coverage'])

        results['peptide_exact_precision'].append(row['results']['peptide']['exact']['precision'])
        results['peptide_exact_recall'].append(row['results']['peptide']['exact']['recall'])
        results['peptide_exact_coverage'].append(row['results']['peptide']['exact']['coverage'])

        results['aa_mass_precision'].append(row['results']['aa']['mass']['precision'])
        results['aa_mass_recall'].append(row['results']['aa']['mass']['recall'])
        results['aa_mass_coverage'].append(row['results']['aa']['mass']['coverage'])

        results['aa_exact_precision'].append(row['results']['aa']['exact']['precision'])
        results['aa_exact_recall'].append(row['results']['aa']['exact']['recall'])
        results['aa_exact_coverage'].append(row['results']['aa']['exact']['coverage'])
    return pd.DataFrame(results)


class PlotDataPoint:
    """
    Class for plotting data points.
    """

    @staticmethod
    def plot_metric(
        benchmark_metrics_df: pd.DataFrame,
        level: str = "peptide",
        evaluation_type: str = "mass",
        software_colors: Dict[str, str] = {
            "AdaNovo": "#8b26ff",
            "Casanovo": "#8bc6fd",
            "DeepNovo": "#108E2E",
            "PepNet": "#F89008",
            "Pi-HelixNovo": "#E43924",
            "Pi-PrimeNovo": "#663200",
            "PEAKS": "#f032e6",
        },
        mapping: Dict[str, int] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "None",
    ) -> go.Figure:
        
        # Define layout
        results_df = flatten_results_column(benchmark_metrics_df)
        benchmark_metrics_df = pd.concat([benchmark_metrics_df, results_df], axis=1)
        results_min = results_df.min()
        results_max = results_df.max()

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
                    + f"Model checkpoint: {benchmark_metrics_df.checkpoint[idx]}<br>"
                    + f"Number of Beams: {benchmark_metrics_df.n_beams[idx]}<br>"
                    + f"Decoding Strategy: {benchmark_metrics_df.decoding_strategy[idx]}<br>"
                    + f"Precursor Tolerance: {benchmark_metrics_df.precursor_mass_tolerance[idx]}<br>"
                    + f"Tolerance for precursor removal: {benchmark_metrics_df.remove_precursor_tol[idx]}<br>"
                    + f"Number of peaks: {benchmark_metrics_df.n_peaks[idx]} <br>"
                    + f"Min mz: {benchmark_metrics_df.min_mz[idx]}<br>"
                    + f"Max mz: {benchmark_metrics_df.max_mz[idx]}<br>"
                    + f"Min peptide length: {benchmark_metrics_df.min_peptide_length[idx]}<br>"
                    + f"Max peptide length: {benchmark_metrics_df.max_peptide_length[idx]}<br>"
                    + f"Min intensity: {benchmark_metrics_df.min_intensity[idx]}<br>"
                    + f"Max intensity: {benchmark_metrics_df.max_intensity[idx]}<br>"
                    + f"Max precursor charge: {benchmark_metrics_df.max_precursor_charge[idx]}<br>"
                    + f"Isotope error range: {benchmark_metrics_df.isotope_error_range[idx]}<br>"
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

        layout_xaxis_range = [
            results_min[f"{level}_{evaluation_type}_coverage"] - results_min[f"{level}_{evaluation_type}_coverage"] * .05,
            results_max[f"{level}_{evaluation_type}_coverage"] + results_max[f"{level}_{evaluation_type}_coverage"] * .05
        ]
        layout_yaxis_range = [
            results_min[f"{level}_{evaluation_type}_precision"] - results_min[f"{level}_{evaluation_type}_precision"] * .05,
            results_max[f"{level}_{evaluation_type}_precision"] + results_max[f"{level}_{evaluation_type}_precision"] * .05
        ]
        layout_xaxis_title = (
            "Coverage"
        )
        layout_yaxis_title = (
            "Precision"
        )
        
        fig = go.Figure(
            layout_yaxis_range=layout_yaxis_range,
            layout_xaxis_range=layout_xaxis_range,
        )

        # Get all unique color-software combinations (necessary for highlighting)
        color_software_combinations = benchmark_metrics_df[["color", "software_name"]].drop_duplicates()

        # plot the data points, one trace per software tool
        for _, row in color_software_combinations.iterrows():
            color = row["color"]
            software = row["software_name"]

            tmp_df = benchmark_metrics_df[
                (benchmark_metrics_df["color"] == color) & (benchmark_metrics_df["software_name"] == software)
            ]

            fig.add_trace(
                go.Scatter(
                    x=tmp_df[f"{level}_{evaluation_type}_coverage"],
                    y=tmp_df[f"{level}_{evaluation_type}_precision"],
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
                title=layout_yaxis_title,
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
    
    def plot_ptm_overview(
            self,
            benchmark_metrics_df: pd.DataFrame,
            mod_labels: List[str],
            software_colors: Dict[str, str] = {
                "AdaNovo": "#8b26ff",
                "Casanovo": "#8bc6fd",
                "DeepNovo": "#108E2E",
                "PepNet": "#F89008",
                "Pi-HelixNovo": "#E43924",
                "Pi-PrimeNovo": "#663200",
                "PEAKS": "#f032e6",
            }
        ):
        
        fig = go.Figure()
        for i, row in benchmark_metrics_df.iterrows():
            x, y = self.get_modification_scores(
                row['results']['in_depth']['PTM'],
                mod_labels=mod_labels
            )
            tool = row['software_name']

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode='lines+markers',
                    name=tool,
                    marker=dict(color=software_colors[tool])
                )
            )
        
        fig.update_layout(
            width=700,
            height=400,
            xaxis=dict(title="Modification", color="black", gridwidth=2, linecolor="black"),
            yaxis=dict(linecolor="black")
        )
        fig.update_yaxes(title="Precision", color="black", gridwidth=2)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

        return fig

    def plot_ptm_specific(
            self,
            benchmark_metrics_df,
            mod_label,
            software_colors: Dict[str, str] = {
                "AdaNovo": "#8b26ff",
                "Casanovo": "#8bc6fd",
                "DeepNovo": "#108E2E",
                "PepNet": "#F89008",
                "Pi-HelixNovo": "#E43924",
                "Pi-PrimeNovo": "#663200",
                "PEAKS": "#f032e6",
            }
        ):
        fig = go.Figure()
        for i, row in benchmark_metrics_df.iterrows():
            ptm_data = row['results']['in_depth']['PTM']
            x = ptm_data[mod_label]['correct_gt'] / (ptm_data[mod_label]['counts_gt']+.0001)
            y = ptm_data[mod_label]['correct_dn'] / (ptm_data[mod_label]['counts_dn']+.0001)
            tool = row['software_name']
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    name=tool,
                    marker=dict(color=software_colors[tool])
                )
            )
        
        fig.update_layout(
            width=500,
            height=500,
            xaxis=dict(title="Precision (Ground-truth)", color='black', gridwidth=2),
            yaxis=dict(title="Precision (denovo)", color='black', gridwidth=2)
        )

        return fig


    @staticmethod
    def get_modification_scores(mod_dict, mod_labels):
        x = []
        y = []

        for mod_label in mod_labels:
            x.append(mod_label)
            y.append(
                mod_dict[mod_label]['correct_gt'] / mod_dict[mod_label]['counts_gt'] + .0001
            )
        return x, y


    def plot_spectrum_feature(
            self,
            benchmark_metrics_df,
            feature,
            evaluation_type='mass',
            software_colors={
                "AdaNovo": "#8b26ff",
                "Casanovo": "#8bc6fd",
                "DeepNovo": "#108E2E",
                "PepNet": "#F89008",
                "Pi-HelixNovo": "#E43924",
                "Pi-PrimeNovo": "#663200",
                "PEAKS": "#f032e6",
                'test': 'black'
            }
    ):
        fig = go.Figure()


        for i, row in benchmark_metrics_df.iterrows():
            data = row['results']['in_depth']['Spectrum'][feature]
            x = []
            y = []
            for k, v in data.items():
                x.append(k)
                y.append(v[evaluation_type])

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    name=row['software_name'],
                    marker=dict(color=software_colors[row['software_name']]),
                    mode='lines+markers'
                )
        )
            
        fig.update_layout(
            width=500,
            height=500,
            xaxis=dict(title=f"{feature}", color='black', gridwidth=2),
            yaxis=dict(title="Precision", color='black', gridwidth=2)
        )
        return fig