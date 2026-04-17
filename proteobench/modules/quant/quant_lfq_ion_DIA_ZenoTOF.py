"""
DIA Quantification Module for precursor level Quantification for ZenoTOF.
"""

from __future__ import annotations

from typing import Optional

from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_base_module import QuantModule


class DIAQuantIonModuleZenoTOF(QuantModule):
    """
    DIA Quantification Module for precursor level Quantification for ZenoTOF.

    Parameters
    ----------
    token : str
        GitHub token for the user.
    proteobot_repo_name : str, optional
        Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DIA_ZenoTOF".
    proteobench_repo_name : str, optional
        Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DIA_ZenoTOF".
    branch : str, optional
        Git branch name. Defaults to None.

    Attributes
    ----------
    module_id : str
        Module identifier for configuration.
    precursor_column_name: str
        Level of quantification.
    """

    module_id: str = "quant_lfq_DIA_ion_ZenoTOF"

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_lfq_DIA_ion_ZenoTOF",
        proteobench_repo_name: str = "Proteobench/Results_quant_lfq_DIA_ion_ZenoTOF",
        branch: Optional[str] = None,
    ):
        """
        Initialize the DIA Quantification Module for precursor level Quantification for ZenoTOF.

        Parameters
        ----------
        token : str
            GitHub token for the user.
        proteobot_repo_name : str, optional
            Name of the repository for pull requests and where new points are added, by default "Proteobot/Results_quant_ion_DIA_ZenoTOF".
        proteobench_repo_name : str, optional
            Name of the repository where the benchmarking results will be stored, by default "Proteobench/Results_quant_ion_DIA_ZenoTOF".
        branch : str, optional
            Git branch name. Defaults to None.
        """
        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=MODULE_SETTINGS_DIRS[self.module_id],
            module_id=self.module_id,
            branch=branch,
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
