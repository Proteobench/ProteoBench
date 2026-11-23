"""
The accuracy-vs-abundance comparison figure of the LFQ quant modules.

The figure answers one question: does a workflow stay accurate over the whole dynamic range, or
only where the signal is strong? One column per species plots a summary of the absolute
quantification error (``|epsilon|``) against abundance rank, one line per workflow, so a workflow
that is accurate on average but falls apart at the low-abundance end is distinguished from one
that is uniformly mediocre. This matters most for the low-input modules, where the differences
between tools concentrate at the low-abundance end.

Two choices change what the figure actually measures, so both are dropdowns on the figure rather
than being fixed in code:

``STATISTICS``
    Whether a bin is summarized by the median or the mean of its absolute errors, with the
    matching interval (a distribution-free confidence interval of the median, or the standard
    error of the mean). Absolute errors are bounded below by zero and right-skewed, so the two
    can rank workflows differently; the median is the default.

``VIEWS``
    Which precursors are compared, and how they are binned. Restricting to the precursors every
    workflow quantified makes the comparison like-for-like but hides what a workflow achieved on
    the precursors only it found; binning each workflow on its own abundance rank keeps every
    precursor but means a bin no longer holds the same precursors for each workflow. Because that
    caveat is easy to overlook, every point reports in its hover text how much of its bin the
    other workflows also have in that bin.

Switching either dropdown only restyles the figure: every view is drawn into it once and toggled
by visibility, and the statistic is a restyle of values already present, so nothing is recomputed
and no Streamlit rerun is needed.

A plot generator opts into the figure by forwarding to ``plot_accuracy_vs_abundance`` from its
``generate_comparison_plots``; see :class:`~proteobench.plotting.plot_generator_lfq_lowinput.
LFQLowInputPlotGenerator`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from proteobench.plotting.utils.plotly_helpers import empty_figure, hex_to_rgba

#: Left-to-right species order of the accuracy-vs-abundance figure. Ordered by expected A-vs-B
#: ratio, from the species depleted in condition A to the unchanged human background, so the
#: panel titles read as a ratio series rather than an arbitrary order.
SPECIES_ORDER = ("ECOLI", "YEAST", "HUMAN")

#: Columns of the intermediate table the accuracy-vs-abundance plot needs, on top of the
#: precursor identifier column.
REQUIRED_COLUMNS = ("species", "epsilon", "log_Intensity_mean_A", "log_Intensity_mean_B")

#: Intermediate column holding the expected log2 A-vs-B ratio of a precursor's species.
EXPECTED_RATIO_COLUMN = "log2_expectedRatio"

#: Pixel height of the accuracy-vs-abundance figure, and the margins reserved for its header
#: (title, the two dropdowns and the caveat line) and for its axis titles.
FIGURE_HEIGHT = 715
TOP_MARGIN = 225
BOTTOM_MARGIN = 80

#: Distance from the top of the figure, in pixels, of each header element. They are stacked
#: rather than placed side by side so that they cannot overlap each other when the figure is
#: rendered into a narrow container.
STATISTIC_MENU_Y = 52
VIEW_MENU_Y = 92
CAVEAT_Y = 142

#: Normal quantile setting the coverage of both error bands. 1.96 gives 95%.
INTERVAL_Z = 1.96


@dataclass(frozen=True)
class _Statistic:
    """
    One way of summarizing the absolute errors in a bin, as offered by the statistic dropdown.

    Parameters
    ----------
    key : str
        Identifier, and the prefix of the columns ``_abundance_bin_statistics`` computes for it.
    label : str
        Text of the dropdown entry.
    axis_title : str
        Y axis title while this statistic is shown.
    interval_label : str
        Name of the accompanying interval, as it appears in the hover text.
    """

    key: str
    label: str
    axis_title: str
    interval_label: str

    @property
    def centre_column(self) -> str:
        """
        Name of the column holding the summarized value.

        Returns
        -------
        str
            Column name in a bin-statistics table.
        """
        return self.key

    @property
    def low_column(self) -> str:
        """
        Name of the column holding the lower bound of the interval.

        Returns
        -------
        str
            Column name in a bin-statistics table.
        """
        return f"{self.key}_low"

    @property
    def high_column(self) -> str:
        """
        Name of the column holding the upper bound of the interval.

        Returns
        -------
        str
            Column name in a bin-statistics table.
        """
        return f"{self.key}_high"


@dataclass(frozen=True)
class _View:
    """
    One combination of precursor set and binning, as offered by the view dropdown.

    Parameters
    ----------
    key : str
        Identifier, used to tag the traces belonging to this view.
    label : str
        Text of the dropdown entry.
    caveat : str
        Line shown under the dropdowns while this view is active, stating what is compared.
    shared_only : bool
        Whether the view is restricted to precursors every workflow quantified.
    common_bins : bool
        Whether a precursor falls in the same bin for every workflow. When False each workflow is
        binned on its own abundance rank, so a bin need not hold the same precursors.
    """

    key: str
    label: str
    caveat: str
    shared_only: bool
    common_bins: bool


#: The statistics a bin can be summarized with. Absolute errors are bounded below by zero and
#: right-skewed, so the two can rank workflows differently; the first entry is the default, and
#: is the median for that reason.
STATISTICS = (
    _Statistic(
        key="median",
        label="Median absolute error",
        axis_title="Median |epsilon| (|measured - expected| log2FC)",
        interval_label="95% CI",
    ),
    _Statistic(
        key="mean",
        label="Mean absolute error",
        axis_title="Mean |epsilon| (|measured - expected| log2FC)",
        interval_label="±SEM",
    ),
)

#: Which precursors are compared, and how they are binned. Restricting to the precursors every
#: workflow quantified makes the comparison like-for-like but hides what a workflow achieved on
#: the precursors only it found; binning each workflow on its own abundance rank keeps every
#: precursor but means a bin no longer holds the same precursors for each workflow. The first
#: entry is the default, and is the only view in which every bin compares the same precursors.
VIEWS = (
    _View(
        key="shared_common",
        label="Shared precursors, identical set per bin",
        caveat=(
            "Only precursors quantified by every workflow, each one in the same bin for every "
            "workflow: each bin compares exactly the same precursors."
        ),
        shared_only=True,
        common_bins=True,
    ),
    _View(
        key="shared_per_workflow",
        label="Shared precursors, per-workflow rank bins",
        caveat=(
            "Only precursors quantified by every workflow, but each bin holds each workflow's "
            "own abundance-rank interval: the precursors compared within a bin differ (see hover)."
        ),
        shared_only=True,
        common_bins=False,
    ),
    _View(
        key="all_per_workflow",
        label="All precursors, per-workflow rank bins",
        caveat=(
            "Every precursor each workflow quantified, binned by that workflow's own abundance "
            "rank: the precursors compared within a bin differ (see hover)."
        ),
        shared_only=False,
        common_bins=False,
    ),
)


def _accuracy_frame(intermediate: pd.DataFrame, precursor_column_name: str) -> pd.DataFrame:
    """
    Reduce one workflow's intermediate table to what the abundance binning needs.

    Parameters
    ----------
    intermediate : pd.DataFrame
        Intermediate table of one workflow, already checked for the required columns.
    precursor_column_name : str
        Name of the precursor identifier column.

    Returns
    -------
    pd.DataFrame
        The precursor column, ``species``, the absolute error and the mean log intensity over
        both conditions, without duplicated precursors or unusable rows.
    """
    frame = intermediate[[precursor_column_name, *REQUIRED_COLUMNS]].copy()
    frame["abundance"] = 0.5 * (frame["log_Intensity_mean_A"] + frame["log_Intensity_mean_B"])
    frame["abs_err"] = frame["epsilon"].abs()
    frame = frame.dropna(subset=["abs_err", "abundance"]).drop_duplicates(subset=precursor_column_name)
    return frame[[precursor_column_name, "species", "abs_err", "abundance"]]


def _median_with_ci(values: np.ndarray) -> Tuple[float, float, float]:
    """
    Compute the median and a distribution-free confidence interval around it.

    The interval is the order-statistic interval for the median, using the usual normal
    approximation of its rank bounds. Unlike the standard error of the mean it makes no
    assumption about the shape of the distribution, which matters here because absolute errors
    are bounded below by zero and strongly right-skewed.

    Parameters
    ----------
    values : np.ndarray
        Observations. Non-finite values are ignored.

    Returns
    -------
    Tuple[float, float, float]
        The median, the lower bound and the upper bound. The bounds are ``np.nan`` when fewer
        than three finite observations are available.
    """
    finite = np.sort(np.asarray(values, dtype=float)[np.isfinite(values)])
    if finite.size == 0:
        return np.nan, np.nan, np.nan

    median = float(np.median(finite))
    if finite.size < 3:
        return median, np.nan, np.nan

    half_width = INTERVAL_Z * np.sqrt(finite.size) / 2.0
    lower_rank = max(int(np.floor(finite.size / 2.0 - half_width)), 0)
    upper_rank = min(int(np.ceil(finite.size / 2.0 + half_width)) - 1, finite.size - 1)
    return median, float(finite[lower_rank]), float(finite[upper_rank])


def _mean_with_sem(values: np.ndarray) -> Tuple[float, float, float]:
    """
    Compute the mean and the band one standard error of the mean wide around it.

    Parameters
    ----------
    values : np.ndarray
        Observations. Non-finite values are ignored.

    Returns
    -------
    Tuple[float, float, float]
        The mean, the lower bound and the upper bound. The bounds are ``np.nan`` when fewer than
        two finite observations are available.
    """
    finite = np.asarray(values, dtype=float)[np.isfinite(values)]
    if finite.size == 0:
        return np.nan, np.nan, np.nan

    mean = float(finite.mean())
    if finite.size < 2:
        return mean, np.nan, np.nan

    sem = float(finite.std(ddof=1) / np.sqrt(finite.size))
    return mean, mean - sem, mean + sem


def _rank_to_bin(ranks: pd.Series, n_bins: int) -> pd.Series:
    """
    Map fractional abundance ranks onto equal-width rank bins.

    Equal-width bins on a percentile scale are used rather than quantile bins so that bin *k*
    means the same abundance-rank interval for every workflow and every species, which is what
    makes the per-workflow binning views comparable.

    Parameters
    ----------
    ranks : pd.Series
        Fractional ranks in ``(0, 1]``, as returned by ``Series.rank(pct=True)``.
    n_bins : int
        Number of bins the rank range is split into.

    Returns
    -------
    pd.Series
        Zero-based bin index per entry, with the index of ``ranks``.
    """
    return pd.Series(np.minimum((ranks.to_numpy() * n_bins).astype(int), n_bins - 1), index=ranks.index)


def _bin_assignments(subsets: Dict[str, pd.DataFrame], n_bins: int, common_bins: bool) -> Dict[str, pd.Series]:
    """
    Decide which abundance-rank bin each precursor falls in, for each workflow.

    Parameters
    ----------
    subsets : Dict[str, pd.DataFrame]
        Per workflow, its precursors of one species, indexed by precursor.
    n_bins : int
        Number of equal-width abundance-rank bins.
    common_bins : bool
        When True one assignment is computed from the abundance rank averaged over workflows and
        shared by all of them; when False each workflow is binned on its own rank.

    Returns
    -------
    Dict[str, pd.Series]
        Bin index per precursor, per workflow. Empty when a common assignment was asked for but
        no precursor is ranked by every workflow.
    """
    if not common_bins:
        return {label: _rank_to_bin(subset["abundance"].rank(pct=True), n_bins) for label, subset in subsets.items()}

    ranks = pd.DataFrame({label: subset["abundance"].rank(pct=True) for label, subset in subsets.items()}).dropna()
    if ranks.empty:
        return {}

    shared_assignment = _rank_to_bin(ranks.mean(axis=1), n_bins)
    return {label: shared_assignment for label in subsets}


def _bin_overlap(members: Dict[str, Dict[int, set]], label: str, bin_index: int) -> float:
    """
    Compute how much of one workflow's bin the other workflows also have in that bin.

    Parameters
    ----------
    members : Dict[str, Dict[int, set]]
        Per workflow and bin, the precursors that fall in it.
    label : str
        Workflow whose bin the overlap is expressed as a fraction of.
    bin_index : int
        The bin.

    Returns
    -------
    float
        Percentage of this workflow's precursors in the bin that every other workflow also has in
        the same bin. Always 100 when the bins were assigned in common.
    """
    own = members[label][bin_index]
    if not own:
        return np.nan

    shared_in_bin = set(own)
    for other in members:
        if other != label:
            shared_in_bin &= members[other].get(bin_index, set())
    return 100.0 * len(shared_in_bin) / len(own)


def _abundance_bin_statistics(
    frames: Dict[str, pd.DataFrame],
    precursor_column_name: str,
    species: str,
    n_bins: int,
    shared_precursors: Optional[Set[str]],
    common_bins: bool,
) -> Dict[str, pd.DataFrame]:
    """
    Summarize the absolute quantification error of each workflow per abundance-rank bin.

    Abundance ranks are percentiles computed within this species and within a workflow, so they
    describe where a precursor sits in that workflow's own dynamic range for that species. Every
    statistic is computed for every bin, so switching statistic never has to recompute.

    Parameters
    ----------
    frames : Dict[str, pd.DataFrame]
        Per-workflow table with the precursor column, ``species``, ``abs_err`` and ``abundance``.
    precursor_column_name : str
        Name of the precursor identifier column.
    species : str
        Species the statistics are computed for.
    n_bins : int
        Number of equal-width abundance-rank bins.
    shared_precursors : Optional[Set[str]]
        Precursors every workflow quantified. When given, the statistics are restricted to them;
        when None each workflow contributes all its own precursors.
    common_bins : bool
        When True, bins are assigned once from the abundance rank averaged over workflows, so a
        precursor falls in the same bin for every workflow. When False, each workflow is binned
        by its own rank.

    Returns
    -------
    Dict[str, pd.DataFrame]
        Per workflow, one row per populated bin with the columns ``bin``, ``center``,
        ``bin_low``, ``bin_high``, ``n``, ``overlap`` (the percentage of that bin's precursors
        that also sit in the corresponding bin of every other workflow) and, per entry of
        ``STATISTICS``, its summary and interval bounds. Empty when a
        workflow has no precursor of this species.
    """
    subsets: Dict[str, pd.DataFrame] = {}
    for label, frame in frames.items():
        subset = frame[frame["species"] == species]
        if shared_precursors is not None:
            subset = subset[subset[precursor_column_name].isin(shared_precursors)]
        if subset.empty:
            return {}
        subsets[label] = subset.set_index(precursor_column_name)

    assignments = _bin_assignments(subsets, n_bins, common_bins)
    if not assignments:
        return {}

    members: Dict[str, Dict[int, set]] = {}
    tables: Dict[str, pd.DataFrame] = {}
    width = 100.0 / n_bins
    for label, subset in subsets.items():
        assigned = assignments[label].reindex(subset.index).dropna().astype(int)
        if assigned.empty:
            return {}

        members[label] = {}
        rows = []
        for bin_index, group in subset.loc[assigned.index, "abs_err"].groupby(assigned):
            bin_index = int(bin_index)
            members[label][bin_index] = set(group.index)
            median, median_low, median_high = _median_with_ci(group.to_numpy())
            mean, mean_low, mean_high = _mean_with_sem(group.to_numpy())
            rows.append(
                {
                    "bin": bin_index,
                    "center": (bin_index + 0.5) * width,
                    "bin_low": bin_index * width,
                    "bin_high": (bin_index + 1) * width,
                    "n": int(group.size),
                    "median": median,
                    "median_low": median_low,
                    "median_high": median_high,
                    "mean": mean,
                    "mean_low": mean_low,
                    "mean_high": mean_high,
                }
            )
        tables[label] = pd.DataFrame(rows).sort_values("bin").reset_index(drop=True)

    for label, table in tables.items():
        table["overlap"] = [_bin_overlap(members, label, bin_index) for bin_index in table["bin"]]
    return tables


def _species_panel_title(species: str, log2_expected_ratio: Optional[float]) -> str:
    """
    Build the title of a species panel, stating the ratio the species was spiked at.

    Parameters
    ----------
    species : str
        Species name, as it appears in the intermediate table.
    log2_expected_ratio : Optional[float]
        Expected log2 ratio of condition A over condition B for this species. When missing, the
        title carries the species name alone.

    Returns
    -------
    str
        Panel title, with the expected ratio on a second line as both an ``A:B`` ratio and its
        log2 value.
    """
    if log2_expected_ratio is None or not np.isfinite(log2_expected_ratio):
        return f"<b>{species}</b>"

    ratio = Fraction(2.0 ** float(log2_expected_ratio)).limit_denominator(20)
    return (
        f"<b>{species}</b><br>"
        f"<span style='font-size:11px'>expected A:B = {ratio.numerator}:{ratio.denominator} "
        f"(log2FC = {float(log2_expected_ratio):+.2f})</span>"
    )


def _band_y(band: pd.DataFrame, statistic: _Statistic) -> np.ndarray:
    """
    Build the closed polygon of an interval band, upper bound out and lower bound back.

    Parameters
    ----------
    band : pd.DataFrame
        Bin statistics of one workflow, restricted to the bins the band is drawn on.
    statistic : _Statistic
        The statistic whose interval is drawn.

    Returns
    -------
    np.ndarray
        The y values of the polygon, matching an x of the bin centers followed by their reverse.
    """
    return np.concatenate([band[statistic.high_column].to_numpy(), band[statistic.low_column].to_numpy()[::-1]])


def _hover_data(table: pd.DataFrame, statistic: _Statistic) -> np.ndarray:
    """
    Assemble the per-point values the hover template of a summary line refers to.

    Parameters
    ----------
    table : pd.DataFrame
        Bin statistics of one workflow.
    statistic : _Statistic
        The statistic whose interval bounds are shown.

    Returns
    -------
    np.ndarray
        One row per bin, holding the bin size, the overlap percentage, the interval bounds and
        the bin's rank interval, in the order the hover template indexes them.
    """
    columns = ["n", "overlap", statistic.low_column, statistic.high_column, "bin_low", "bin_high"]
    return table[columns].to_numpy()


def _hover_template(statistic: _Statistic, view: _View) -> str:
    """
    Build the hover template of a summary line.

    In a per-workflow binning view the bin does not hold the same precursors for every workflow,
    which is easy to miss when only looking at the lines. The template therefore reports how much
    of the bin the other workflows also have in that bin.

    Parameters
    ----------
    statistic : _Statistic
        The statistic the line shows.
    view : _View
        The view the line belongs to.

    Returns
    -------
    str
        A plotly hover template.
    """
    overlap_line = (
        "Identical precursors compared in this bin<br>"
        if view.common_bins
        else "Also in every other workflow's bin: %{customdata[1]:.0f}% of these precursors<br>"
    )
    return (
        "<b>%{fullData.name}</b><br>"
        "Abundance rank bin: %{customdata[4]:.0f}-%{customdata[5]:.0f}%<br>"
        f"{statistic.label}: " + "%{y:.3f} "
        f"({statistic.interval_label} " + "%{customdata[2]:.3f} to %{customdata[3]:.3f})<br>"
        "Precursors in bin: %{customdata[0]:,.0f}<br>" + overlap_line + "<extra></extra>"
    )


def _winner_hover(winners: Sequence[str], statistic: _Statistic) -> List[str]:
    """
    Build the hover text of the strip marking the most accurate workflow per bin.

    Parameters
    ----------
    winners : Sequence[str]
        Label of the winning workflow per bin.
    statistic : _Statistic
        The statistic the winner was decided on.

    Returns
    -------
    List[str]
        One hover string per bin.
    """
    return [f"Lowest {statistic.label.lower()}: {label}" for label in winners]


def _header_paper_y(pixels_from_top: float) -> float:
    """
    Convert a distance from the top of the figure into the paper y coordinate of that point.

    The title, the dropdowns and the caveat line all sit in the top margin, above the plotting
    area, where paper coordinates exceed 1. Placing them in pixels keeps them from colliding with
    each other and with the two-line panel titles.

    Parameters
    ----------
    pixels_from_top : float
        Distance from the top edge of the figure, in pixels.

    Returns
    -------
    float
        The corresponding y coordinate in paper units.
    """
    plot_height = FIGURE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
    return 1.0 + (TOP_MARGIN - pixels_from_top) / plot_height


def _current_property(trace: go.Scatter, path: str) -> Any:
    """
    Read a possibly nested trace property, so a restyle can leave it unchanged.

    A single restyle sets one list of values per property across all the traces it addresses.
    Traces for which a property does not vary with the statistic are therefore given back the
    value they already carry rather than being left out.

    Parameters
    ----------
    trace : go.Scatter
        The trace to read from.
    path : str
        Property path, with nested properties separated by dots (e.g. ``"marker.color"``).

    Returns
    -------
    Any
        The trace's current value for that property, or None when it is not set.
    """
    value: Any = trace
    for part in path.split("."):
        value = getattr(value, part, None)
        if value is None:
            return None
    return value


def _dropdown(buttons: List[dict], pixels_from_top: float) -> dict:
    """
    Build a left-aligned dropdown in the figure's top margin.

    Parameters
    ----------
    buttons : List[dict]
        The dropdown's entries.
    pixels_from_top : float
        Distance from the top edge of the figure, in pixels.

    Returns
    -------
    dict
        An ``updatemenus`` entry.
    """
    return {
        "type": "dropdown",
        "direction": "down",
        "showactive": True,
        "x": 0.0,
        "y": _header_paper_y(pixels_from_top),
        "xanchor": "left",
        "yanchor": "top",
        "buttons": buttons,
    }


def _statistic_dropdown(figure: go.Figure, trace_statistics: List[Dict[str, Dict[str, Any]]]) -> dict:
    """
    Build the dropdown that switches a bin's summary between the median and the mean.

    Switching is a restyle of values already in the figure rather than a change of which traces
    are visible, so it composes with the view dropdown instead of fighting it.

    Parameters
    ----------
    figure : go.Figure
        The figure whose traces are restyled.
    trace_statistics : List[Dict[str, Dict[str, Any]]]
        Per trace, the properties that differ per statistic, as
        ``{statistic key: {property path: value}}``.

    Returns
    -------
    dict
        An ``updatemenus`` entry.
    """
    indices = [index for index, statistics in enumerate(trace_statistics) if statistics]
    properties = sorted({path for statistics in trace_statistics for s in statistics.values() for path in s})

    buttons = []
    for statistic in STATISTICS:
        restyle = {
            path: [
                trace_statistics[index][statistic.key].get(path, _current_property(figure.data[index], path))
                for index in indices
            ]
            for path in properties
        }
        buttons.append(
            {
                "label": statistic.label,
                "method": "update",
                "args": [restyle, {"yaxis.title.text": statistic.axis_title}, indices],
            }
        )
    return _dropdown(buttons, STATISTIC_MENU_Y)


def _view_dropdown(trace_views: List[Optional[str]], caveat_index: int) -> dict:
    """
    Build the dropdown that switches the precursor set and the binning.

    Parameters
    ----------
    trace_views : List[Optional[str]]
        Per trace, the key of the view it belongs to, or None when it is always shown.
    caveat_index : int
        Index in ``layout.annotations`` of the caveat line each view rewrites.

    Returns
    -------
    dict
        An ``updatemenus`` entry.
    """
    buttons = [
        {
            "label": view.label,
            "method": "update",
            "args": [
                {"visible": [v is None or v == view.key for v in trace_views]},
                {f"annotations[{caveat_index}].text": view.caveat},
            ],
        }
        for view in VIEWS
    ]
    return _dropdown(buttons, VIEW_MENU_Y)


def plot_accuracy_vs_abundance(
    intermediates: Dict[str, pd.DataFrame],
    precursor_column_name: str = "precursor ion",
    species_order: Sequence[str] = SPECIES_ORDER,
    n_bins: int = 12,
    min_per_bin: int = 20,
    colors: Optional[Dict[str, str]] = None,
    expected_ratios: Optional[Dict[str, float]] = None,
) -> go.Figure:
    """
    Compare quantification accuracy over the abundance range of each workflow.

    One column per species shows a summary of the absolute error (``|epsilon|``) of every
    workflow as a function of abundance rank, with an interval around it as a band. A strip
    below each panel marks the workflow with the lowest error in each abundance bin, so it is
    visible at a glance whether one workflow is uniformly more accurate or whether the ranking
    flips with abundance. A gradient bar at the bottom of each panel marks the low-abundance
    (left) and high-abundance (right) end of the axis.

    Two dropdowns on the figure select what is measured:
    ``STATISTICS`` chooses between the median and the mean of a bin, and
    ``VIEWS`` chooses the precursor set and the binning. In the views
    that bin each workflow on its own rank the precursors compared within a bin are not
    identical, so every point reports in its hover text how much of its bin the other
    workflows also have in that bin, and a caveat is shown under the dropdowns.

    Abundance ranks are percentiles computed within a species and within a workflow, so 0% is
    the least abundant and 100% the most abundant precursor of that species for that workflow.

    Parameters
    ----------
    intermediates : Dict[str, pd.DataFrame]
        Mapping of workflow label (e.g. a ProteoBench ID or tool name) to its intermediate
        DataFrame, as produced by ``QuantScoresHYE.generate_intermediate``. Each DataFrame
        must contain the precursor column and ``REQUIRED_COLUMNS``. At least two
        workflows are required.
    precursor_column_name : str, optional
        Name of the precursor identifier column shared across workflows.
    species_order : Sequence[str], optional
        Species to show, and their left-to-right column order in the figure.
    n_bins : int, optional
        Number of equal-width abundance-rank bins each panel is split into.
    min_per_bin : int, optional
        Minimum number of precursors a workflow must have in a bin for it to be drawn.
    colors : Dict[str, str], optional
        Mapping of workflow label to a plotting color (e.g. the software's usual color).
        Labels without an explicit entry fall back to the Plotly qualitative palette.
    expected_ratios : Dict[str, float], optional
        Expected log2 A-vs-B ratio per species, shown in the panel titles. Taken from the
        intermediate table's ``EXPECTED_RATIO_COLUMN`` when not given.

    Returns
    -------
    go.Figure
        The figure, or a placeholder carrying an explanatory message when fewer than two
        workflows are given, required columns are missing, or the workflows share no
        precursors.
    """
    labels = list(intermediates.keys())
    if len(labels) < 2:
        return empty_figure("Select at least two workflows to compare.")

    palette = px.colors.qualitative.Plotly
    color_map = {label: (colors or {}).get(label, palette[i % len(palette)]) for i, label in enumerate(labels)}

    frames: Dict[str, pd.DataFrame] = {}
    ratios: Dict[str, float] = dict(expected_ratios or {})
    for label in labels:
        table = intermediates[label]
        missing = [c for c in (precursor_column_name, *REQUIRED_COLUMNS) if c not in table.columns]
        if missing:
            return empty_figure(f"Workflow '{label}' is missing column(s): {', '.join(missing)}.")

        frames[label] = _accuracy_frame(table, precursor_column_name)
        if EXPECTED_RATIO_COLUMN in table.columns:
            for species, value in table.groupby("species")[EXPECTED_RATIO_COLUMN].median().items():
                ratios.setdefault(str(species), float(value))

    shared = set.intersection(*(set(frame[precursor_column_name]) for frame in frames.values()))
    if not shared:
        return empty_figure("No precursors are shared between the selected workflows.")

    species_list = [s for s in species_order if any((frame["species"] == s).any() for frame in frames.values())]
    if not species_list:
        return empty_figure("No shared precursors match the requested species.")

    fig = make_subplots(
        rows=3,
        cols=len(species_list),
        shared_xaxes=True,
        row_heights=[0.76, 0.12, 0.12],
        vertical_spacing=0.03,
        subplot_titles=[_species_panel_title(species, ratios.get(species)) for species in species_list],
    )

    # Which view a trace belongs to (None: always shown), and the properties that change
    # with the statistic. The dropdowns are built from these two lists.
    trace_views: List[Optional[str]] = []
    trace_statistics: List[Dict[str, Dict[str, Any]]] = []

    def add(trace, row, col, view=None, statistics=None):
        """Add a trace, and record what the dropdowns have to do with it."""
        fig.add_trace(trace, row=row, col=col)
        trace_views.append(view)
        trace_statistics.append(statistics or {})

    for col in range(1, len(species_list) + 1):
        _add_direction_strip(add, col)

    for view in VIEWS:
        for col, species in enumerate(species_list, start=1):
            tables = _abundance_bin_statistics(
                frames=frames,
                precursor_column_name=precursor_column_name,
                species=species,
                n_bins=n_bins,
                shared_precursors=shared if view.shared_only else None,
                common_bins=view.common_bins,
            )
            tables = {label: table[table["n"] >= min_per_bin] for label, table in tables.items()}

            for label in labels:
                table = tables.get(label)
                if table is not None and not table.empty:
                    _add_workflow_traces(add, table, label, color_map[label], view, col)
            _add_winner_strip(add, tables, labels, color_map, n_bins, view, col)

    _style_axes(fig, len(species_list))

    # The caveat line is rewritten by the view dropdown, so its index in layout.annotations
    # (right after the one subplot title per species) has to be known up front.
    caveat_index = len(fig.layout.annotations)
    fig.add_annotation(
        text=VIEWS[0].caveat,
        xref="paper",
        yref="paper",
        x=0.0,
        y=_header_paper_y(CAVEAT_Y),
        xanchor="left",
        yanchor="top",
        showarrow=False,
        font={"size": 11, "color": "#555555"},
    )

    for trace, view_key in zip(fig.data, trace_views):
        trace.visible = view_key is None or view_key == VIEWS[0].key

    fig.update_layout(
        height=FIGURE_HEIGHT,
        margin={"t": TOP_MARGIN, "b": BOTTOM_MARGIN},
        barmode="overlay",
        bargap=0.0,
        title={
            "text": "Quantification accuracy vs abundance",
            "x": 0.0,
            "xanchor": "left",
            "yref": "container",
            "y": 0.98,
            "yanchor": "top",
        },
        legend_title_text="Workflow",
        updatemenus=[
            _statistic_dropdown(fig, trace_statistics),
            _view_dropdown(trace_views, caveat_index),
        ],
    )
    return fig


def _add_workflow_traces(
    add: Callable[..., None],
    table: pd.DataFrame,
    label: str,
    color: str,
    view: _View,
    col: int,
) -> None:
    """
    Add one workflow's interval band and summary line to a species panel.

    Parameters
    ----------
    add : Callable
        Callback that adds a trace and records what the dropdowns do with it.
    table : pd.DataFrame
        Per-bin statistics of this workflow, as returned by ``_abundance_bin_statistics``.
    label : str
        Workflow label, used as the trace and legend name.
    color : str
        Hex color of the workflow.
    view : _View
        The view these traces belong to.
    col : int
        Column (species panel) the traces belong to.

    Returns
    -------
    None
        The traces are added through ``add``.
    """
    default = STATISTICS[0]

    # The band is drawn on the bins where every statistic has a finite interval, so that
    # switching statistic only has to restyle the y values and never the x values.
    interval_columns = [column for statistic in STATISTICS for column in (statistic.low_column, statistic.high_column)]
    band = table.dropna(subset=interval_columns)
    if len(band) > 1:
        band_x = band["center"].to_numpy()
        add(
            go.Scatter(
                x=np.concatenate([band_x, band_x[::-1]]),
                y=_band_y(band, default),
                fill="toself",
                fillcolor=hex_to_rgba(color, 0.15),
                line={"color": "rgba(0, 0, 0, 0)"},
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=col,
            view=view.key,
            statistics={statistic.key: {"y": _band_y(band, statistic)} for statistic in STATISTICS},
        )

    add(
        go.Scatter(
            x=table["center"].to_numpy(),
            y=table[default.centre_column].to_numpy(),
            mode="lines+markers",
            line={"color": color, "width": 2},
            name=label,
            legendgroup=label,
            showlegend=(col == 1),
            customdata=_hover_data(table, default),
            hovertemplate=_hover_template(default, view),
        ),
        row=1,
        col=col,
        view=view.key,
        statistics={
            statistic.key: {
                "y": table[statistic.centre_column].to_numpy(),
                "customdata": _hover_data(table, statistic),
                "hovertemplate": _hover_template(statistic, view),
            }
            for statistic in STATISTICS
        },
    )


def _add_winner_strip(
    add: Callable[..., None],
    tables: Dict[str, pd.DataFrame],
    labels: Sequence[str],
    color_map: Dict[str, str],
    n_bins: int,
    view: _View,
    col: int,
) -> None:
    """
    Add the strip that colors each abundance bin by its most accurate workflow.

    Only bins in which every workflow passed the minimum-count filter are drawn, so the
    comparison is never made on a bin one of the workflows barely populated.

    Parameters
    ----------
    add : Callable
        Callback that adds a trace and records what the dropdowns do with it.
    tables : Dict[str, pd.DataFrame]
        Per-bin statistics per workflow, already filtered on ``min_per_bin``.
    labels : Sequence[str]
        Workflow labels, in legend order.
    color_map : Dict[str, str]
        Mapping of workflow label to hex color.
    n_bins : int
        Number of abundance-rank bins, which fixes the bar width.
    view : _View
        The view this strip belongs to.
    col : int
        Column (species panel) the strip belongs to.

    Returns
    -------
    None
        The trace is added through ``add``.
    """
    present = [label for label in labels if label in tables and not tables[label].empty]
    if len(present) < 2:
        return

    indexed = {label: tables[label].set_index("bin") for label in present}
    bins = sorted(set.intersection(*(set(table.index) for table in indexed.values())))
    if not bins:
        return

    winners = {
        statistic.key: [min(present, key=lambda label: indexed[label].loc[b, statistic.centre_column]) for b in bins]
        for statistic in STATISTICS
    }
    default = STATISTICS[0]
    width = 100.0 / n_bins
    add(
        go.Bar(
            x=[(b + 0.5) * width for b in bins],
            y=[1] * len(bins),
            width=[width] * len(bins),
            marker={"color": [color_map[label] for label in winners[default.key]], "line": {"width": 0}},
            showlegend=False,
            hovertext=_winner_hover(winners[default.key], default),
            hoverinfo="text",
        ),
        row=2,
        col=col,
        view=view.key,
        statistics={
            statistic.key: {
                "marker.color": [color_map[label] for label in winners[statistic.key]],
                "hovertext": _winner_hover(winners[statistic.key], statistic),
            }
            for statistic in STATISTICS
        },
    )


def _add_direction_strip(add: Callable[..., None], col: int) -> None:
    """
    Add the gradient bar that marks the low- and high-abundance end of a panel.

    The bar runs from a pale tint on the left to a saturated one on the right and carries the
    words "low abundance" and "high abundance", so the direction of the x axis is readable
    without consulting the axis ticks.

    Parameters
    ----------
    add : Callable
        Callback that adds a trace and records what the dropdowns do with it.
    col : int
        Column (species panel) the bar belongs to.

    Returns
    -------
    None
        The traces are added through ``add``.
    """
    add(
        go.Heatmap(
            x=np.linspace(0.0, 100.0, 120),
            y=[0.5],
            z=[np.linspace(0.0, 1.0, 120)],
            colorscale=[[0.0, "#eff3ff"], [1.0, "#2171b5"]],
            showscale=False,
            hoverinfo="skip",
        ),
        row=3,
        col=col,
    )
    add(
        go.Scatter(
            x=[1.5, 98.5],
            y=[0.5, 0.5],
            mode="text",
            text=["◀ low abundance", "high abundance ▶"],
            textposition=["middle right", "middle left"],
            textfont={"size": 10, "color": ["#08306b", "#ffffff"]},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=3,
        col=col,
    )


def _style_axes(fig: go.Figure, n_species: int) -> None:
    """
    Title and bound the axes of every panel of the accuracy-vs-abundance figure.

    Parameters
    ----------
    fig : go.Figure
        The figure under construction, modified in place.
    n_species : int
        Number of species columns.

    Returns
    -------
    None
        The axes of ``fig`` are updated in place.
    """
    for col in range(1, n_species + 1):
        fig.update_yaxes(showticklabels=(col == 1), row=1, col=col)
        fig.update_yaxes(
            showticklabels=False,
            range=[0, 1],
            row=2,
            col=col,
            title_text="Most<br>accurate" if col == 1 else None,
            title_font={"size": 9},
        )
        fig.update_yaxes(visible=False, range=[0, 1], row=3, col=col)
        for row in (1, 2, 3):
            fig.update_xaxes(range=[0, 100], row=row, col=col)
        fig.update_xaxes(title_text="Abundance rank (%)", tickvals=[0, 25, 50, 75, 100], row=3, col=col)

    fig.update_yaxes(title_text=STATISTICS[0].axis_title, row=1, col=1)
