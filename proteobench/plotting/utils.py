"""
Shared plotting helpers.

Holds ``create_kde_distribution_plot``, a replacement for
``plotly.figure_factory.create_distplot``, which plotly 7.0.0 removed. Both fold-change
distribution plots called it with ``show_hist=False, show_rug=False``, so the only part
they used was the kernel density estimate; this reproduces that figure directly.
"""

from typing import List, Sequence

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde

#: Points per density curve. Matches the grid ``create_distplot`` used, so the curves are
#: sampled identically to the figures this replaced.
KDE_POINTS = 500


def create_kde_distribution_plot(
    hist_data: Sequence[Sequence[float]],
    group_labels: Sequence[str],
    colors: Sequence[str],
) -> go.Figure:
    """
    Plot one kernel density curve per group.

    Reproduces ``plotly.figure_factory.create_distplot(..., show_hist=False, show_rug=False)``,
    which was removed in plotly 7.0.0. Each curve is a Gaussian KDE evaluated on a
    ``KDE_POINTS``-point grid spanning that group's own minimum to maximum, matching the grid
    and default bandwidth the figure factory used, so existing figures are unchanged.

    Groups with fewer than two distinct values are skipped: a KDE needs a non-zero spread and
    would otherwise raise inside ``gaussian_kde``.

    Parameters
    ----------
    hist_data : Sequence[Sequence[float]]
        One sequence of observations per group.
    group_labels : Sequence[str]
        Trace name for each group, in the same order as ``hist_data``.
    colors : Sequence[str]
        Colour for each group. Indexed cyclically, as the figure factory did, so a short
        sequence repeats rather than raising.

    Returns
    -------
    go.Figure
        Figure with one filled line trace per plottable group.
    """
    fig = go.Figure()

    for index, observations in enumerate(hist_data):
        values = np.asarray(observations, dtype=float)
        values = values[np.isfinite(values)]
        # gaussian_kde inverts the covariance of the sample, so a single point or a constant
        # run is singular. Skipping keeps one degenerate species from losing the whole figure.
        if values.size < 2 or np.unique(values).size < 2:
            continue

        start, end = float(values.min()), float(values.max())
        grid = np.array([start + x * (end - start) / KDE_POINTS for x in range(KDE_POINTS)])
        density = gaussian_kde(values)(grid)

        label = group_labels[index]
        fig.add_trace(
            go.Scatter(
                x=grid,
                y=density,
                mode="lines",
                name=label,
                legendgroup=label,
                showlegend=True,
                marker=dict(color=colors[index % len(colors)]),
                xaxis="x1",
                yaxis="y1",
            )
        )

    # Carried over from the figure factory's layout so the replacement renders identically.
    # traceorder and hovermode are visible; zeroline=False suppresses a line the curves sit on.
    fig.update_layout(
        barmode="overlay",
        hovermode="closest",
        legend=dict(traceorder="reversed"),
        xaxis=dict(domain=[0.0, 1.0], zeroline=False),
        yaxis=dict(domain=[0.0, 1.0]),
    )

    return fig


def fill_density_traces(fig: go.Figure, opacity: float = 0.4) -> go.Figure:
    """
    Shade the area under each line trace.

    Parameters
    ----------
    fig : go.Figure
        Figure whose line traces should be filled, modified in place.
    opacity : float
        Opacity of the shaded area.

    Returns
    -------
    go.Figure
        The same figure, for chaining.
    """
    traces: List[go.Scatter] = [trace for trace in fig.data if getattr(trace, "mode", None) == "lines"]
    for trace in traces:
        trace.update(fill="tozeroy", opacity=opacity)
    return fig
