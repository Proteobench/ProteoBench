"""
Cross-workflow quantification-accuracy comparison plot.

Unlike the per-workflow in-depth plots in ``plot_generator_lfq_HYE.py``, this plot compares two
or more benchmark workflow results directly, restricted to the precursors they identify in
common. It shows which workflow is quantitatively more accurate, and whether that ranking
depends on abundance.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_REQUIRED_COLUMNS = ("species", "epsilon", "log_Intensity_mean_A", "log_Intensity_mean_B")


def _empty_figure(message: str) -> go.Figure:
    """
    Build a placeholder figure carrying an explanatory annotation.

    Parameters
    ----------
    message : str
        Text shown in the center of the empty plot area.

    Returns
    -------
    go.Figure
        A figure with no traces and a centered annotation.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
    )
    return fig


def _hex_to_rgba(color: str, alpha: float) -> str:
    """
    Convert a hex color string to an ``rgba(...)`` string with the given opacity.

    Parameters
    ----------
    color : str
        A ``#rrggbb`` hex color string. Any other format falls back to mid-gray.
    alpha : float
        Opacity between 0 and 1.

    Returns
    -------
    str
        A CSS-style ``rgba(r, g, b, a)`` color string.
    """
    color = color.lstrip("#")
    if len(color) != 6:
        return f"rgba(128, 128, 128, {alpha})"
    r, g, b = bytes.fromhex(color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def plot_accuracy_vs_abundance(
    intermediates: Dict[str, pd.DataFrame],
    precursor_column_name: str = "precursor ion",
    species_order: Sequence[str] = ("HUMAN", "YEAST", "ECOLI"),
    n_bins: int = 12,
    min_per_bin: int = 20,
    colors: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """
    Compare quantification accuracy vs abundance across workflows, on their shared precursors.

    For each species, precursors are restricted to those quantified by every workflow in
    ``intermediates`` (the stringent overlap). Within that overlap, an abundance rank is
    computed per workflow and averaged, precursors are grouped into abundance-rank bins, and per
    bin the mean absolute error (``|epsilon|``) of each workflow is plotted with its standard
    error. A band below each species panel marks the workflow with the lowest mean error in each
    abundance bin, so it is visible at a glance whether one workflow is uniformly more accurate
    or whether the ranking flips with abundance.

    Parameters
    ----------
    intermediates : Dict[str, pd.DataFrame]
        Mapping of workflow label (e.g. a ProteoBench ID or tool name) to its intermediate
        DataFrame, as produced by ``QuantScoresHYE.generate_intermediate``. Each DataFrame must
        contain the precursor column, ``species``, ``epsilon``, ``log_Intensity_mean_A`` and
        ``log_Intensity_mean_B``. At least two workflows are required.
    precursor_column_name : str, optional
        Name of the precursor identifier column shared across workflows.
    species_order : Sequence[str], optional
        Species to show, and their left-to-right column order in the figure.
    n_bins : int, optional
        Number of abundance-rank quantile bins computed per species.
    min_per_bin : int, optional
        Minimum number of shared precursors a bin must contain to be drawn.
    colors : Dict[str, str], optional
        Mapping of workflow label to a plotting color (e.g. the software's usual color). Labels
        without an explicit entry fall back to the Plotly qualitative palette.

    Returns
    -------
    go.Figure
        A figure with one column per species: on top, mean ``|epsilon|`` vs abundance rank with
        an SEM band, one line per workflow; below, a band colored by the most accurate workflow
        in each abundance bin. A placeholder figure with an explanatory message is returned
        instead when fewer than two workflows are given, required columns are missing, or the
        workflows share no precursors.
    """
    labels = list(intermediates.keys())
    if len(labels) < 2:
        return _empty_figure("Select at least two workflows to compare.")

    palette = px.colors.qualitative.Plotly
    color_map = {label: (colors or {}).get(label, palette[i % len(palette)]) for i, label in enumerate(labels)}

    merged = None
    for label in labels:
        df = intermediates[label]
        missing = [c for c in (precursor_column_name, *_REQUIRED_COLUMNS) if c not in df.columns]
        if missing:
            return _empty_figure(f"Workflow '{label}' is missing column(s): {', '.join(missing)}.")

        sub = df[[precursor_column_name, "species", "epsilon", "log_Intensity_mean_A", "log_Intensity_mean_B"]].copy()
        sub["abundance"] = 0.5 * (sub["log_Intensity_mean_A"] + sub["log_Intensity_mean_B"])
        sub["abs_err"] = sub["epsilon"].abs()
        sub = sub.dropna(subset=["abs_err", "abundance"])

        keep_cols = [precursor_column_name, "abs_err", "abundance"]
        if merged is None:
            keep_cols = [precursor_column_name, "species"] + keep_cols[1:]
        sub = sub[keep_cols].rename(columns={"abs_err": f"abs_err__{label}", "abundance": f"abund__{label}"})
        merged = sub if merged is None else merged.merge(sub, on=precursor_column_name, how="inner")

    if merged is None or merged.empty:
        return _empty_figure("No precursors are shared between the selected workflows.")

    rank_cols = []
    for label in labels:
        rank_col = f"rank__{label}"
        merged[rank_col] = merged[f"abund__{label}"].rank(pct=True) * 100
        rank_cols.append(rank_col)
    merged["abundance"] = merged[rank_cols].mean(axis=1)

    species_list = [s for s in species_order if s in merged["species"].unique()]
    if not species_list:
        return _empty_figure("No shared precursors match the requested species.")

    fig = make_subplots(
        rows=2,
        cols=len(species_list),
        shared_xaxes=True,
        row_heights=[0.85, 0.15],
        vertical_spacing=0.04,
        subplot_titles=[f"{sp} (n={(merged['species'] == sp).sum():,})" for sp in species_list],
    )

    for col, species in enumerate(species_list, start=1):
        d = merged[merged["species"] == species]
        try:
            bins = pd.qcut(d["abundance"], n_bins, duplicates="drop")
        except ValueError:
            continue
        grouped = d.groupby(bins, observed=True)
        bin_centers = grouped["abundance"].median()
        keep = grouped.size() >= min_per_bin

        mean_err = {}
        for label in labels:
            mean_t = grouped[f"abs_err__{label}"].mean()
            sem_t = grouped[f"abs_err__{label}"].sem()
            mean_err[label] = mean_t

            x = bin_centers[keep].to_numpy()
            y = mean_t[keep].to_numpy()
            y_upper = (mean_t + sem_t)[keep].to_numpy()
            y_lower = (mean_t - sem_t)[keep].to_numpy()

            fig.add_trace(
                go.Scatter(
                    x=np.concatenate([x, x[::-1]]),
                    y=np.concatenate([y_upper, y_lower[::-1]]),
                    fill="toself",
                    fillcolor=_hex_to_rgba(color_map[label], 0.15),
                    line={"color": "rgba(0, 0, 0, 0)"},
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=1,
                col=col,
            )
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines+markers",
                    line={"color": color_map[label], "width": 2},
                    name=label,
                    legendgroup=label,
                    showlegend=(col == 1),
                ),
                row=1,
                col=col,
            )

        intervals = [iv for iv, k in zip(grouped.groups.keys(), keep.to_numpy()) if k]
        if intervals:
            err_matrix = np.vstack([mean_err[label][keep].to_numpy() for label in labels])
            best_idx = np.argmin(err_matrix, axis=0)
            fig.add_trace(
                go.Bar(
                    x=[(iv.left + iv.right) / 2 for iv in intervals],
                    y=[1] * len(intervals),
                    width=[iv.right - iv.left for iv in intervals],
                    marker_color=[color_map[labels[i]] for i in best_idx],
                    showlegend=False,
                    hovertext=[f"Most accurate: {labels[i]}" for i in best_idx],
                    hoverinfo="text",
                ),
                row=2,
                col=col,
            )

        fig.update_yaxes(showticklabels=(col == 1), row=1, col=col)
        fig.update_yaxes(visible=False, range=[0, 1], row=2, col=col)
        fig.update_xaxes(title_text="Abundance rank (percentile, shared precursors)", row=2, col=col)

    fig.update_yaxes(title_text="Mean |epsilon| (|measured - expected| log2FC)", row=1, col=1)
    fig.update_layout(
        height=550,
        barmode="overlay",
        title="Quantification accuracy vs abundance (shared precursors)",
        legend_title_text="Workflow",
    )
    return fig
