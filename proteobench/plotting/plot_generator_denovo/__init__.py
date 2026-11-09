"""
Plotting and datapoint-view helpers for the de novo module.

Split out of a single 2.7k-line module. The import path is unchanged: everything public is
re-exported here, so ``from proteobench.plotting.plot_generator_denovo import X`` still works.
"""

from proteobench.plotting.plot_generator_denovo.results import (  # noqa: F401
    EMPTY_METRICS,
    datapoint_has_required_fields,
    flatten_results_column,
)
from proteobench.plotting.plot_generator_denovo.labels import (  # noqa: F401
    CHECKPOINT_SEPARATOR,
    REFINEMENT_MODEL_NAMES,
    WORKFLOW_LABEL_FIELDS,
    build_display_labels,
    build_variant_descriptions,
)
from proteobench.plotting.plot_generator_denovo.ranking import (  # noqa: F401
    datapoint_score,
    leading_datapoints,
    rank_within_tools,
)
from proteobench.plotting.plot_generator_denovo.columns import (  # noqa: F401
    IDENTIFIER_COLUMNS,
    classify_datapoint_columns,
    columns_varying_within_tool,
    default_hidden_columns,
    ordered_datapoint_columns,
)
from proteobench.plotting.plot_generator_denovo.selection import (  # noqa: F401
    BEST_MARKER_SCALE,
    BEST_MARKER_SYMBOL,
    DIMMED_OPACITY,
    MUTED_COLOR,
    MUTED_CURVE_OPACITY,
    SECONDARY_CURVE_OPACITY,
    SECONDARY_OPACITY,
    SELECTION_PRESETS,
    SHADE_LIGHTNESS_BOUNDS,
    SOFTWARE_COLORS,
    SOFTWARE_MARKERS,
    assign_datapoint_colors,
    preset_selection,
    resolve_coloured_datapoints,
    resolve_emphasis,
    shade_within_tool,
)
from proteobench.plotting.plot_generator_denovo.generator import (  # noqa: F401
    DeNovoPlotGenerator,
    EPSILON,
    INFASTA_CATEGORIES,
    INFASTA_COLORS,
    INFASTA_LABELS,
    MAIN_PLOT_AXIS_RANGE,
    MAX_CURVE_POINTS,
    PR_CURVE_AXIS_RANGE,
    QUADRANT_BOUNDARY,
    QUADRANT_COLORSCALE,
    QUADRANT_LABELS,
    thin_curve,
)

__all__ = [
    "BEST_MARKER_SCALE",
    "BEST_MARKER_SYMBOL",
    "CHECKPOINT_SEPARATOR",
    "DIMMED_OPACITY",
    "DeNovoPlotGenerator",
    "EMPTY_METRICS",
    "EPSILON",
    "IDENTIFIER_COLUMNS",
    "INFASTA_CATEGORIES",
    "INFASTA_COLORS",
    "INFASTA_LABELS",
    "MAIN_PLOT_AXIS_RANGE",
    "MAX_CURVE_POINTS",
    "MUTED_COLOR",
    "MUTED_CURVE_OPACITY",
    "PR_CURVE_AXIS_RANGE",
    "QUADRANT_BOUNDARY",
    "QUADRANT_COLORSCALE",
    "QUADRANT_LABELS",
    "REFINEMENT_MODEL_NAMES",
    "SECONDARY_CURVE_OPACITY",
    "SECONDARY_OPACITY",
    "SELECTION_PRESETS",
    "SHADE_LIGHTNESS_BOUNDS",
    "SOFTWARE_COLORS",
    "SOFTWARE_MARKERS",
    "WORKFLOW_LABEL_FIELDS",
    "assign_datapoint_colors",
    "build_display_labels",
    "build_variant_descriptions",
    "build_workflow_labels",
    "classify_datapoint_columns",
    "columns_varying_within_tool",
    "datapoint_has_required_fields",
    "datapoint_score",
    "default_hidden_columns",
    "flatten_results_column",
    "leading_datapoints",
    "ordered_datapoint_columns",
    "preset_selection",
    "rank_within_tools",
    "resolve_coloured_datapoints",
    "resolve_emphasis",
    "shade_within_tool",
    "thin_curve",
]
