"""
DIA Quantification Module for precursor level Quantification for single cell data.
"""

from __future__ import annotations

from typing import Optional

from proteobench.datapoint.quant_datapoint import QuantDatapointPYE
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_base_module import QuantModule
from proteobench.plotting.plot_generator_lfq_PYE import LFQPYEPlotGenerator
from proteobench.score.quantscoresPYE import QuantScoresPYE


class DIAQuantIonModulePlasma(QuantModule):
    """
    DIA Quantification Module for precursor level Quantification for low input (single-cell) data.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str, optional
        Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DIA_plasma".
    proteobench_repo_name : str, optional
        Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DIA_plasma".

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    quant_score_class = QuantScoresPYE
    datapoint_class = QuantDatapointPYE

    module_id: str = "quant_lfq_DIA_ion_plasma"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_ion_DIA_plasma",
        proteobench_repo_name: str = "Proteobench/Results_quant_ion_DIA_plasma",
    ):
        """
        Initialize the DIA Quantification Module for precursor level Quantification for low input data.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DIA_plasma".
        proteobench_repo_name : str, optional
            Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DIA_plasma".
        """
        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=MODULE_SETTINGS_DIRS[self.module_id],
            module_id=self.module_id,
        )
        self.precursor_column_name = "precursor ion"

    def is_implemented(self) -> bool:
        """
        Return whether the module is fully implemented.

        Returns
        -------
        bool
            Whether the module is fully implemented.
        """
        return False

    def get_plot_generator(self):
        """Return the plot generator for the module.

        Returns
        -------
        PlotGenerator
            The plot generator for the module.
        """

        return LFQPYEPlotGenerator()
