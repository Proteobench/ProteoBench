"""
Plot generator for the low-input LFQ HYE (Human-Yeast-Ecoli) quantification modules.

Low-input modules use the same HYE benchmark sample as the regular ion modules, so every plot
is inherited from :class:`LFQHYEPlotGenerator`. What distinguishes them is which comparison
plot they put in front of the user: at low sample input the differences between tools
concentrate at the low-abundance end, so the question is not only how accurate a workflow is
overall, but over which part of the dynamic range it stays accurate. These modules therefore
add the accuracy-vs-abundance plot to the workflow comparison tab.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go

from proteobench.plotting.plot_generator_lfq_HYE import LFQHYEPlotGenerator


class LFQLowInputPlotGenerator(LFQHYEPlotGenerator):
    """
    Plot generator for the low-input LFQ HYE quantification modules.

    Identical to :class:`LFQHYEPlotGenerator` except that it adds the inherited
    ``plot_accuracy_vs_abundance`` figure to the workflow comparison tab.
    """

    def generate_comparison_plots(
        self,
        intermediates: Dict[str, pd.DataFrame],
        precursor_column_name: str = "precursor ion",
        **kwargs,
    ) -> Dict[str, go.Figure]:
        """
        Generate the cross-workflow comparison plots of the low-input modules.

        Parameters
        ----------
        intermediates : Dict[str, pd.DataFrame]
            Mapping of workflow label (e.g. a ProteoBench ID) to that workflow's intermediate
            DataFrame, as produced by ``QuantScoresHYE.generate_intermediate``.
        precursor_column_name : str, optional
            Name of the precursor identifier column shared across workflows.
        **kwargs : dict
            Additional parameters forwarded to ``plot_accuracy_vs_abundance``.

        Returns
        -------
        Dict[str, go.Figure]
            Dictionary with the ``accuracy_vs_abundance`` figure.
        """
        return {
            "accuracy_vs_abundance": self.plot_accuracy_vs_abundance(
                intermediates,
                precursor_column_name=precursor_column_name,
                **kwargs,
            )
        }

    def get_comparison_plot_layout(self) -> List[dict]:
        """
        Define the comparison tabs of the low-input modules.

        Returns
        -------
        List[dict]
            The tabs every module shows, followed by the accuracy-vs-abundance plot.
        """
        return super().get_comparison_plot_layout() + [
            {
                "name": "accuracy_vs_abundance",
                "title": "Quantification Accuracy vs Abundance",
            }
        ]

    def get_comparison_plot_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for each comparison tab.

        Returns
        -------
        Dict[str, str]
            The inherited descriptions plus the one for the accuracy-vs-abundance plot.
        """
        descriptions = super().get_comparison_plot_descriptions()
        descriptions["accuracy_vs_abundance"] = (
            "Restricted to the precursors both workflows identify, split by species: mean "
            "absolute error vs abundance rank per workflow, and which workflow is most "
            "accurate in each abundance bin."
        )
        return descriptions
