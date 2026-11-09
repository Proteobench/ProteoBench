"""
Building blocks of the plot generators.

``plotly_helpers`` holds the small helpers every generator needs. The other modules each hold
one figure that is too large to keep inside a generator class: the generator declares the plot
and forwards to the module, which owns the computation and the layout.
"""

from proteobench.plotting.utils.plotly_helpers import (
    create_kde_distribution_plot,
    empty_figure,
    fill_density_traces,
    hex_to_rgba,
)

__all__ = [
    "create_kde_distribution_plot",
    "empty_figure",
    "fill_density_traces",
    "hex_to_rgba",
]
