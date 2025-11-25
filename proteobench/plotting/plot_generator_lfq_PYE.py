from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot

from proteobench.plotting.plot_generator_base import PlotGeneratorBase
from proteobench.plotting.plot_generator_lfq_HYE import PlotGeneratorLFQHYE


class PlotGeneratorLFQPYE(PlotGeneratorLFQHYE):
    """
    Plot Generator for LFQ PYE Module.
    Inherits from PlotGeneratorLFQHYE as the plotting logic is similar.
    """

    def generate_in_depth_plots(
        self, performance_data: pd.DataFrame, parse_settings: any, **kwargs
    ) -> Dict[str, go.Figure]:
        """
        Generate in-depth plots for LFQ PYE module.

        Parameters
        ----------
        performance_data : pd.DataFrame
            The performance data to plot.
        parse_settings : any
            Parsing settings used for the module.
        **kwargs : dict
            Additional module-specific parameters.
        """
        plots = {}

        species_expected_ratio = parse_settings.species_expected_ratio()

        # Generate dynamic range visualization # TODO

        # Generate CV violing plot
        plots["cv"] = super().generate_cv_violin_plot(performance_data)

        # Generate Missingness plot # TODO

        # Generate MA plot
        plots["ma_plot"] = super().generate_ma_plot(performance_data, species_expected_ratio)

        return plots
