"""
Module for plotting results of de novo models
"""

from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from proteobench.plotting.plot_generator_base import PlotGeneratorBase

EPSILON = 0.0001


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
        results["engine"].append(row["software_name"])

        results["peptide_mass_precision"].append(row["results"]["peptide"]["mass"]["precision"])
        results["peptide_mass_recall"].append(row["results"]["peptide"]["mass"]["recall"])
        results["peptide_mass_coverage"].append(row["results"]["peptide"]["mass"]["coverage"])

        results["peptide_exact_precision"].append(row["results"]["peptide"]["exact"]["precision"])
        results["peptide_exact_recall"].append(row["results"]["peptide"]["exact"]["recall"])
        results["peptide_exact_coverage"].append(row["results"]["peptide"]["exact"]["coverage"])

        results["aa_mass_precision"].append(row["results"]["aa"]["mass"]["precision"])
        results["aa_mass_recall"].append(row["results"]["aa"]["mass"]["recall"])
        results["aa_mass_coverage"].append(row["results"]["aa"]["mass"]["coverage"])

        results["aa_exact_precision"].append(row["results"]["aa"]["exact"]["precision"])
        results["aa_exact_recall"].append(row["results"]["aa"]["exact"]["recall"])
        results["aa_exact_coverage"].append(row["results"]["aa"]["exact"]["coverage"])
    return pd.DataFrame(results)


class DeNovoPlotGenerator(PlotGeneratorBase):
    """
    Plot generator for de novo sequencing data points.
    Implements the PlotGeneratorBase interface for consistent module plotting.
    """

    def plot_main_metric(self, result_df: pd.DataFrame, **kwargs) -> go.Figure:
        """
        Generate the main performance metric plot.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot.
        **kwargs : dict
            Additional parameters:
            - level: str (default "precision") - metric type ("precision" or "recall")
            - evaluation_type: str (default "mass") - evaluation type ("mass" or "exact")
            - colorblind_mode: bool (default False) - whether to use different shapes for software tools
            - software_colors: Dict[str, str] - color mapping for software tools
            - software_markers: Dict[str, str] - marker mapping for software tools (used when colorblind_mode is True)
            - mapping: Dict[str, int] - size mapping for old/new datapoints
            - highlight_color: str - color for highlighted datapoints
            - label: str - label field to display

        Returns
        -------
        go.Figure
            The generated plotly figure for the main performance metric.
        """
        # Extract parameters from kwargs with defaults
        level = kwargs.get("level", "precision")
        evaluation_type = kwargs.get("evaluation_type", "mass")
        colorblind_mode = kwargs.get("colorblind_mode", False)
        software_colors = kwargs.get(
            "software_colors",
            {
                "AdaNovo": "#88ccef",
                "Casanovo": "#cc6777",
                "DeepNovo": "#ddcc77",
                "PepNet": "#147733",
                "Pi-HelixNovo": "#342288",
                "Pi-PrimeNovo": "#aa4599",
                "PEAKS": "#671100",
            },
        )
        software_markers = kwargs.get(
            "software_markers",
            {
                "AdaNovo": "circle",
                "Casanovo": "square",
                "DeepNovo": "diamond",
                "PepNet": "cross",
                "Pi-HelixNovo": "x",
                "Pi-PrimeNovo": "triangle-up",
                "PEAKS": "star",
            },
        )
        mapping = kwargs.get("mapping", {"old": 10, "new": 20})
        highlight_color = kwargs.get("highlight_color", "#d30067")
        label = kwargs.get("label", "None")

        # Use result_df as the main dataframe (renamed from benchmark_metrics_df)
        benchmark_metrics_df = result_df

        # Define layout
        benchmark_metrics_df = benchmark_metrics_df.reset_index(drop=True)
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

        # Set markers based on software tool (if colorblind mode is enabled)
        markers = [software_markers[software] for software in benchmark_metrics_df["software_name"]]

        benchmark_metrics_df["color"] = colors
        benchmark_metrics_df["hover_text"] = hover_texts
        benchmark_metrics_df["scatter_size"] = scatter_size

        if colorblind_mode:
            benchmark_metrics_df["marker"] = markers
        else:
            benchmark_metrics_df["marker"] = "circle"

        layout_xaxis_range = [
            results_min[f"peptide_{evaluation_type}_{level}"]
            - results_min[f"peptide_{evaluation_type}_{level}"] * 0.05,
            results_max[f"peptide_{evaluation_type}_{level}"]
            + results_max[f"peptide_{evaluation_type}_{level}"] * 0.05,
        ]
        layout_yaxis_range = [
            results_min[f"aa_{evaluation_type}_{level}"] - results_min[f"aa_{evaluation_type}_{level}"] * 0.05,
            results_max[f"aa_{evaluation_type}_{level}"] + results_max[f"aa_{evaluation_type}_{level}"] * 0.05,
        ]
        layout_xaxis_title = f"Peptide {level.capitalize()}"
        layout_yaxis_title = f"Amino Acid {level.capitalize()}"

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
                    x=tmp_df[f"peptide_{evaluation_type}_{level}"],
                    y=tmp_df[f"aa_{evaluation_type}_{level}"],
                    mode="markers" if label == "None" else "markers+text",
                    hovertext=tmp_df["hover_text"],
                    text=tmp_df[label] if label != "None" else None,
                    marker=dict(
                        color=tmp_df["color"],
                        showscale=False,
                        symbol=tmp_df["marker"].iloc[0] if colorblind_mode else "circle",
                    ),
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
            text="-Alpha-",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        fig.update_layout(clickmode="event+select")

        return fig

    def generate_in_depth_plots(
        self, performance_data: pd.DataFrame, parse_settings: any = None, **kwargs
    ) -> Dict[str, go.Figure]:
        """
        Generate module-specific in-depth plots.

        Parameters
        ----------
        performance_data : pd.DataFrame
            The performance data to plot.
        parse_settings : any, optional
            Parse settings for the module (not used by de novo, included for signature compatibility).
        **kwargs : dict
            Additional parameters:
            - mod_labels: List[str] - list of PTM modification labels
            - mod_label: str - specific PTM label for detailed plot
            - feature: str - spectrum feature to plot
            - evaluation_type: str - evaluation type ("mass" or "exact")

        Returns
        -------
        Dict[str, go.Figure]
            Dictionary mapping plot names to plotly figures.
        """
        plots = {}

        # Extract parameters with defaults
        mod_labels = kwargs.get(
            "mod_labels",
            [
                "M-Oxidation",
                "Q-Deamidation",
                "N-Deamidation",
                "N-term Acetylation",
                "N-term Carbamylation",
                "N-term Ammonia-loss",
            ],
        )
        features = kwargs.get("features", ["Missing Fragmentation Sites", "Peptide Length", "% Explained Intensity"])
        evaluation_types = kwargs.get("evaluation_type", ["mass", "exact"])
        software_colors = kwargs.get(
            "software_colors",
            {
                "AdaNovo": "#88ccef",
                "Casanovo": "#cc6777",
                "DeepNovo": "#ddcc77",
                "PepNet": "#147733",
                "Pi-HelixNovo": "#342288",
                "Pi-PrimeNovo": "#aa4599",
                "PEAKS": "#671100",
            },
        )

        # Generate PTM plots
        plots["ptm_overview"] = self.plot_ptm_overview(
            performance_data, mod_labels=mod_labels, software_colors=software_colors
        )

        plots["ptm_specific"] = {}
        for mod_label in mod_labels:
            plots["ptm_specific"][mod_label] = self.plot_ptm_specific(
                performance_data, mod_label=mod_label, software_colors=software_colors
            )

        # Generate spectrum feature plot
        plots["spectrum_feature"] = {}
        for feature in features:
            plots["spectrum_feature"][feature] = {}
            for evaluation_type in evaluation_types:
                plots["spectrum_feature"][feature][evaluation_type] = self.plot_spectrum_feature(
                    performance_data, feature=feature, evaluation_type=evaluation_type, software_colors=software_colors
                )

        # Generate species plot
        plots["species_overview"] = {}
        for evaluation_type in evaluation_types:
            plots["species_overview"][evaluation_type] = self.plot_species_overview(
                performance_data, evaluation_type=evaluation_type, software_colors=software_colors
            )

        return plots

    def get_in_depth_plot_layout(self) -> list:
        """
        Define the layout configuration for displaying plots.

        Returns
        -------
        list
            List of plot configurations for organizing the UI display.
        """
        return [
            {"plots": ["ptm_overview", "ptm_specific"], "columns": 1, "title": "PTM Analysis"},
            {"plots": ["spectrum_feature"], "columns": 1, "title": "Spectrum Features"},
            {"plots": ["species_overview"], "columns": 1, "title": "Species Analysis"},
        ]

    def get_in_depth_plot_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for each in-depth plot.

        Returns
        -------
        Dict[str, str]
            Dictionary mapping plot names to their descriptions.
        """
        return {
            "ptm_overview": "Overview of precision across different post-translational modifications (PTMs). "
            "Shows how well each tool identifies modified amino acids.",
            "ptm_specific": "Detailed analysis of a specific PTM, comparing precision between ground truth "
            "and de novo predictions.",
            "spectrum_feature": "Analysis of precision relative to spectrum features such as missing "
            "fragmentation sites, peptide length, or explained intensity.",
            "species_overview": "Breakdown of precision across different species in the dataset.",
        }

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
        },
    ):
        fig = go.Figure()
        for i, row in benchmark_metrics_df.iterrows():
            x, y = self.get_modification_scores(row["results"]["in_depth"]["PTM"], mod_labels=mod_labels)
            tool = row["software_name"]

            fig.add_trace(
                go.Scatter(x=x, y=y, mode="lines+markers", name=tool, marker=dict(color=software_colors[tool]))
            )

        fig.update_layout(
            width=700,
            height=400,
            xaxis=dict(title="Modification", color="black", gridwidth=2, linecolor="black"),
            yaxis=dict(linecolor="black"),
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
        },
    ):
        fig = go.Figure()
        for i, row in benchmark_metrics_df.iterrows():
            ptm_data = row["results"]["in_depth"]["PTM"]

            # To make division by 0 impossible

            x = ptm_data[mod_label]["correct_gt"] / (ptm_data[mod_label]["counts_gt"] + EPSILON)
            y = ptm_data[mod_label]["correct_dn"] / (ptm_data[mod_label]["counts_dn"] + EPSILON)
            tool = row["software_name"]
            fig.add_trace(go.Scatter(x=[x], y=[y], name=tool, marker=dict(color=software_colors[tool])))

        fig.update_layout(
            width=500,
            height=500,
            xaxis=dict(title="Precision (Ground-truth)", color="black", gridwidth=2),
            yaxis=dict(title="Precision (denovo)", color="black", gridwidth=2),
        )

        return fig

    @staticmethod
    def get_modification_scores(mod_dict, mod_labels):
        x = []
        y = []

        for mod_label in mod_labels:
            x.append(mod_label)
            y.append(mod_dict[mod_label]["correct_gt"] / mod_dict[mod_label]["counts_gt"] + EPSILON)
        return x, y

    def plot_spectrum_feature(
        self,
        benchmark_metrics_df,
        feature,
        evaluation_type="mass",
        software_colors={
            "AdaNovo": "#8b26ff",
            "Casanovo": "#8bc6fd",
            "DeepNovo": "#108E2E",
            "PepNet": "#F89008",
            "Pi-HelixNovo": "#E43924",
            "Pi-PrimeNovo": "#663200",
            "PEAKS": "#f032e6",
            "test": "black",
        },
    ):
        # Create a subplot with 2 rows, shared x-axis
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.8, 0.2],
            vertical_spacing=0,
            subplot_titles=(f"{feature} vs Precision", None),
        )
        if len(benchmark_metrics_df) == 0:
            fig.add_trace(go.Scatter())
            fig.add_trace(go.Bar())
            fig.update_layout(
                height=600,
                width=600,
                xaxis=dict(title=None, color="black"),
                yaxis=dict(title="Precision", color="black"),
                xaxis2=dict(title=f"{feature}", color="black"),
                yaxis2=dict(title="Number of Spectra", color="black"),
                margin=dict(t=50),
            )
            fig.update_yaxes(
                autorange="reversed",
                # tickvals=[-v for v in sorted(set(df['y_bar']))],
                # ticktext=[v for v in sorted(set(df['y_bar']))],
                row=2,
                col=1,
            )
            return fig

        ### Reformat df
        benchmark_metrics_df = benchmark_metrics_df.reset_index(drop=True)

        dtps_to_plot = [x["in_depth"]["Spectrum"][feature] for x in benchmark_metrics_df["results"].tolist()]
        # Stringify the keys of the datapoint to plot and convert to dataframe
        df = pd.DataFrame([{str(k): v for k, v in i.items()} for i in dtps_to_plot])

        df = df.fillna(str({"exact": 0.0, "mass": 0.0, "n_spectra": 0}))
        df = (
            pd.concat([df, benchmark_metrics_df[["software_name", "id"]]], axis=1)
            .melt(id_vars=["id", "software_name"])
            .rename(columns={"variable": feature, "value": "metrics"})
        )
        df["metrics"] = df["metrics"].apply(lambda x: eval(x) if isinstance(x, str) else x)

        ### Create the scatter-lineplot of the feature
        for dtp_id in df["id"].unique():
            df_dtp = df.loc[df["id"] == dtp_id]
            tool = df_dtp.reset_index().loc[0, "software_name"]

            fig.add_trace(
                go.Scatter(
                    x=df_dtp[feature].tolist(),
                    y=df_dtp["metrics"].apply(lambda x: x[evaluation_type]).tolist(),
                    name=tool,
                    marker=dict(color=software_colors.get(tool, "gray")),
                    mode="lines+markers",
                ),
                row=1,
                col=1,
            )

        ### Create the bar chart
        # Extract the counts as medians for all plotted points
        bar_data = df.groupby(feature)["metrics"].apply(lambda x: np.median([i["n_spectra"] for i in x]))
        bar_counts = bar_data.tolist()
        bar_xaxis = bar_data.index.tolist()

        # Construct hover text
        def create_hovertext(df: pd.DataFrame):
            text = "Number of spectra for each tool"
            for i, (id, metric) in df[["id", "metrics"]].iterrows():
                text += f'<br>{id}: {metric["n_spectra"]}'
            return text

        hovertexts = df.groupby(feature).apply(lambda x: create_hovertext(x)).tolist()

        # Construct the barchart
        fig.add_trace(
            go.Bar(x=bar_xaxis, y=bar_counts, hovertext=hovertexts, marker=dict(color="gray"), showlegend=False),
            row=2,
            col=1,
        )

        fig.update_layout(
            height=600,
            width=600,
            xaxis=dict(title=None, color="black"),
            yaxis=dict(title="Precision", color="black"),
            xaxis2=dict(title=f"{feature}", color="black"),
            yaxis2=dict(title="Number of Spectra", color="black"),
            margin=dict(t=50),
        )
        fig.update_yaxes(
            autorange="reversed",
            # tickvals=[-v for v in sorted(set(df['y_bar']))],
            # ticktext=[v for v in sorted(set(df['y_bar']))],
            row=2,
            col=1,
        )

        return fig

    def plot_species_overview(
        self,
        benchmark_metrics_df,
        evaluation_type="mass",
        software_colors={
            "AdaNovo": "#8b26ff",
            "Casanovo": "#8bc6fd",
            "DeepNovo": "#108E2E",
            "PepNet": "#F89008",
            "Pi-HelixNovo": "#E43924",
            "Pi-PrimeNovo": "#663200",
            "PEAKS": "#f032e6",
            "test": "black",
        },
    ):
        # Create a subplot with 2 rows, shared x-axis
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.8, 0.2],
            vertical_spacing=0,
            subplot_titles=("Species vs Precision", None),
        )
        if len(benchmark_metrics_df) == 0:
            fig.add_trace(go.Scatter())
            fig.add_trace(go.Bar())
            fig.update_layout(
                height=600,
                width=600,
                xaxis=dict(title=None, color="black"),
                yaxis=dict(title="Precision", color="black"),
                xaxis2=dict(title="Species", color="black"),
                yaxis2=dict(title="Number of Spectra", color="black"),
                margin=dict(t=50),
            )
            fig.update_yaxes(
                autorange="reversed",
                # tickvals=[-v for v in sorted(set(df['y_bar']))],
                # ticktext=[v for v in sorted(set(df['y_bar']))],
                row=2,
                col=1,
            )
            return fig

        benchmark_metrics_df = benchmark_metrics_df.reset_index(drop=True)

        df = (
            pd.DataFrame([x["in_depth"]["Species"] for x in benchmark_metrics_df["results"].tolist()])
            .fillna(str({"exact": 0.0, "mass": 0.0, "n_spectra": 0}))
            .map(lambda x: eval(x) if isinstance(x, str) else x)
        )
        df = (
            pd.concat([df, benchmark_metrics_df[["software_name", "id"]]], axis=1)
            .melt(id_vars=["id", "software_name"])
            .rename(columns={"variable": "Species", "value": "metrics"})
        )
        df["metrics"] = df["metrics"].apply(lambda x: eval(x) if isinstance(x, str) else x)

        ### Create the scatter-lineplot of the feature
        for dtp_id in df["id"].unique():
            df_dtp = df.loc[df["id"] == dtp_id]
            tool = df_dtp.reset_index().loc[0, "software_name"]

            fig.add_trace(
                go.Scatter(
                    x=df_dtp["Species"].tolist(),
                    y=df_dtp["metrics"].apply(lambda x: x[evaluation_type]).tolist(),
                    name=tool,
                    marker=dict(color=software_colors.get(tool, "gray")),
                    mode="lines+markers",
                ),
                row=1,
                col=1,
            )

        ### Create the bar chart
        # Extract the counts as medians for all plotted points
        bar_data = df.groupby("Species")["metrics"].apply(lambda x: np.median([i["n_spectra"] for i in x]))
        bar_counts = bar_data.tolist()
        bar_xaxis = bar_data.index.tolist()

        # Construct hover text
        def create_hovertext(df: pd.DataFrame):
            text = "Number of spectra for each tool"
            for i, (id, metric) in df[["id", "metrics"]].iterrows():
                text += f'<br>{id}: {metric["n_spectra"]}'
            return text

        hovertexts = df.groupby("Species").apply(lambda x: create_hovertext(x)).tolist()

        # Construct the barchart
        fig.add_trace(
            go.Bar(x=bar_xaxis, y=bar_counts, hovertext=hovertexts, marker=dict(color="gray"), showlegend=False),
            row=2,
            col=1,
        )

        fig.update_layout(
            height=600,
            width=600,
            xaxis=dict(title=None, color="black"),
            yaxis=dict(title="Precision", color="black"),
            xaxis2=dict(title="Species", color="black"),
            yaxis2=dict(title="Number of Spectra", color="black"),
            margin=dict(t=50),
        )
        fig.update_yaxes(
            autorange="reversed",
            # tickvals=[-v for v in sorted(set(df['y_bar']))],
            # ticktext=[v for v in sorted(set(df['y_bar']))],
            row=2,
            col=1,
        )
        return fig

    def plot_species_specific():
        pass
