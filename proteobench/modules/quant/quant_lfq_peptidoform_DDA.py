"""
DDA Quantification Module for Peptidoform level Quantification.
"""

from __future__ import annotations

from typing import Optional

from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_base_module import QuantModule


class DDAQuantPeptidoformModule(QuantModule):
    """
    DDA Quantification Module for Peptidoform level Quantification.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str, optional
        Repository for pull requests and adding new points, by default "Proteobot/Results_quant_peptidoform_DDA".
    proteobench_repo_name : str, optional
        Repository for storing benchmarking results, by default "Proteobench/Results_quant_peptidoform_DDA".

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    module_id: str = "quant_lfq_DDA_peptidoform"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_peptidoform_DDA",
        proteobench_repo_name: str = "Proteobench/Results_quant_peptidoform_DDA",
        branch: Optional[str] = None,
    ):
        """
        Initialize the DDA Quantification Module for Peptidoform level Quantification.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Repository for pull requests and adding new points, by default "Proteobot/Results_quant_peptidoform_DDA".
        proteobench_repo_name : str, optional
            Repository for storing benchmarking results, by default "Proteobench/Results_quant_peptidoform_DDA".
        """
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
        return super().get_plot_generator()
