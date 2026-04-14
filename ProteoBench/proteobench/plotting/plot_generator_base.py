from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd
from plotly import graph_objects as go


class PlotGeneratorBase(ABC):
    """
    Abstract base class for module-specific plot generators.
    Each module can extend this to define its own in-depth plots.
    """

    @abstractmethod
    def generate_in_depth_plots(self, performance_data: pd.DataFrame, **kwargs) -> Dict[str, go.Figure]:
        """
        Generate module-specific plots.

        Parameters
        ----------
        performance_data : pd.DataFrame
            The performance data to plot
        **kwargs : dict
            Additional module-specific parameters. Common parameters include:
            - parse_settings: ParseSettings - module-specific parse settings (may be optional for some modules)
            - metric: str - metric to display (e.g., "Median", "Mean")
            - mode: str - calculation mode (e.g., "Global", "Species-weighted")
            - colorblind_mode: bool - whether to use colorblind-friendly visualization

            Each implementation should document which parameters it accepts.

        Returns
        -------
        Dict[str, go.Figure]
            Dictionary mapping plot names to plotly figures

        Notes
        -----
        Implementations may add parse_settings as an explicit positional parameter
        for consistency with generic tab code, even if not used by the module.
        """
        pass

    @abstractmethod
    def get_in_depth_plot_layout(self) -> list:
        """
        Define the layout configuration for displaying plots.

        Returns
        -------
        list
            List of plot configurations, e.g.:
            [
                {"plots": ["logfc", "cv"], "columns": 2, "title": "Distribution Plots"},
                {"plots": ["ma_plot"], "columns": 1, "title": "MA Plot"}
            ]
        """
        pass

    @abstractmethod
    def get_in_depth_plot_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for each plot.

        Returns
        -------
        Dict[str, str]
            Dictionary mapping plot names to their descriptions
        """
        pass

    @abstractmethod
    def plot_main_metric(self, result_df: pd.DataFrame, hide_annot: bool = False, **kwargs) -> go.Figure:
        """
        Generate the main performance metric plot for the module.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot.
        hide_annot : bool, optional
            Whether to hide annotations on the plot (default is False).
        **kwargs : dict
            Additional module-specific parameters.
        Returns
        -------
        go.Figure
            The generated plotly figure for the main performance metric.
        """
        pass
