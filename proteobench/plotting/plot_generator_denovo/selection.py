"""
Which datapoints are coloured, how, and which the presets pick.
"""

from typing import Any, Iterable, List, Mapping, Optional, Tuple

import pandas as pd

from proteobench.plotting.plot_generator_denovo.ranking import datapoint_score, rank_within_tools


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

#: Bounds for the lightness of a shaded family, so that no member of a tool's colour family
#: washes out against the background or darkens into black.
SHADE_LIGHTNESS_BOUNDS = (0.22, 0.80)


def _hex_to_hsl(color: str) -> Tuple[float, float, float]:
    """Convert a ``#rrggbb`` string to hue, saturation and lightness, each in [0, 1]."""
    value = int(color.lstrip("#"), 16)
    red, green, blue = ((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255
    high, low = max(red, green, blue), min(red, green, blue)
    lightness = (high + low) / 2
    if high == low:
        return 0.0, 0.0, lightness
    delta = high - low
    saturation = delta / (2 - high - low) if lightness > 0.5 else delta / (high + low)
    if high == red:
        hue = (green - blue) / delta + (6 if green < blue else 0)
    elif high == green:
        hue = (blue - red) / delta + 2
    else:
        hue = (red - green) / delta + 4
    return hue / 6, saturation, lightness


def _hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    """Convert hue, saturation and lightness, each in [0, 1], to a ``#rrggbb`` string."""

    def channel(p: float, q: float, t: float) -> float:
        t = t % 1.0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if saturation == 0:
        red = green = blue = lightness
    else:
        q = lightness * (1 + saturation) if lightness < 0.5 else lightness + saturation - lightness * saturation
        p = 2 * lightness - q
        red, green, blue = channel(p, q, hue + 1 / 3), channel(p, q, hue), channel(p, q, hue - 1 / 3)
    return "#{:02x}{:02x}{:02x}".format(*(int(round(min(1.0, max(0.0, c)) * 255)) for c in (red, green, blue)))


def shade_within_tool(color: str, position: int, count: int) -> str:
    """
    Vary a tool's colour by lightness, so several of its datapoints stay distinguishable.

    Hue is reserved for the tool, because that is what makes a figure readable across tools, so
    the datapoint has to be carried by something else. Lightness offers as many distinguishable
    steps as a group needs, where a dash cycle runs out after six, and it carries an ordering
    for free: ``position`` 0 is the darkest, so the darkest member of a family is its best run.

    Parameters
    ----------
    color : str
        The tool's base colour, as ``#rrggbb``.
    position : int
        Zero-based position of this datapoint within its tool's displayed group.
    count : int
        Number of the tool's datapoints being displayed.

    Returns
    -------
    str
        The shaded colour as ``#rrggbb``. The base colour is returned unchanged when the group
        holds at most one datapoint, since there is then nothing to separate.
    """
    if count <= 1 or position < 0:
        return color
    hue, saturation, lightness = _hex_to_hsl(color)
    # Wider groups get a wider spread, capped so that even a large family stays within one hue's
    # readable lightness range rather than running from white to black.
    span = min(0.34, 0.08 + 0.03 * count)
    target = lightness - span / 2 + (span * position) / (count - 1)
    low, high = SHADE_LIGHTNESS_BOUNDS
    return _hsl_to_hex(hue, saturation, min(high, max(low, target)))


#: Colour for a datapoint that is present but not emphasised. Every submission stays visible, so
#: a tool's spread can be seen, without every submission competing for attention.
MUTED_COLOR = "#c9c9c9"

#: Opacity of a non-emphasised curve. Lower than the equivalent for markers because a full-width
#: line covers far more of the plot than a marker does, so it needs to recede further to stop a
#: tool with fifteen submissions from visually outweighing a tool with one.
MUTED_CURVE_OPACITY = 0.18

#: Opacity of a datapoint belonging to a tool other than the one currently highlighted.
DIMMED_OPACITY = 0.12

#: Opacity of a coloured datapoint that is not the best of its tool within the current selection.
#: With every datapoint shown by default, a tool submitted fifteen times would otherwise put
#: fifteen equally loud marks on the plot. Fading the rest keeps the spread visible as context
#: while the eye stays on the run that decides where the tool actually sits.
SECONDARY_OPACITY = 0.4

#: Marker symbol for the best datapoint of each tool, matching the star the result table puts
#: beside that tool's name. Only used outside colourblind mode, where the symbol is already
#: spoken for: there it says which tool a point belongs to.
BEST_MARKER_SYMBOL = "star"

#: How much larger a star is drawn than the circle it replaces. A five-pointed star encloses
#: roughly half the ink of a circle of the same nominal size, so a little is needed or the
#: datapoint being singled out would read as the smallest mark on the plot. Only a little,
#: though: the size is multiplied again for an unpublished datapoint, and at 1.35 the two
#: multipliers together made a star twice the width of the points around it.
BEST_MARKER_SCALE = 1.12

#: Opacity of a curve in that same position. Lower than the marker equivalent for the reason
#: :data:`MUTED_CURVE_OPACITY` is: a full-width line covers far more of the plot than a marker.
SECONDARY_CURVE_OPACITY = 0.3


def resolve_coloured_datapoints(
    result_df: pd.DataFrame,
    best_by_tool: Optional[Mapping[str, Any]] = None,
    muted_tools: Iterable[str] = (),
    selected_ids: Iterable[str] = (),
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
    explicit_only: bool = False,
) -> pd.Series:
    """
    Decide which datapoints are drawn in their tool's colour rather than greyed.

    By default exactly one datapoint per tool is coloured, its best, which is what keeps the
    figure from being biased by how many times a tool was submitted. Two overrides sit on top: a
    datapoint whose ID appears in ``selected_ids`` is coloured regardless of rank, and a tool
    named in ``muted_tools`` is never coloured at all, selected or not, which is how a whole tool
    is greyed in one action.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to resolve. Must carry ``software_name``; ``id`` is used when present.
    best_by_tool : Mapping, optional
        Tool name to best index, from :func:`rank_within_tools`. Computed here when omitted.
    muted_tools : Iterable of str
        Tools that are never coloured, whether or not their datapoints are selected.
    selected_ids : Iterable of str
        ProteoBench IDs of datapoints to colour regardless of rank.
    evaluation_type : str
        Evaluation type used when ``best_by_tool`` has to be computed.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination used when ``best_by_tool`` has to be computed.
    explicit_only : bool
        When True, colour exactly ``selected_ids`` and nothing else. A caller driving the
        colouring from a checkbox needs an empty selection to mean an empty plot, not a silent
        fall back to the per-tool bests, which is what the default rule would do.

    Returns
    -------
    pd.Series
        Boolean Series aligned to ``result_df.index``, True where the datapoint is coloured.
    """
    if len(result_df) == 0:
        return pd.Series([], dtype=bool)
    if best_by_tool is None:
        _, best_by_tool = rank_within_tools(result_df, evaluation_type, ambiguity_combo)

    muted = {str(tool) for tool in muted_tools}
    selected = {str(point_id) for point_id in selected_ids}
    ids = result_df["id"].astype(str) if "id" in result_df.columns else pd.Series("", index=result_df.index)
    software = (
        result_df["software_name"].astype(str)
        if "software_name" in result_df.columns
        else pd.Series("Custom", index=result_df.index)
    )

    coloured = pd.Series(False, index=result_df.index, dtype=bool)
    for idx in result_df.index:
        # Muting is checked before the selection, not after it. A tool named in ``muted_tools``
        # is never coloured, however its datapoints came to be selected: checked only on the
        # automatic branch, a mute did nothing at all once the table was driving the colouring
        # from its own ticks, which is why "Grey out tools" appeared not to register.
        tool = software.at[idx]
        if tool in muted:
            continue
        if ids.at[idx] in selected:
            coloured.at[idx] = True
            continue
        if explicit_only:
            continue
        coloured.at[idx] = best_by_tool.get(tool) == idx
    return coloured


#: The two ways of picking which datapoints an in-depth view compares.
SELECTION_PRESETS = ("cross_tool", "tool_specific")


def preset_selection(
    result_df: pd.DataFrame,
    preset: str = "cross_tool",
    tool: Optional[str] = None,
    top_n: int = 0,
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
) -> List[str]:
    """
    The ProteoBench IDs a selection preset picks out.

    The two presets answer different questions and deliberately suppress each other's:

    - ``cross_tool`` takes each tool's best datapoint, one per tool. This is the comparison that
      is not biased by how many times a tool was submitted, and it is what a reader opening the
      page should see first.
    - ``tool_specific`` takes one tool's own submissions, the ``top_n`` best or all of them. This
      is the within-tool comparison the cross-tool view hides.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to pick from. Must carry ``software_name`` and ``id``.
    preset : str
        One of :data:`SELECTION_PRESETS`.
    tool : str, optional
        The tool for ``tool_specific``. Defaults to the tool with the best datapoint overall.
    top_n : int
        How many of the tool's submissions to take, best first. ``0`` means all of them.
    evaluation_type : str
        Evaluation type the ranking is based on.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination the ranking is based on.

    Returns
    -------
    list of str
        Selected ProteoBench IDs, ordered best first within each tool.

    Raises
    ------
    ValueError
        If ``preset`` is not one of :data:`SELECTION_PRESETS`.
    """
    if preset not in SELECTION_PRESETS:
        raise ValueError(f"Unknown selection preset {preset!r}; expected one of {', '.join(SELECTION_PRESETS)}")
    if len(result_df) == 0 or "id" not in result_df.columns:
        return []

    ranks, best_by_tool = rank_within_tools(result_df, evaluation_type, ambiguity_combo)
    ids = result_df["id"].astype(str)
    software = result_df["software_name"].astype(str)

    if preset == "cross_tool":
        # Ordered by how good each tool's best is, so the legend and table read best-first.
        ordered_tools = sorted(
            best_by_tool,
            key=lambda name: -(datapoint_score(result_df.loc[best_by_tool[name]], evaluation_type, ambiguity_combo)),
        )
        return [ids.at[best_by_tool[name]] for name in ordered_tools]

    if tool is None:
        if not best_by_tool:
            return []
        tool = max(
            best_by_tool,
            key=lambda name: datapoint_score(result_df.loc[best_by_tool[name]], evaluation_type, ambiguity_combo),
        )
    members = [idx for idx in result_df.index if software.at[idx] == str(tool)]
    members.sort(key=lambda idx: int(ranks.at[idx]) if idx in ranks.index else 0)
    if top_n and top_n > 0:
        members = members[:top_n]
    return [ids.at[idx] for idx in members]


def assign_datapoint_colors(
    result_df: pd.DataFrame,
    software_colors: Optional[Mapping[str, str]] = None,
    ranks: Optional[pd.Series] = None,
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
) -> pd.Series:
    """
    Give every datapoint in a selection a colour, shading only where that helps.

    Which rule applies follows from the selection itself, so no caller has to declare a mode:

    - **Several tools selected.** Hue is doing its original job, telling tools apart, so each
      datapoint simply takes its tool's colour. A shade per datapoint would compete with exactly
      the comparison a cross-tool selection exists to make.
    - **One tool selected.** Every mark belongs to that tool, so hue is free to carry the
      datapoint instead: each run takes the tool's hue at a lightness set by its rank, best
      darkest, via :func:`shade_within_tool`.

    Parameters
    ----------
    result_df : pd.DataFrame
        The selected datapoints. Must carry ``software_name``.
    software_colors : Mapping, optional
        Tool name to colour. Defaults to :data:`SOFTWARE_COLORS`.
    ranks : pd.Series, optional
        Precomputed ranks from :func:`rank_within_tools`, reused when the caller already has
        them. Computed here when omitted.
    evaluation_type : str
        Evaluation type used when ranks have to be computed.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination used when ranks have to be computed.

    Returns
    -------
    pd.Series
        Colours aligned to ``result_df.index``.
    """
    palette = SOFTWARE_COLORS if software_colors is None else software_colors
    if len(result_df) == 0:
        return pd.Series([], dtype=str)
    software = (
        result_df["software_name"].astype(str)
        if "software_name" in result_df.columns
        else pd.Series("Custom", index=result_df.index)
    )
    base = pd.Series([palette.get(software.at[idx], "gray") for idx in result_df.index], index=result_df.index)
    if software.nunique() != 1:
        return base

    if ranks is None:
        ranks, _ = rank_within_tools(result_df, evaluation_type, ambiguity_combo)
    ordered = sorted(result_df.index, key=lambda idx: (int(ranks.at[idx]) if idx in ranks.index else 0))
    count = len(ordered)
    return pd.Series(
        {idx: shade_within_tool(base.at[idx], position, count) for position, idx in enumerate(ordered)},
        dtype=object,
    ).reindex(result_df.index)


def resolve_emphasis(result_df: pd.DataFrame, highlight_id: Optional[str] = None) -> pd.Series:
    """
    Decide which datapoints are emphasised while one of them is highlighted.

    The granularity follows the selection, matching :func:`assign_datapoint_colors`. Across
    several tools, highlighting one mark raises every mark of that software, which is what a
    cross-tool reader wants and what the main scatter does. Within a single tool that rule would
    raise the whole selection and say nothing, so it narrows to the one datapoint.

    Parameters
    ----------
    result_df : pd.DataFrame
        The selected datapoints. Must carry ``software_name``; ``id`` is used when present.
    highlight_id : str, optional
        ProteoBench ID of the highlighted datapoint. ``None`` means nothing is highlighted.

    Returns
    -------
    pd.Series
        Boolean Series aligned to ``result_df.index``. All True when nothing is highlighted or
        the ID is not found, so callers can dim on ``not emphasised`` unconditionally.
    """
    if len(result_df) == 0:
        return pd.Series([], dtype=bool)
    everything = pd.Series(True, index=result_df.index, dtype=bool)
    if not highlight_id or "id" not in result_df.columns:
        return everything

    ids = result_df["id"].astype(str)
    matches = ids == str(highlight_id)
    if not matches.any():
        return everything

    software = (
        result_df["software_name"].astype(str)
        if "software_name" in result_df.columns
        else pd.Series("Custom", index=result_df.index)
    )
    if software.nunique() == 1:
        return matches
    return software == software[matches].iloc[0]
