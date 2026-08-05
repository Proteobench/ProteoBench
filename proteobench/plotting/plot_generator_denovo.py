"""
Module for plotting results of de novo models
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from proteobench.plotting.plot_generator_base import PlotGeneratorBase

EPSILON = 0.0001

# Main-metric-plot quadrant treatment: fixed axes (padded slightly past 0/1 so points at the
# edges aren't clipped), a boundary at the data midpoint splitting the plot into four named
# regions, and a continuous background gradient (not four flat quadrant colors) since "how far
# into the corner" is itself meaningful -- a point deep in Q1 is doing better than one just
# past the boundary, even though both are "good performance."
MAIN_PLOT_AXIS_RANGE = [-0.05, 1.1]
QUADRANT_BOUNDARY = 0.5
# Precision-coverage curve view: a smaller pad than the scatter's, just enough that a curve
# endpoint sitting exactly at 0 or 1 isn't clipped by the axis border.
PR_CURVE_AXIS_RANGE = [-0.03, 1.03]
# Single sequential hue, light (low) to dark blue (high) -- a magnitude encoding ("how good"),
# not a category or polarity one, so one hue avoids both a rainbow and a red/green pair that
# would be indistinguishable to red-green colorblind users.
QUADRANT_COLORSCALE = [
    [0.0, "#f4efe4"],
    [0.35, "#cfe0e8"],
    [0.65, "#8fb9cf"],
    [0.85, "#4d87ac"],
    [1.0, "#1f5678"],
]
QUADRANT_LABELS = {
    "good": {"text": "<b>Good performance</b>"},
    "near_miss": {
        "text": "<b>Near-miss</b><br><span style='font-size:10px'>Often suggests a very similar peptide</span>"
    },
    "low": {"text": "<b>Low performance</b>"},
    "alt_candidate": {
        "text": (
            "<b>Alternative candidate</b><br>" "<span style='font-size:10px'>(Suggests fully different peptide)</span>"
        )
    },
}

SOFTWARE_COLORS = {
    "AdaNovo": "#88CCEE",
    "Casanovo": "#CC6677",
    "DeepNovo": "#DDCC77",
    "PepNet": "#117733",
    "Pi-HelixNovo": "#332288",
    "Pi-PrimeNovo": "#AA4499",
    "PEAKS": "#661100",
    "SMSNet": "#44AA99",
    "InstaNovo": "#999933",
    "ContraNovo": "#882255",
    "PointNovo": "#E07030",
    "NovoB": "#4477AA",
    "Custom": "#000000",
}
SOFTWARE_MARKERS = {
    "AdaNovo": "circle",
    "Casanovo": "square",
    "DeepNovo": "diamond",
    "PepNet": "cross",
    "Pi-HelixNovo": "x",
    "Pi-PrimeNovo": "triangle-up",
    "PEAKS": "star",
    "SMSNet": "triangle-down",
    "InstaNovo": "pentagon",
    "ContraNovo": "hexagon",
    "PointNovo": "triangle-left",
    "NovoB": "triangle-right",
    "Custom": "circle-open",
}


_LEVELS = ("peptide", "aa")
_EVALUATION_TYPES = ("mass", "exact")
_METRICS = ("precision", "recall", "coverage", "auc")


def _get_metrics_leaf(row: pd.Series, level: str, evaluation_type: str, ambiguity_combo: Optional[str] = None) -> dict:
    """
    Return the `{precision, recall, coverage, auc}` dict for one level/evaluation-type,
    optionally reading an ambiguity-toggle combination instead of the baseline.

    Ambiguity combinations only exist under exact-mode matching (mass-mode metrics are
    identical regardless, since I/L are isomeric and deamidated Q/N are isobaric with E/D
    either way), so `ambiguity_combo` is ignored for `evaluation_type == "mass"`.
    """
    leaf = row["results"][level][evaluation_type]
    if evaluation_type == "exact" and ambiguity_combo:
        return leaf["ambiguity"][ambiguity_combo]
    return leaf


def datapoint_has_required_fields(
    results_dict: dict,
    evaluation_type: str,
    needs_auc: bool,
    ambiguity_combo: Optional[str],
    needs_curve: bool = False,
) -> bool:
    """
    Check whether a datapoint's `results` dict has the fields the main plot needs for the
    currently selected evaluation type, metric (precision or AUC), and ambiguity combination.

    Used to silently hide datapoints submitted before a given field existed (e.g. `auc`,
    `curve`, or the `ambiguity` sub-dict) rather than erroring, mirroring the HYE plot
    generator's handling of legacy datapoints missing newer metric fields.
    """
    try:
        for level in _LEVELS:
            leaf = _get_metrics_leaf({"results": results_dict}, level, evaluation_type, ambiguity_combo)
            if needs_auc and "auc" not in leaf:
                return False
            if needs_curve and "curve" not in leaf:
                return False
    except (TypeError, KeyError):
        return False
    return True


def flatten_results_column(df: pd.DataFrame, ambiguity_combo: Optional[str] = None) -> pd.DataFrame:
    """
    Flatten each row's nested `results` dict into flat `{level}_{evaluation_type}_{metric}`
    columns for plotting.

    Parameters
    ----------
    ambiguity_combo : str, optional
        One of `"il"`, `"deam"`, `"both"` to read the corresponding exact-mode ambiguity
        combination instead of the baseline; `None` (default) reads the baseline. Ignored
        for mass-mode fields, which don't have ambiguity combinations (see
        `_get_metrics_leaf`).
    """
    results = {"engine": []}
    for level in _LEVELS:
        for evaluation_type in _EVALUATION_TYPES:
            for metric in _METRICS:
                results[f"{level}_{evaluation_type}_{metric}"] = []

    for _, row in df.iterrows():
        results["engine"].append(row["software_name"])
        for level in _LEVELS:
            for evaluation_type in _EVALUATION_TYPES:
                leaf = _get_metrics_leaf(row, level, evaluation_type, ambiguity_combo)
                for metric in _METRICS:
                    # `.get(..., nan)`, not `[...]`: a legacy datapoint may lack "auc" even
                    # when it's not the metric currently being plotted (datapoint_has_
                    # required_fields already decided visibility for the active selection;
                    # this must not crash just because it computes every column eagerly).
                    results[f"{level}_{evaluation_type}_{metric}"].append(leaf.get(metric, float("nan")))

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
            - level: str (default "precision") - metric type ("precision" or "auc")
            - evaluation_type: str (default "mass") - evaluation type ("mass" or "exact")
            - allow_il: bool (default True) - under exact evaluation, treat I/L as equivalent
            - allow_deamidation: bool (default False) - under exact evaluation, treat
              deamidated Q/N as equivalent to E/D
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
        allow_il = kwargs.get("allow_il", True)
        allow_deamidation = kwargs.get("allow_deamidation", False)
        colorblind_mode = kwargs.get("colorblind_mode", False)
        software_colors = kwargs.get(
            "software_colors",
            SOFTWARE_COLORS,
        )
        software_markers = kwargs.get(
            "software_markers",
            SOFTWARE_MARKERS,
        )
        mapping = kwargs.get("mapping", {"old": 10, "new": 20})
        highlight_color = kwargs.get("highlight_color", "#d30067")
        label = kwargs.get("label", "None")

        # Ambiguity combinations only exist under exact-mode matching; mass-mode metrics
        # are identical regardless (I/L are isomeric, deamidated Q/N isobaric with E/D).
        ambiguity_combo = None
        if evaluation_type == "exact":
            if allow_il and allow_deamidation:
                ambiguity_combo = "both"
            elif allow_il:
                ambiguity_combo = "il"
            elif allow_deamidation:
                ambiguity_combo = "deam"

        # Use result_df as the main dataframe (renamed from benchmark_metrics_df)
        benchmark_metrics_df = result_df.reset_index(drop=True)

        # Silently hide datapoints submitted before the selected field existed (AUC, or the
        # ambiguity combination), rather than erroring on a missing key.
        needs_auc = level == "auc"
        benchmark_metrics_df = benchmark_metrics_df[
            benchmark_metrics_df["results"].apply(
                lambda r: datapoint_has_required_fields(r, evaluation_type, needs_auc, ambiguity_combo)
            )
        ].reset_index(drop=True)

        # Define layout
        results_df = flatten_results_column(benchmark_metrics_df, ambiguity_combo=ambiguity_combo)
        benchmark_metrics_df = pd.concat([benchmark_metrics_df, results_df], axis=1)

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

        # Fixed axis range (not the data's own min/max): both precision and AUC are bounded
        # in [0, 1], so a shared, fixed range keeps the quadrant boundary and background
        # gradient below anchored to the same meaningful midpoint every time, and padding
        # past 0/1 (rather than clipping exactly at them) keeps points at the edges visible.
        layout_xaxis_range = list(MAIN_PLOT_AXIS_RANGE)
        layout_yaxis_range = list(MAIN_PLOT_AXIS_RANGE)
        level_title = "AUC" if level == "auc" else level.capitalize()
        layout_xaxis_title = f"Peptide {level_title}"
        layout_yaxis_title = f"Amino Acid {level_title}"

        fig = go.Figure(
            layout_yaxis_range=layout_yaxis_range,
            layout_xaxis_range=layout_xaxis_range,
        )

        # Continuous background gradient, lightest at the origin and deepest at (1, 1), so
        # "how far into the corner" reads visually even within a single quadrant. Added first
        # so the scatter markers below are drawn on top of it, not the other way around.
        grid_coords = np.linspace(MAIN_PLOT_AXIS_RANGE[0], MAIN_PLOT_AXIS_RANGE[1], 60)
        grid_z = [[(x + y) / 2 for x in grid_coords] for y in grid_coords]
        fig.add_trace(
            go.Heatmap(
                x=grid_coords,
                y=grid_coords,
                z=grid_z,
                zmin=0,
                zmax=1,
                colorscale=QUADRANT_COLORSCALE,
                showscale=False,
                opacity=0.45,
                hoverinfo="skip",
            )
        )

        # Dashed boundary lines at the data midpoint, splitting the plot into the four named
        # regions (drawn above the gradient/markers so they stay crisp at any zoom).
        fig.add_shape(
            type="line",
            x0=QUADRANT_BOUNDARY,
            x1=QUADRANT_BOUNDARY,
            y0=MAIN_PLOT_AXIS_RANGE[0],
            y1=MAIN_PLOT_AXIS_RANGE[1],
            line=dict(color="rgba(90,90,90,0.6)", width=1, dash="dash"),
            layer="above",
        )
        fig.add_shape(
            type="line",
            x0=MAIN_PLOT_AXIS_RANGE[0],
            x1=MAIN_PLOT_AXIS_RANGE[1],
            y0=QUADRANT_BOUNDARY,
            y1=QUADRANT_BOUNDARY,
            line=dict(color="rgba(90,90,90,0.6)", width=1, dash="dash"),
            layer="above",
        )

        # Quadrant labels, placed inside each region near its outer edge.
        left_x = (MAIN_PLOT_AXIS_RANGE[0] + QUADRANT_BOUNDARY) / 2
        right_x = (QUADRANT_BOUNDARY + MAIN_PLOT_AXIS_RANGE[1]) / 2
        top_y = MAIN_PLOT_AXIS_RANGE[1] - 0.05
        bottom_y = MAIN_PLOT_AXIS_RANGE[0] + 0.03
        for x, y, quadrant_key in (
            (right_x, top_y, "good"),
            (left_x, top_y, "near_miss"),
            (left_x, bottom_y, "low"),
            (right_x, bottom_y, "alt_candidate"),
        ):
            fig.add_annotation(
                x=x,
                y=y,
                text=QUADRANT_LABELS[quadrant_key]["text"],
                showarrow=False,
                font=dict(size=12, color="rgba(60,60,60,0.85)"),
                align="center",
            )

        # Corner cue: further into the top-right is strictly better on both axes.
        fig.add_annotation(
            x=MAIN_PLOT_AXIS_RANGE[1],
            y=MAIN_PLOT_AXIS_RANGE[1],
            xanchor="right",
            yanchor="top",
            text="↗ better performance",
            showarrow=False,
            font=dict(size=11, color="#1f5678"),
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

    def plot_precision_coverage_curves(self, result_df: pd.DataFrame, **kwargs) -> go.Figure:
        """
        Generate the precision-vs-coverage curve view: peptide-level and amino-acid-level
        curves side by side, one line per software tool. An alternative to `plot_main_metric`
        showing the full threshold-swept curve behind a single-point precision/AUC value,
        rather than a single-point summary of it.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot.
        **kwargs : dict
            Additional parameters:
            - evaluation_type: str (default "mass") - evaluation type ("mass" or "exact")
            - allow_il: bool (default True) - under exact evaluation, treat I/L as equivalent
            - allow_deamidation: bool (default False) - under exact evaluation, treat
              deamidated Q/N as equivalent to E/D
            - software_colors: Dict[str, str] - color mapping for software tools

        Returns
        -------
        go.Figure
            A 1x2 subplot figure: peptide-level curve (left), amino-acid-level curve (right).
        """
        evaluation_type = kwargs.get("evaluation_type", "mass")
        allow_il = kwargs.get("allow_il", True)
        allow_deamidation = kwargs.get("allow_deamidation", False)
        software_colors = kwargs.get("software_colors", SOFTWARE_COLORS)

        ambiguity_combo = None
        if evaluation_type == "exact":
            if allow_il and allow_deamidation:
                ambiguity_combo = "both"
            elif allow_il:
                ambiguity_combo = "il"
            elif allow_deamidation:
                ambiguity_combo = "deam"

        # Silently hide datapoints submitted before the stored curve existed, same as
        # plot_main_metric does for `auc`/`ambiguity`.
        benchmark_metrics_df = result_df.reset_index(drop=True)
        benchmark_metrics_df = benchmark_metrics_df[
            benchmark_metrics_df["results"].apply(
                lambda r: datapoint_has_required_fields(
                    r, evaluation_type, needs_auc=False, ambiguity_combo=ambiguity_combo, needs_curve=True
                )
            )
        ].reset_index(drop=True)

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Peptide-level", "Amino-acid-level"),
            horizontal_spacing=0.12,
        )

        for col_idx, level in enumerate(_LEVELS, start=1):
            for _, row in benchmark_metrics_df.iterrows():
                curve = _get_metrics_leaf(row, level, evaluation_type, ambiguity_combo).get("curve")
                if not curve or not curve.get("coverage"):
                    continue  # degenerate curve (e.g. all-identical scores) or legacy datapoint
                software = row["software_name"]
                fig.add_trace(
                    go.Scatter(
                        x=curve["coverage"],
                        y=curve["precision"],
                        mode="lines",
                        name=software,
                        legendgroup=software,
                        showlegend=(col_idx == 1),
                        line=dict(color=software_colors.get(software, "gray")),
                        hovertemplate=f"{software}<br>Coverage: %{{x:.3f}}<br>Precision: %{{y:.3f}}<extra></extra>",
                    ),
                    row=1,
                    col=col_idx,
                )

        for col_idx in (1, 2):
            fig.update_xaxes(title_text="Coverage", range=PR_CURVE_AXIS_RANGE, row=1, col=col_idx)
            fig.update_yaxes(title_text="Precision", range=PR_CURVE_AXIS_RANGE, row=1, col=col_idx)

        fig.update_layout(width=900, height=480)
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
            SOFTWARE_COLORS,
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

    def get_metrics_help_markdown(self) -> str:
        """
        Return a Markdown explanation of how the metrics of the main plot are calculated.

        Returns
        -------
        str
            The Markdown explanation shown in the "How are the metrics calculated?" popover.
        """
        return """
            Each point is one benchmark run. The predicted peptidoforms are compared against the
            ground-truth peptidoforms of the benchmark dataset, and both axes show the same metric
            at two different levels of granularity.

            **X-axis** - the metric at **peptide level**: a prediction counts as correct only when
            the whole peptidoform is considered a match.

            **Y-axis** - the metric at **amino-acid level**: the individual amino acids that are
            correctly predicted are counted, so partially correct sequences still contribute.

            A tool in the **upper right corner** therefore performs well at both levels. A point
            that sits high but not far to the right predicts many individual amino acids correctly
            without getting whole sequences right.

            **Select the classification metric** - which metric is shown on both axes:

            - **Precision** - the fraction of the reported predictions that is correct:
              `precision = correct predictions / reported predictions`. It describes how reliable
              the reported sequences are.
            - **Recall** - the fraction of the spectra that received a correct prediction:
              `recall = correct predictions / total spectra`. It describes the coverage of the
              dataset.

            The two differ whenever a tool does not report a prediction for every spectrum: a tool
            can reach a high precision by only reporting its confident predictions, while its recall
            stays low.

            **Select the stringency of evaluation** - when a prediction counts as correct:

            - **Exact** - the predicted sequence must match the ground truth exactly, including the
              modifications and their positions. This is the strictest criterion.
            - **Mass-based** - a prediction also counts as correct when it matches the ground truth
              through the longest mass-matching prefix and suffix, using a cumulative mass tolerance
              of 50 ppm and an individual amino-acid tolerance of 20 ppm. This accepts
              interpretations that cannot be distinguished by mass, such as isobaric amino acids
              (for example I and L). Mass-based numbers are therefore always equal to or higher than
              the exact numbers.

            **Colorblind Mode** - distinguishes the software tools by marker shape in addition to
            colour.
            """

    def get_in_depth_metrics_help_markdown(self) -> str:
        """
        Return a Markdown explanation of how the in-depth plots are calculated.

        Returns
        -------
        str
            The Markdown explanation shown in the "How are the metrics calculated?" popover on the
            in-depth tab.
        """
        return """
            The plots on this tab break the overall performance down by properties of the peptide or
            the spectrum, instead of reducing each run to a single pair of numbers as the main plot
            does. They are all derived from the same per-PSM comparison between the predicted and the
            ground-truth peptidoform.

            Each PSM is classified into one **match type** by aligning the prediction against the
            ground truth from both termini:

            - **exact** - the predicted sequence matches the ground truth exactly, including the
              modifications and their positions.
            - **mass** - not an exact match, but the prediction matches through its longest
              mass-matching prefix and suffix, within a cumulative mass tolerance of 50 ppm and an
              individual amino-acid tolerance of 20 ppm. This covers interpretations that cannot be
              distinguished by mass, such as isobaric amino acids (for example I and L).
            - **mismatch** - neither of the above.

            The alignment also records for each individual amino acid whether it was matched, which is
            what the PTM plots below are based on.

            **PTM plots** - restricted to the PSMs whose peptidoform carries the modification in
            question, and reported for six modifications: oxidation of M, deamidation of Q and of N,
            and N-terminal acetylation, carbamylation and ammonia loss. Per modification the fraction
            of modified residues that was matched exactly is computed twice:

            - over the modifications present in the **ground truth** - did the tool find the
              modification that is really there?
            - over the modifications the tool **predicted** - was a predicted modification real?

            The overview plot puts the first on the x-axis and the second on the y-axis, so the two
            failure modes are separated: a tool low on the x-axis misses modifications that are there,
            while a tool low on the y-axis reports modifications that are not.

            **Spectrum feature plots** - the PSMs are binned by a spectrum or peptide property, and
            within each bin the fraction of correctly predicted PSMs is computed per tool. The upper
            panel draws that fraction as a line per tool. The lower panel is a grey bar chart of the
            number of spectra per bin, so a line can be read together with how much data supports it:
            the extreme bins are usually sparse, and their values are correspondingly noisy. Hovering
            a bar lists the per-tool spectrum counts. Three properties are available:

            - **Missing fragmentation sites** - the number of backbone positions with no supporting
              fragment ion, binned from 0 to 30. De novo sequencing needs contiguous fragment
              coverage, so accuracy is expected to drop as this rises.
            - **Peptide length** - binned from 5 to 30 residues. Longer peptides offer more
              opportunity for a single wrong residue to break an exact match.
            - **% explained intensity** - the fraction of the spectrum intensity that the annotation
              accounts for, binned in 3% steps. It is a proxy for spectrum quality.

            **Species overview** - the same two-panel layout, with the source organism of the
            ground-truth peptide on the x-axis, over the nine species in the benchmark dataset.
            Because most models are trained predominantly on human data, this exposes how well a model
            generalises to organisms it has seen less of.

            The spectrum feature plots and the species overview each have an **Exact evaluation
            mode** toggle. It switches between counting only exact matches and counting exact plus
            mass matches as correct, so it changes which match types are treated as correct rather
            than the underlying classification. The PTM plots have no such toggle: they are always
            evaluated on exact residue-level matches.
            """

    def plot_ptm_overview(
        self,
        benchmark_metrics_df: pd.DataFrame,
        mod_labels: List[str],
        software_colors: Dict[str, str] = SOFTWARE_COLORS,
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
        software_colors: Dict[str, str] = SOFTWARE_COLORS,
    ):
        fig = go.Figure()

        # Same continuous corner gradient as the main plot (light -> dark towards (1, 1)):
        # this plot's diagonal has the same "good" orientation -- top-right is strong
        # performance, bottom-left is poor -- per Description.ptm_specific below.
        grid_coords = np.linspace(0.0, 1.0, 60)
        grid_z = [[(x + y) / 2 for x in grid_coords] for y in grid_coords]
        fig.add_trace(
            go.Heatmap(
                x=grid_coords,
                y=grid_coords,
                z=grid_z,
                zmin=0,
                zmax=1,
                colorscale=QUADRANT_COLORSCALE,
                showscale=False,
                opacity=0.45,
                hoverinfo="skip",
            )
        )

        for i, row in benchmark_metrics_df.iterrows():
            ptm_data = row["results"]["in_depth"]["PTM"]

            # To make division by 0 impossible

            x = ptm_data[mod_label]["correct_gt"] / (ptm_data[mod_label]["counts_gt"] + EPSILON)
            y = ptm_data[mod_label]["correct_dn"] / (ptm_data[mod_label]["counts_dn"] + EPSILON)
            tool = row["software_name"]
            fig.add_trace(go.Scatter(x=[x], y=[y], name=tool, marker=dict(color=software_colors[tool])))

        # Short corner descriptions, condensed from Description.ptm_specific's
        # "How to interpret the plot" section.
        for x, y, xanchor, yanchor, text in (
            (0.97, 0.97, "right", "top", "<b>Strong performance</b><br>frequent & correct"),
            (0.03, 0.97, "left", "top", "<b>Conservative</b><br>rare but correct"),
            (0.03, 0.03, "left", "bottom", "<b>Poor performance</b><br>rare & incorrect"),
            (0.97, 0.03, "right", "bottom", "<b>Overprediction</b><br>frequent but incorrect"),
        ):
            fig.add_annotation(
                x=x,
                y=y,
                xanchor=xanchor,
                yanchor=yanchor,
                text=text,
                showarrow=False,
                align=xanchor,
                font=dict(size=10, color="rgba(60,60,60,0.85)"),
            )

        fig.update_layout(
            width=500,
            height=500,
            xaxis=dict(title="Precision (Ground-truth)", color="black", gridwidth=2, range=[0, 1]),
            yaxis=dict(title="Precision (denovo)", color="black", gridwidth=2, range=[0, 1]),
        )

        return fig

    @staticmethod
    def get_modification_scores(mod_dict, mod_labels):
        x = []
        y = []

        for mod_label in mod_labels:
            x.append(mod_label)
            # EPSILON must guard the denominator (as plot_ptm_specific does), not be added
            # to the final ratio -- `a / b + EPSILON` is `(a / b) + EPSILON` in Python, which
            # still raises ZeroDivisionError when counts_gt is 0 (a modification that never
            # occurs in the ground truth for the current view, e.g. a rare PTM on a small
            # per-species selection).
            y.append(mod_dict[mod_label]["correct_gt"] / (mod_dict[mod_label]["counts_gt"] + EPSILON))
        return x, y

    def plot_spectrum_feature(
        self,
        benchmark_metrics_df,
        feature,
        evaluation_type="mass",
        software_colors=SOFTWARE_COLORS,
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
        software_colors=SOFTWARE_COLORS,
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
