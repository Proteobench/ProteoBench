"""
The de novo plot generator itself.
"""

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from proteobench.plotting.plot_generator_base import PlotGeneratorBase
from proteobench.plotting.plot_generator_denovo.results import (
    _LEVELS,
    _ambiguity_combo_for,
    _get_metrics_leaf,
    _metrics_or_empty,
    datapoint_has_required_fields,
    flatten_results_column,
)
from proteobench.plotting.plot_generator_denovo.labels import (
    _display_value,
    _is_blank,
    build_display_labels,
    build_variant_descriptions,
)
from proteobench.plotting.plot_generator_denovo.ranking import leading_datapoints, rank_within_tools
from proteobench.plotting.plot_generator_denovo.selection import (
    BEST_MARKER_SCALE,
    BEST_MARKER_SYMBOL,
    DIMMED_OPACITY,
    MUTED_COLOR,
    MUTED_CURVE_OPACITY,
    SECONDARY_CURVE_OPACITY,
    SECONDARY_OPACITY,
    SOFTWARE_COLORS,
    SOFTWARE_MARKERS,
    assign_datapoint_colors,
    resolve_coloured_datapoints,
    resolve_emphasis,
)


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
        "text": "<b>Near-miss</b><br><span style='font-size:10px'>Often incorrect, but predictions are very similar to ground-truth peptide</span>"
    },
    "low": {"text": "<b>Low performance</b>"},
    "alt_candidate": {
        "text": (
            "<b>Alternative candidate</b><br>"
            "<span style='font-size:10px'>(Often correct, but when incorrect, suggest a completely different peptide)</span>"
        )
    },
}

# FASTA-category breakdown (correct / in_fasta / not_in_fasta), computed once per datapoint by
# `DenovoDatapoint.get_infasta_metrics` from the "category" column `DenovoScores.add_fasta_category`
# assigns during scoring. Colors match the exploratory notebook this feature was designed in.
INFASTA_CATEGORIES = ("correct", "in_fasta", "not_in_fasta")

INFASTA_COLORS = {
    "correct": "#4C9A6D",  # muted green
    "in_fasta": "#F2A541",  # muted amber
    "not_in_fasta": "#D1495B",  # muted rose
}

INFASTA_LABELS = {
    "correct": "Correct",
    "in_fasta": "In FASTA",
    "not_in_fasta": "Not in FASTA",
}

#: Most points kept per precision-coverage curve. The stored curves hold ~500 points each, which
#: at a couple of hundred datapoints is several megabytes of JSON per rerun for a 700px-wide plot
#: that cannot resolve anything like that many. Evenly subsampling to this many is invisible and
#: cuts the payload by roughly four fifths.
MAX_CURVE_POINTS = 120


def thin_curve(coverage: Sequence[float], precision: Sequence[float]) -> Tuple[list, list]:
    """
    Subsample a stored curve to at most :data:`MAX_CURVE_POINTS` points.

    The first and last points are always kept, so the curve still spans its full coverage range.

    Parameters
    ----------
    coverage : sequence of float
        Curve x values.
    precision : sequence of float
        Curve y values.

    Returns
    -------
    tuple of (list, list)
        The thinned coverage and precision values.
    """
    count = min(len(coverage), len(precision))
    if count <= MAX_CURVE_POINTS:
        return list(coverage[:count]), list(precision[:count])
    step = count / MAX_CURVE_POINTS
    keep = sorted({int(i * step) for i in range(MAX_CURVE_POINTS)} | {count - 1})
    return [coverage[i] for i in keep], [precision[i] for i in keep]


#: Line and marker styling for the in-depth plots, keyed by whether the datapoint is emphasised.
#: With nothing highlighted every datapoint is emphasised, so the figure reads as it did before.
_IN_DEPTH_LINE_EMPHASIS = {
    True: {"width": 2.6, "size": 7, "opacity": 0.95},
    False: {"width": 1.2, "size": 5, "opacity": DIMMED_OPACITY + 0.06},
}


def _leader_line_annotations(points: List[dict], xref: str = "x", yref: str = "y") -> List[dict]:
    """
    Place labels clear of their datapoints, each joined to its own point by a leader line.

    Offsets are spread around a circle rather than applied uniformly, because the datapoints that
    most need labelling are frequently almost coincident: several runs of one tool differing only
    in decoding strategy land within a few thousandths of each other, and a fixed offset would
    stack their labels on top of one another.

    Parameters
    ----------
    points : list of dict
        One entry per label, with ``x``, ``y``, ``text`` and ``color`` keys.
    xref : str
        Plotly x-axis reference the coordinates belong to.
    yref : str
        Plotly y-axis reference the coordinates belong to.

    Returns
    -------
    list of dict
        Plotly annotation dicts, ready to extend a layout's ``annotations``.
    """
    count = len(points)
    if count == 0:
        return []
    radius = 58 if count <= 2 else 58 + min(34, (count - 2) * 7)
    annotations = []
    for position, point in enumerate(points):
        angle = (-np.pi / 2) + (2 * np.pi * position) / max(count, 3)
        annotations.append(
            dict(
                x=point["x"],
                y=point["y"],
                xref=xref,
                yref=yref,
                ax=float(np.cos(angle) * radius),
                ay=float(np.sin(angle) * radius),
                axref="pixel",
                ayref="pixel",
                text=point["text"],
                showarrow=True,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor=point["color"],
                standoff=4,
                font=dict(size=10, color="#1a1a1a"),
                bgcolor="rgba(255,255,255,0.86)",
                bordercolor=point["color"],
                borderwidth=1,
                borderpad=2,
                captureevents=False,
            )
        )
    return annotations


def _empty_main_metric_figure(level_title: str) -> go.Figure:
    """
    The main-metric figure drawn when there is nothing to plot.

    Either the caller passed an empty frame, or every datapoint was filtered out as missing the
    selected field. Boolean-indexing an empty frame drops its columns, so the real path would
    raise ``KeyError`` on ``software_name`` rather than draw anything.

    Parameters
    ----------
    level_title : str
        Name of the plotted metric, for the axis titles.

    Returns
    -------
    go.Figure
        Empty axes, saying so.
    """
    empty = go.Figure()
    empty.update_layout(
        width=700,
        height=700,
        xaxis=dict(title=f"Peptide {level_title}", range=list(MAIN_PLOT_AXIS_RANGE)),
        yaxis=dict(title=f"Amino Acid {level_title}", range=list(MAIN_PLOT_AXIS_RANGE)),
        plot_bgcolor="white",
    )
    empty.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        text="No datapoints to display for this selection",
        font=dict(size=14, color="rgba(60,60,60,0.75)"),
    )
    return empty


def _main_metric_hover_texts(
    benchmark_metrics_df: pd.DataFrame,
    display_labels: pd.Series,
    variants: pd.Series,
    best_by_tool: Dict[str, object],
    evaluation_type: str,
    level: str,
    level_title: str,
    hover_columns: Optional[Sequence[str]],
) -> List[str]:
    """
    The hover box of every datapoint: its identity, what it was, and the two plotted values.

    Only the columns the caller asked for are added. The previous fixed dump of every parameter
    buried the few fields that actually differ between the points being compared among a dozen
    identical ones. The "ProteoBench ID:" line is kept verbatim because ``render_metric_plot``
    parses the clicked point's ID out of the hover text.

    Parameters
    ----------
    benchmark_metrics_df : pd.DataFrame
        The datapoints being drawn, already flattened.
    display_labels : pd.Series
        Name per datapoint.
    variants : pd.Series
        What sets each datapoint apart from its tool's other runs; blank where nothing does.
    best_by_tool : dict
        Tool name to the index of its best datapoint.
    evaluation_type : str
        ``"mass"`` or ``"exact"``.
    level : str
        Metric being plotted.
    level_title : str
        Its display name.
    hover_columns : Sequence of str, optional
        Parameter columns to list under the values.

    Returns
    -------
    list of str
        One hover string per row, in the frame's own order.
    """
    hover_texts = []
    for idx, row in benchmark_metrics_df.iterrows():
        lines = [
            f"ProteoBench ID: {row['id']}",
            f"<b>{display_labels.at[idx]}</b>",
        ]
        # Directly under the name, before anything else: on a tool submitted many times the
        # name alone says which run this is only by its rank, and what the reader wants to
        # know first is what that run actually was.
        if variants.at[idx]:
            lines.append(f"<i>{variants.at[idx]}</i>")
        if best_by_tool.get(str(row["software_name"])) == idx:
            lines.append("Best datapoint of this tool")
        for axis, prefix in (("peptide", "Peptide"), ("aa", "Amino acid")):
            value = row.get(f"{axis}_{evaluation_type}_{level}")
            if isinstance(value, (int, float)) and not isinstance(value, bool) and not np.isnan(value):
                lines.append(f"{prefix} {level_title}: {value:.3f}")
        for column in hover_columns or []:
            if column not in benchmark_metrics_df.columns:
                continue
            lines.append(f"{column}: {_display_value(row[column])}")
        if row.get("is_temporary") is True:
            lines.append("Private submission, not yet published")
        hover_texts.append("<br>".join(lines))
    return hover_texts


def _main_metric_marker_arrays(
    benchmark_metrics_df: pd.DataFrame,
    coloured: pd.Series,
    leading: set,
    highlight_tool: Optional[str],
    highlight_color: str,
    software_colors: Dict[str, str],
) -> Tuple[List[str], List[float], List[float]]:
    """
    Per-point colour, opacity and outline width for the main-metric scatter.

    Colour is the tool's own where the datapoint is coloured, and the shared muted grey
    otherwise. Highlighting a tool colours every one of its datapoints, including the ones that
    are grey by default, which is how a tool's spread becomes visible on demand without
    colouring every tool's spread all of the time.

    Parameters
    ----------
    benchmark_metrics_df : pd.DataFrame
        The datapoints being drawn.
    coloured : pd.Series
        Whether each datapoint is drawn in its tool's colour.
    leading : set
        Indices of the best coloured datapoint of each tool.
    highlight_tool : str, optional
        Tool to bring forward, dimming the rest.
    highlight_color : str
        Colour for rows flagged in a ``Highlight`` column, which overrides everything else.
    software_colors : Dict[str, str]
        Colour per tool.

    Returns
    -------
    tuple of list
        Colours, opacities and outline widths, aligned to the frame's order.
    """
    colors, opacities, line_widths = [], [], []
    for idx in benchmark_metrics_df.index:
        tool = str(benchmark_metrics_df.at[idx, "software_name"])
        tool_color = software_colors.get(tool, "gray")
        is_highlighted = highlight_tool is not None and tool == highlight_tool
        if highlight_tool is not None and not is_highlighted:
            colors.append(tool_color if coloured.at[idx] else MUTED_COLOR)
            opacities.append(DIMMED_OPACITY)
            line_widths.append(0.0)
        elif is_highlighted:
            colors.append(tool_color)
            opacities.append(0.95)
            line_widths.append(1.6 if coloured.at[idx] else 1.0)
        elif coloured.at[idx]:
            colors.append(tool_color)
            opacities.append(0.95 if idx in leading else SECONDARY_OPACITY)
            line_widths.append(1.0 if idx in leading else 0.0)
        else:
            colors.append(MUTED_COLOR)
            opacities.append(0.55)
            line_widths.append(1.0)
    if "Highlight" in benchmark_metrics_df.columns:
        colors = [
            highlight_color if highlight else item for item, highlight in zip(colors, benchmark_metrics_df["Highlight"])
        ]
    return colors, opacities, line_widths


def _add_quadrant_background(fig: go.Figure) -> None:
    """
    Draw the four named regions behind the datapoints, in place.

    A continuous gradient, lightest at the origin and deepest at (1, 1), so "how far into the
    corner" reads visually even within a single quadrant. Added before the markers so they are
    drawn on top of it, with the boundary lines above both so they stay crisp at any zoom.

    Parameters
    ----------
    fig : go.Figure
        Figure to draw into.
    """
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
            opacity=0.28,
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
        muted_tools = kwargs.get("muted_tools", ())
        selected_ids = kwargs.get("selected_ids", ())
        explicit_selection = kwargs.get("explicit_selection", False)
        highlight_tool = kwargs.get("highlight_tool", None)
        hover_columns = kwargs.get("hover_columns", None)
        # `label` named a single column to print on every point; `annotation_columns` supersedes
        # it with a list, drawn with leader lines and only on the datapoints worth labelling.
        annotation_columns = kwargs.get("annotation_columns", None)
        if annotation_columns is None:
            annotation_columns = [] if label in (None, "None") else [label]

        ambiguity_combo = _ambiguity_combo_for(evaluation_type, allow_il, allow_deamidation)

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

        level_title = "AUC" if level == "auc" else level.capitalize()

        # Nothing left to plot: either the caller passed an empty frame, or every datapoint was
        # filtered out as missing the selected field. Boolean-indexing an empty frame drops its
        # columns, so everything below would raise KeyError on `software_name` rather than draw
        # an empty figure. The in-depth plots already return a skeleton in this situation.
        if len(benchmark_metrics_df) == 0:
            return _empty_main_metric_figure(level_title)

        # Ranking, labels and colouring. Exactly one datapoint per tool is coloured by default,
        # its best, so that a tool submitted fifteen times does not visually outweigh a tool
        # submitted once. Everything else stays on the plot in grey rather than being dropped.
        ranks, best_by_tool = rank_within_tools(benchmark_metrics_df, evaluation_type, ambiguity_combo)
        display_labels = build_display_labels(benchmark_metrics_df, ranks=ranks)
        # What tells a run apart from its own tool's other submissions, kept separate from the
        # name rather than folded into it: the name stays short enough to read on the plot, and
        # the parameters still reach the reader, on hover and in the table's own column.
        variants = build_variant_descriptions(benchmark_metrics_df)
        coloured = resolve_coloured_datapoints(
            benchmark_metrics_df,
            best_by_tool=best_by_tool,
            muted_tools=muted_tools,
            selected_ids=selected_ids,
            explicit_only=explicit_selection,
        )
        benchmark_metrics_df["display_label"] = display_labels
        benchmark_metrics_df["is_coloured"] = coloured
        # Being coloured no longer implies being a tool's representative: the table can tick
        # every run a tool submitted. The best coloured run of each tool keeps full weight and
        # the rest are faded into the same hue, so a tool's spread reads as context.
        leading = leading_datapoints(benchmark_metrics_df, coloured, ranks)
        best_indices = set(best_by_tool.values())

        # Hover carries the datapoint's identity, the two plotted values, and only the columns
        # the caller asked for. The previous fixed dump of every parameter buried the few fields
        # that actually differ between the points being compared among a dozen identical ones.
        # The "ProteoBench ID:" line is kept verbatim because `render_metric_plot` parses the
        # clicked point's ID out of the hover text.
        hover_texts = _main_metric_hover_texts(
            benchmark_metrics_df,
            display_labels=display_labels,
            variants=variants,
            best_by_tool=best_by_tool,
            evaluation_type=evaluation_type,
            level=level,
            level_title=level_title,
            hover_columns=hover_columns,
        )

        # Size says coloured or greyed; the old/new ratio is applied on top as a multiplier
        # rather than an absolute size, so an unpublished point stays easy to find without
        # overriding the distinction that now carries the primary meaning.
        base_sizes = [14 if idx in leading else (10 if coloured.at[idx] else 9) for idx in benchmark_metrics_df.index]
        if not colorblind_mode:
            base_sizes = [
                size * BEST_MARKER_SCALE if idx in best_indices else size
                for size, idx in zip(base_sizes, benchmark_metrics_df.index)
            ]
        old_size, new_size = mapping.get("old", 10), mapping.get("new", 20)
        new_ratio = (new_size / old_size) if old_size else 1.0
        if "old_new" in benchmark_metrics_df.columns:
            # Absent on datapoints that have not been through a submission, so it is read
            # defensively rather than indexed into.
            states = benchmark_metrics_df["old_new"].astype(str)
            scatter_size = [size * new_ratio if state == "new" else size for size, state in zip(base_sizes, states)]
        else:
            scatter_size = list(base_sizes)
        if "Highlight" in benchmark_metrics_df.columns:
            scatter_size = [
                item * 2 if highlight else item
                for item, highlight in zip(scatter_size, benchmark_metrics_df["Highlight"])
            ]

        # Colour is the tool's own where the datapoint is coloured, and the shared muted grey
        # otherwise. Highlighting a tool colours every one of its datapoints, including the ones
        # that are grey by default, which is how a tool's spread becomes visible on demand
        # without colouring every tool's spread all of the time.
        highlight_tool = str(highlight_tool) if highlight_tool else None
        colors, opacities, line_widths = _main_metric_marker_arrays(
            benchmark_metrics_df,
            coloured=coloured,
            leading=leading,
            highlight_tool=highlight_tool,
            highlight_color=highlight_color,
            software_colors=software_colors,
        )

        # Set markers based on software tool (if colorblind mode is enabled). `.get` rather than
        # `[...]`: an unregistered tool must fall back, not raise.
        markers = [software_markers.get(software, "circle") for software in benchmark_metrics_df["software_name"]]

        benchmark_metrics_df["color"] = colors
        benchmark_metrics_df["opacity"] = opacities
        benchmark_metrics_df["line_width"] = line_widths
        benchmark_metrics_df["hover_text"] = hover_texts
        benchmark_metrics_df["scatter_size"] = scatter_size

        # Each tool's best run is drawn as a star, the same mark the table puts beside it, so
        # the point the ranking is about can be found in the cloud without reading any label.
        # Not in colourblind mode: there the symbol is how a tool is identified at all, and
        # restyling one point per tool would make every tool's best look like the same tool.
        if colorblind_mode:
            benchmark_metrics_df["marker"] = markers
        else:
            benchmark_metrics_df["marker"] = [
                BEST_MARKER_SYMBOL if idx in best_indices else "circle" for idx in benchmark_metrics_df.index
            ]

        # Fixed axis range (not the data's own min/max): both precision and AUC are bounded
        # in [0, 1], so a shared, fixed range keeps the quadrant boundary and background
        # gradient below anchored to the same meaningful midpoint every time, and padding
        # past 0/1 (rather than clipping exactly at them) keeps points at the edges visible.
        layout_xaxis_range = list(MAIN_PLOT_AXIS_RANGE)
        layout_yaxis_range = list(MAIN_PLOT_AXIS_RANGE)
        layout_xaxis_title = f"Peptide {level_title}"
        layout_yaxis_title = f"Amino Acid {level_title}"

        fig = go.Figure(
            layout_yaxis_range=layout_yaxis_range,
            layout_xaxis_range=layout_xaxis_range,
        )

        _add_quadrant_background(fig)

        # One trace per software tool, not one per colour. Grouping by colour would split a
        # tool whose datapoints are partly coloured and partly greyed into two traces, giving it
        # two identical legend entries -- the same duplication this redesign exists to remove.
        # Per-point colour, size and opacity are passed as arrays within the one trace instead.
        for software in benchmark_metrics_df["software_name"].drop_duplicates():
            tmp_df = benchmark_metrics_df[benchmark_metrics_df["software_name"] == software]
            symbol = tmp_df["marker"].iloc[0] if colorblind_mode else "circle"

            # Plotly takes a legend swatch from the trace's *first* point, so a tool whose first
            # row happens to be a greyed datapoint would advertise itself in grey. The legend has
            # to say what a tool's colour is, not what one arbitrary datapoint is currently drawn
            # in, so the entry comes from a pointless proxy trace in the tool's own colour and
            # the data trace itself is kept out of the legend. Both share a legendgroup, so
            # clicking the entry still toggles the tool's datapoints.
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(color=software_colors.get(str(software), "gray"), size=12, symbol=symbol),
                    name=str(software),
                    legendgroup=str(software),
                    showlegend=True,
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=tmp_df[f"peptide_{evaluation_type}_{level}"],
                    y=tmp_df[f"aa_{evaluation_type}_{level}"],
                    mode="markers",
                    hovertext=tmp_df["hover_text"],
                    hoverinfo="text",
                    customdata=tmp_df["id"] if "id" in tmp_df.columns else None,
                    marker=dict(
                        color=list(tmp_df["color"]),
                        opacity=list(tmp_df["opacity"]),
                        size=list(tmp_df["scatter_size"]),
                        showscale=False,
                        # Per point, not per trace: within one tool's trace the best run carries
                        # the star and the rest stay circles.
                        symbol=list(tmp_df["marker"]),
                        line=dict(color="rgba(0,0,0,0.45)", width=list(tmp_df["line_width"])),
                    ),
                    name=str(software),
                    legendgroup=str(software),
                    showlegend=False,
                )
            )

        # Labels are drawn beside the datapoints they belong to, joined by a leader line, rather
        # than printed on top of every point. Only the datapoints worth labelling get one: the
        # coloured ones, or every datapoint of a highlighted tool. Labelling all of them at once
        # is exactly the clutter this replaces.
        annotation_points = []
        for idx in benchmark_metrics_df.index:
            tool = str(benchmark_metrics_df.at[idx, "software_name"])
            if highlight_tool is not None:
                if tool != highlight_tool:
                    continue
            elif not coloured.at[idx]:
                continue
            parts = [
                f"{column}: {_display_value(benchmark_metrics_df.at[idx, column])}"
                for column in annotation_columns
                if column in benchmark_metrics_df.columns and not _is_blank(benchmark_metrics_df.at[idx, column])
            ]
            if not parts:
                continue
            x_value = benchmark_metrics_df.at[idx, f"peptide_{evaluation_type}_{level}"]
            y_value = benchmark_metrics_df.at[idx, f"aa_{evaluation_type}_{level}"]
            if not isinstance(x_value, (int, float)) or not isinstance(y_value, (int, float)):
                continue
            if np.isnan(x_value) or np.isnan(y_value):
                continue
            annotation_points.append(
                {
                    "x": x_value,
                    "y": y_value,
                    "text": "<br>".join(parts),
                    "color": software_colors.get(tool, "gray"),
                }
            )
        for annotation in _leader_line_annotations(annotation_points):
            fig.add_annotation(**annotation)

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
            - muted_tools: Iterable[str] - tools that are never coloured, selected or not
            - selected_ids: Iterable[str] - ProteoBench IDs coloured regardless of rank
            - explicit_selection: bool - colour exactly selected_ids and nothing else
            - highlight_tool: str - tool to emphasise, dimming the others

        Returns
        -------
        go.Figure
            A 1x2 subplot figure: peptide-level curve (left), amino-acid-level curve (right).
        """
        evaluation_type = kwargs.get("evaluation_type", "mass")
        allow_il = kwargs.get("allow_il", True)
        allow_deamidation = kwargs.get("allow_deamidation", False)
        software_colors = kwargs.get("software_colors", SOFTWARE_COLORS)
        muted_tools = kwargs.get("muted_tools", ())
        selected_ids = kwargs.get("selected_ids", ())
        explicit_selection = kwargs.get("explicit_selection", False)
        highlight_tool = kwargs.get("highlight_tool", None)

        ambiguity_combo = _ambiguity_combo_for(evaluation_type, allow_il, allow_deamidation)

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

        # Ranked and coloured exactly as the scatter is, so the two views of the same selection
        # agree about which datapoint is a tool's best and which are present for context.
        ranks, best_by_tool = rank_within_tools(benchmark_metrics_df, evaluation_type, ambiguity_combo)
        display_labels = build_display_labels(benchmark_metrics_df, ranks=ranks)
        variants = build_variant_descriptions(benchmark_metrics_df)
        coloured = resolve_coloured_datapoints(
            benchmark_metrics_df,
            best_by_tool=best_by_tool,
            muted_tools=muted_tools,
            selected_ids=selected_ids,
            explicit_only=explicit_selection,
        )
        leading = leading_datapoints(benchmark_metrics_df, coloured, ranks)
        ticked_ids = {str(point_id) for point_id in selected_ids}
        highlight_tool = str(highlight_tool) if highlight_tool else None

        # One legend entry per tool, in the tool's own colour, exactly as in the scatter. Giving
        # every curve its own entry put one row per datapoint in the legend -- ninety-one of them
        # on a full results set -- and coloured each row by whether that curve happens to be
        # greyed. Which datapoint a curve is belongs in the hover, the on-plot label and the
        # table; the legend's job is to say which colour means which tool.
        for software in benchmark_metrics_df["software_name"].drop_duplicates():
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="lines",
                    line=dict(color=software_colors.get(str(software), "gray"), width=2.4),
                    name=str(software),
                    legendgroup=str(software),
                    showlegend=True,
                    hoverinfo="skip",
                ),
                row=1,
                col=1,
            )

        for col_idx, level in enumerate(_LEVELS, start=1):
            for idx, row in benchmark_metrics_df.iterrows():
                curve = _get_metrics_leaf(row, level, evaluation_type, ambiguity_combo).get("curve")
                if not curve or not curve.get("coverage"):
                    continue  # degenerate curve (e.g. all-identical scores) or legacy datapoint
                software = str(row["software_name"])
                label = display_labels.at[idx]
                # Same order as the scatter's hover box: the name, then what this run was.
                variant = f"<br><i>{variants.at[idx]}</i>" if variants.at[idx] else ""
                tool_color = software_colors.get(software, "gray")
                is_highlighted = highlight_tool is not None and software == highlight_tool

                # Once the viewer has ticked a selection, the unticked curves are not drawn at
                # all. Leaving them in as grey context ignores the only control the table offers
                # over this view, and costs the whole payload no matter what is ticked. The test
                # is "ticked", not "coloured", so a greyed-out tool that is ticked still appears,
                # in grey, as "Grey out tools" promises. The highlighted tool is kept so
                # highlighting still shows that tool's other runs.
                is_ticked = (not explicit_selection) or str(row.get("id")) in ticked_ids
                if not is_ticked and not is_highlighted:
                    continue

                # A non-best curve is greyed and made substantially transparent rather than
                # removed. A full-width line covers far more of the plot than a marker, so
                # without the transparency a tool with fifteen submissions would swamp a tool
                # with one even when every one of those lines is grey.
                if highlight_tool is not None and not is_highlighted:
                    color, width, opacity = (
                        (tool_color if coloured.at[idx] else MUTED_COLOR),
                        1.0,
                        DIMMED_OPACITY / 2,
                    )
                elif is_highlighted:
                    color, width, opacity = tool_color, (2.6 if coloured.at[idx] else 1.7), 0.95
                elif coloured.at[idx] and idx in leading:
                    color, width, opacity = tool_color, 2.4, 0.95
                elif coloured.at[idx]:
                    color, width, opacity = tool_color, 1.4, SECONDARY_CURVE_OPACITY
                else:
                    color, width, opacity = MUTED_COLOR, 1.1, MUTED_CURVE_OPACITY

                thinned_coverage, thinned_precision = thin_curve(curve["coverage"], curve["precision"])
                fig.add_trace(
                    go.Scatter(
                        x=thinned_coverage,
                        y=thinned_precision,
                        mode="lines",
                        name=label,
                        legendgroup=software,
                        showlegend=False,
                        opacity=opacity,
                        line=dict(color=color, width=width),
                        customdata=[row.get("id")] if "id" in benchmark_metrics_df.columns else None,
                        hovertemplate=(
                            f"{label}{variant}<br>Coverage: %{{x:.3f}}<br>Precision: %{{y:.3f}}<extra></extra>"
                        ),
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
            - highlight_id: str - ProteoBench ID to emphasise. Across several tools this raises
              every datapoint of that software; within one tool it raises just that datapoint.

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
        # Identity options, applied uniformly to every in-depth figure so one selection reads the
        # same way whichever plot it is looked at in.
        identity = {"highlight_id": kwargs.get("highlight_id")}

        # Generate PTM plots
        plots["ptm_overview"] = self.plot_ptm_overview(
            performance_data, mod_labels=mod_labels, software_colors=software_colors, **identity
        )

        plots["ptm_specific"] = {}
        for mod_label in mod_labels:
            plots["ptm_specific"][mod_label] = self.plot_ptm_specific(
                performance_data, mod_label=mod_label, software_colors=software_colors, **identity
            )

        # Generate spectrum feature plot
        plots["spectrum_feature"] = {}
        for feature in features:
            plots["spectrum_feature"][feature] = {}
            for evaluation_type in evaluation_types:
                plots["spectrum_feature"][feature][evaluation_type] = self.plot_spectrum_feature(
                    performance_data,
                    feature=feature,
                    evaluation_type=evaluation_type,
                    software_colors=software_colors,
                    **identity,
                )

        # Generate species plot
        plots["species_overview"] = {}
        for evaluation_type in evaluation_types:
            plots["species_overview"][evaluation_type] = self.plot_species_overview(
                performance_data, evaluation_type=evaluation_type, software_colors=software_colors, **identity
            )

        # Generate FASTA-category overview plot
        plots["in_fasta_overview"] = self.plot_infasta_overview(performance_data, **identity)

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
            {"plots": ["in_fasta_overview"], "columns": 1, "title": "FASTA Analysis"},
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
            "in_fasta_overview": "Breakdown of predictions into correctly sequenced, incorrect but present "
            "elsewhere in the species' proteome, and not present in the proteome at all.",
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

            The background is shaded from light (bottom-left) to dark (top-right): the further into
            the top-right corner a point sits, the better it performs on both axes at once. Dashed
            lines at the midpoint of each axis split the plot into four named regions:

            - **Good performance** (top-right) - both the peptide- and amino-acid-level metrics are
              high.
            - **Near-miss** (top-left) - the peptide-level metric is low but the amino-acid-level
              metric is high. Often just one or a few residues off from the true sequence.
            - **Low performance** (bottom-left) - both metrics are low.
            - **Alternative candidate** (bottom-right) - the peptide-level metric is high but the
              amino-acid-level metric is low, suggesting a fully different peptide rather than a
              near miss when the prediction is wrong. This region is expected to be sparse.

            **Select the classification metric** - which metric is shown on both axes:

            - **Precision** - the fraction of the reported predictions that is correct, over every
              prediction with no score threshold applied: `precision = correct predictions /
              reported predictions`. Evaluates how reliable the reported sequences are at a tool's
              single, fixed operating point.
            - **AUC** - the area under the tool's precision-vs-coverage curve (average precision),
              swept across every possible score threshold; the underlying curve is shown in the
              adjacent "Precision-Coverage Curves" tab. Evaluates a tool's overall ranking quality
              rather than one operating point, and is `N/A` for tools that don't report a real
              per-residue confidence score.

            **Select the stringency of evaluation** - when a prediction counts as correct:

            - **Exact** - the predicted sequence must match the ground truth exactly, including the
              modifications and their positions. Two toggles relax this for ambiguities inherent to
              the data: **allow I/L mismatches** (isoleucine and leucine are isobaric) and **allow
              deamidation mismatches** (deamidated Q/N are essentially isobaric with E/D).
            - **Mass-based** - a prediction also counts as correct when it matches the ground truth
              through the longest mass-matching prefix and suffix, using a cumulative mass tolerance
              of 50 ppm and an individual amino-acid tolerance of 20 ppm. This already cannot
              distinguish I/L or deamidation regardless of the toggles above, so both are forced on
              and disabled. Mass-based numbers are therefore always equal to or higher than the
              exact numbers.

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

    @staticmethod
    def _in_depth_styling(
        benchmark_metrics_df: pd.DataFrame,
        software_colors: Dict[str, str],
        **kwargs,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Labels, colours and emphasis for one in-depth figure.

        Every in-depth plot identifies its marks the same way, so the three decisions are made
        once here: what each datapoint is called, what colour it takes (shaded only when the
        selection is a single tool), and which datapoints are emphasised while one is
        highlighted.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            The selected datapoints.
        software_colors : Dict[str, str]
            Colour per tool.
        **kwargs : dict
            ``highlight_id`` and ``evaluation_type``.

        Returns
        -------
        tuple of (pd.Series, pd.Series, pd.Series)
            Display labels, colours, and a boolean emphasis mask, all aligned to the frame's
            index.
        """
        evaluation_type = kwargs.get("evaluation_type", "mass")
        ranks, _ = rank_within_tools(benchmark_metrics_df, evaluation_type)
        labels = build_display_labels(benchmark_metrics_df, ranks=ranks)
        colors = assign_datapoint_colors(benchmark_metrics_df, software_colors, ranks=ranks)
        emphasised = resolve_emphasis(benchmark_metrics_df, kwargs.get("highlight_id"))
        return labels, colors, emphasised

    def plot_ptm_overview(
        self,
        benchmark_metrics_df: pd.DataFrame,
        mod_labels: List[str],
        software_colors: Dict[str, str] = SOFTWARE_COLORS,
        **kwargs,
    ):
        """
        Plot the correct share of each modification's ground-truth occurrences, per datapoint.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            The selected datapoints.
        mod_labels : List[str]
            Modifications to plot, in display order.
        software_colors : Dict[str, str]
            Colour per tool.
        **kwargs : dict
            ``highlight_id``, as documented on
            :meth:`generate_in_depth_plots`.

        Returns
        -------
        go.Figure
            One line per datapoint over the modifications.
        """
        labels, colors, emphasised = self._in_depth_styling(benchmark_metrics_df, software_colors, **kwargs)
        fig = go.Figure()
        for idx, row in benchmark_metrics_df.iterrows():
            try:
                ptm_data = row["results"]["in_depth"]["PTM"]
            except (KeyError, TypeError):
                # Legacy datapoint submitted before this metric existed, skipped the way
                # plot_infasta_overview already skips it and the main plot hides datapoints
                # missing newer fields.
                continue
            x, y = self.get_modification_scores(ptm_data, mod_labels=mod_labels)
            style = _IN_DEPTH_LINE_EMPHASIS[bool(emphasised.at[idx])]

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines+markers",
                    name=labels.at[idx],
                    legendgroup=str(row["software_name"]),
                    line=dict(color=colors.at[idx], width=style["width"]),
                    marker=dict(color=colors.at[idx], size=style["size"]),
                    opacity=style["opacity"],
                    customdata=[row.get("id")] * len(x) if "id" in benchmark_metrics_df.columns else None,
                    hovertemplate=f"<b>{labels.at[idx]}</b><br>%{{x}}<br>Correct of ground truth: %{{y:.3f}}<extra></extra>",
                )
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
        **kwargs,
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
                opacity=0.28,
                hoverinfo="skip",
            )
        )

        labels, colors, emphasised = self._in_depth_styling(benchmark_metrics_df, software_colors, **kwargs)
        for idx, row in benchmark_metrics_df.iterrows():
            try:
                ptm_data = row["results"]["in_depth"]["PTM"]
                mod_entry = ptm_data[mod_label]
            except (KeyError, TypeError):
                continue  # legacy datapoint, or a modification this one never recorded

            # To make division by 0 impossible

            x = mod_entry["correct_gt"] / (mod_entry["counts_gt"] + EPSILON)
            y = mod_entry["correct_dn"] / (mod_entry["counts_dn"] + EPSILON)
            style = _IN_DEPTH_LINE_EMPHASIS[bool(emphasised.at[idx])]
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    name=labels.at[idx],
                    legendgroup=str(row["software_name"]),
                    marker=dict(
                        color=colors.at[idx],
                        size=style["size"] + 6,
                        line=dict(color="rgba(0,0,0,0.45)", width=1),
                    ),
                    opacity=style["opacity"],
                    customdata=[row.get("id")] if "id" in benchmark_metrics_df.columns else None,
                    hovertemplate=(
                        f"<b>{labels.at[idx]}</b><br>Ground-truth precision: %{{x:.3f}}"
                        "<br>De novo precision: %{y:.3f}<extra></extra>"
                    ),
                )
            )

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
            if mod_label not in mod_dict:
                continue  # a modification this datapoint never recorded
            x.append(mod_label)
            # EPSILON must guard the denominator (as plot_ptm_specific does), not be added
            # to the final ratio -- `a / b + EPSILON` is `(a / b) + EPSILON` in Python, which
            # still raises ZeroDivisionError when counts_gt is 0 (a modification that never
            # occurs in the ground truth for the current view, e.g. a rare PTM on a small
            # per-species selection).
            y.append(mod_dict[mod_label]["correct_gt"] / (mod_dict[mod_label]["counts_gt"] + EPSILON))
        return x, y

    def _plot_binned_in_depth(
        self,
        benchmark_metrics_df: pd.DataFrame,
        block: str,
        group: Optional[str],
        x_title: str,
        subplot_title: str,
        evaluation_type: str,
        software_colors: Dict[str, str],
        **kwargs,
    ) -> go.Figure:
        """
        Draw the precision-per-category view shared by the spectrum-feature and species plots.

        Both are the same figure over different categories: one line per datapoint across the
        categories, with the spectrum count per category underneath. Factored into one method so
        the labelling and colouring rules cannot drift apart between them.

        The per-datapoint dicts are read directly rather than melted through a DataFrame and
        recovered with ``eval``, which is how this previously round-tripped its values through
        strings: an uploaded result file could run arbitrary code that way
        (GHSA-p237-rc4h-82vq). Anything stored under a category still goes through
        :func:`_metrics_or_empty`, so a value that is not a metrics dict raises rather than
        being quietly dropped, and is never evaluated as Python.

        A category a datapoint has no entry for yields no point, so its line breaks there
        instead of being drawn through zero. A tool that was not measured in some bin has no
        precision there; drawing it at zero states a result that was never obtained, and makes
        the line dive to the floor and back.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            The selected datapoints.
        block : str
            In-depth block to read, ``"Spectrum"`` or ``"Species"``.
        group : str, optional
            Sub-key within the block, the feature name for ``"Spectrum"``; ``None`` for
            ``"Species"``, whose categories sit directly under the block.
        x_title : str
            Axis title for the category axis.
        subplot_title : str
            Title above the precision panel.
        evaluation_type : str
            ``"mass"`` or ``"exact"``, selecting which rate to plot.
        software_colors : Dict[str, str]
            Colour per tool.
        **kwargs : dict
            ``highlight_id``.

        Returns
        -------
        go.Figure
            Two stacked panels: precision per category, and spectra per category.
        """
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.8, 0.2],
            vertical_spacing=0,
            subplot_titles=(subplot_title, None),
        )

        def entries_for(row: pd.Series) -> dict:
            """The category dict of one datapoint, or empty when the block is absent."""
            try:
                node = row["results"]["in_depth"][block]
            except (KeyError, TypeError):
                return {}
            if group is not None:
                node = node.get(group, {}) if isinstance(node, dict) else {}
            return node if isinstance(node, dict) else {}

        # Categories in first-seen order across the selection, which is the order the previous
        # DataFrame-of-dicts produced and the order the stored dicts are written in.
        categories: List[str] = []
        for _, row in benchmark_metrics_df.iterrows():
            for key in entries_for(row):
                if str(key) not in categories:
                    categories.append(str(key))

        if len(benchmark_metrics_df) == 0 or not categories:
            fig.add_trace(go.Scatter())
            fig.add_trace(go.Bar())
            fig.update_layout(
                height=600,
                width=600,
                xaxis=dict(title=None, color="black"),
                yaxis=dict(title="Precision", color="black"),
                xaxis2=dict(title=x_title, color="black"),
                yaxis2=dict(title="Number of Spectra", color="black"),
                margin=dict(t=50),
            )
            fig.update_yaxes(autorange="reversed", row=2, col=1)
            return fig

        labels, colors, emphasised = self._in_depth_styling(
            benchmark_metrics_df, software_colors, evaluation_type=evaluation_type, **kwargs
        )

        counts_per_category: Dict[str, List[float]] = {category: [] for category in categories}
        for idx, row in benchmark_metrics_df.iterrows():
            entries = entries_for(row)
            y_values: List[Optional[float]] = []
            for category in categories:
                if category not in entries:
                    # Not measured here: leave the gap for `connectgaps=False` to break on.
                    y_values.append(None)
                    continue
                # Stored, so it has to be metrics. `_metrics_or_empty` returns the dict, fills a
                # recorded-but-empty entry from EMPTY_METRICS, and raises TypeError on anything
                # else -- never evaluating it, which is what made this path exploitable.
                entry = _metrics_or_empty(entries[category])
                value = entry.get(evaluation_type)
                y_values.append(
                    float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
                )
                if isinstance(entry.get("n_spectra"), (int, float)):
                    counts_per_category[category].append(float(entry["n_spectra"]))

            style = _IN_DEPTH_LINE_EMPHASIS[bool(emphasised.at[idx])]
            fig.add_trace(
                go.Scatter(
                    x=categories,
                    y=y_values,
                    mode="lines+markers",
                    name=labels.at[idx],
                    legendgroup=str(row["software_name"]),
                    line=dict(color=colors.at[idx], width=style["width"]),
                    marker=dict(color=colors.at[idx], size=style["size"]),
                    opacity=style["opacity"],
                    connectgaps=False,
                    customdata=[row.get("id")] * len(categories) if "id" in benchmark_metrics_df.columns else None,
                    hovertemplate=f"<b>{labels.at[idx]}</b><br>%{{x}}<br>Precision: %{{y:.3f}}<extra></extra>",
                ),
                row=1,
                col=1,
            )

        # Median spectrum count per category, as before. Note that this panel does not actually
        # respond to the selection: the spectrum count is a property of the benchmark set, so it
        # is identical for every datapoint, which the hover text now states rather than implying
        # a per-tool breakdown.
        bar_counts = [float(np.median(counts_per_category[c])) if counts_per_category[c] else 0.0 for c in categories]
        hovertexts = [
            f"{category}<br>Spectra in the benchmark set: {int(count)}<br>"
            "Identical for every datapoint, so this panel does not change with the selection"
            for category, count in zip(categories, bar_counts)
        ]
        fig.add_trace(
            go.Bar(
                x=categories,
                y=bar_counts,
                hovertext=hovertexts,
                hoverinfo="text",
                marker=dict(color="gray"),
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            height=600,
            width=600,
            xaxis=dict(title=None, color="black"),
            yaxis=dict(title="Precision", color="black"),
            xaxis2=dict(title=x_title, color="black"),
            yaxis2=dict(title="Number of Spectra", color="black"),
            margin=dict(t=50),
        )
        fig.update_yaxes(autorange="reversed", row=2, col=1)
        return fig

    def plot_spectrum_feature(
        self,
        benchmark_metrics_df,
        feature,
        evaluation_type="mass",
        software_colors=SOFTWARE_COLORS,
        **kwargs,
    ):
        """
        Plot precision across the bins of one spectrum feature, per datapoint.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            The selected datapoints.
        feature : str
            Spectrum feature to plot, a key of ``results["in_depth"]["Spectrum"]``.
        evaluation_type : str
            ``"mass"`` or ``"exact"``.
        software_colors : Dict[str, str]
            Colour per tool.
        **kwargs : dict
            ``highlight_id``.

        Returns
        -------
        go.Figure
            Precision per bin, with the spectrum count per bin underneath.
        """
        return self._plot_binned_in_depth(
            benchmark_metrics_df,
            block="Spectrum",
            group=feature,
            x_title=str(feature),
            subplot_title=f"{feature} vs Precision",
            evaluation_type=evaluation_type,
            software_colors=software_colors,
            **kwargs,
        )

    def plot_species_overview(
        self,
        benchmark_metrics_df,
        evaluation_type="mass",
        software_colors=SOFTWARE_COLORS,
        **kwargs,
    ):
        """
        Plot precision per species, per datapoint.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            The selected datapoints.
        evaluation_type : str
            ``"mass"`` or ``"exact"``.
        software_colors : Dict[str, str]
            Colour per tool.
        **kwargs : dict
            ``highlight_id``.

        Returns
        -------
        go.Figure
            Precision per species, with the spectrum count per species underneath.
        """
        return self._plot_binned_in_depth(
            benchmark_metrics_df,
            block="Species",
            group=None,
            x_title="Species",
            subplot_title="Species vs Precision",
            evaluation_type=evaluation_type,
            software_colors=software_colors,
            **kwargs,
        )

    def plot_infasta_overview(self, benchmark_metrics_df: pd.DataFrame, **kwargs) -> go.Figure:
        """
        Stacked bar chart of the FASTA-category breakdown (correct / in FASTA / not in FASTA),
        one bar per datapoint. Reads the per-datapoint proportions precomputed
        by `DenovoDatapoint.get_infasta_metrics` at benchmarking time (stored under
        `results["in_depth"]["in_FASTA"]`) -- never a live groupby over raw intermediate data,
        which isn't persisted for a submitted datapoint in the first place.
        """
        fig = go.Figure()

        labels, _, _ = self._in_depth_styling(benchmark_metrics_df, SOFTWARE_COLORS, **kwargs)

        # One bar per datapoint, labelled per datapoint. Previously the x value was the tool
        # name, so two submissions of one tool landed on the same category and Plotly summed
        # their bars: a tool with three runs produced a single stack adding to 300%, with no
        # indication that it was not one result. Identity has to be per datapoint here for the
        # figure to be correct, not merely for it to be readable.
        bar_labels = []
        proportions_per_category = {category: [] for category in INFASTA_CATEGORIES}
        for idx, row in benchmark_metrics_df.iterrows():
            try:
                infasta = row["results"]["in_depth"]["in_FASTA"]
            except (KeyError, TypeError):
                # Legacy datapoint submitted before this metric existed -- silently skipped,
                # matching how the main plot hides datapoints missing newer fields.
                continue
            bar_labels.append(labels.at[idx])
            for category in INFASTA_CATEGORIES:
                proportions_per_category[category].append(infasta["proportions"].get(category, 0.0))

        for category in INFASTA_CATEGORIES:
            fig.add_bar(
                name=INFASTA_LABELS[category],
                x=bar_labels,
                y=proportions_per_category[category],
                marker_color=INFASTA_COLORS[category],
                marker_line_width=0,
                text=[f"{v:.0%}" if v >= 0.03 else "" for v in proportions_per_category[category]],
                textposition="inside",
                textfont=dict(color="white", size=13),
                hovertemplate="%{y:.1%}<extra>%{fullData.name}</extra>",
            )

        fig.update_layout(
            barmode="stack",
            width=700,
            height=450,
            title=dict(text="De novo sequencing accuracy by tool", font=dict(size=16)),
            yaxis=dict(title="Proportion of spectra", tickformat=".0%", range=[0, 1]),
            xaxis=dict(title="Datapoint", automargin=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
            margin=dict(t=70, b=50, l=60, r=30),
        )
        return fig
