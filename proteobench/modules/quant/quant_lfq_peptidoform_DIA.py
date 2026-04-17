"""DIA quantification Module."""

from __future__ import annotations

from typing import Optional

from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_base_module import QuantModule


class DIAQuantPeptidoformModule(QuantModule):
    """
    DIA Quantification Module for Peptidoform level Quantification.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str
        Name of the repository for pull requests and where new points are added.
    proteobench_repo_name : str
        Name of the repository where the benchmarking results will be stored.

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    module_id = "quant_lfq_DIA_peptidoform"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_peptidoform_DIA",
        proteobench_repo_name: str = "Proteobench/Results_quant_peptidoform_DIA",
        branch: Optional[str] = None,
    ):
        """
        Initialize the DIA Quantification Module for Peptidoform level Quantification.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_peptidoform_DIA".
        proteobench_repo_name : str, optional
            Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_peptidoform_DIA".
        """
        raise NotImplementedError(
            "This module is not be implemented properly, no parse settings .toml files exist. After .toml files have "
            "been added, the parse settings dir must be added to `MODULE_SETTINGS_DIRS` in the constants.py file!"
        )
        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=MODULE_SETTINGS_DIRS[self.module_id],
            module_id=self.module_id,
            branch=branch,
        )
        self.precursor_column_name = "peptidoform"

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
        """
        Get the plot generator for this module.

        Returns
        -------
        PlotGeneratorBase
            The plot generator instance.
        """
        return super().get_plot_generator()
