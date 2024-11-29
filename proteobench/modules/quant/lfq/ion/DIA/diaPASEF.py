from __future__ import annotations

import os

from proteobench.modules.quant.lfq.ion.DIA.quant_lfq_ion_DIA_AIF import (
    DIAQuantIonModule,
)


class DIAQuantIonModulediaPASEF(DIAQuantIonModule):
    """DIA Quantification Module for Ion level Quantification."""

    def __init__(
        self,
        token: str,
        proteobot_repo_name: str = "Proteobot/Results_quant_ion_DIA_diaPASEF",
        proteobench_repo_name: str = "Proteobench/Results_quant_ion_DIA_diaPASEF",
        parse_settings_dir: str = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "io",
                "parsing",
                "io_parse_settings",
                "Quant",
                "DIA",
                "diaPASEF",
            )
        ),
        module_id="quant_lfq_ion_DIA_diaPASEF",
    ):
        """
        DIA Quantification Module for Ion level Quantification for diaPASEF.

        Parameters
        ----------
        token
            GitHub token for the user.
        proteobot_repo_name
            Name of the repository for pull requests and where new points are added.
        proteobench_repo_name
            Name of the repository where the benchmarking results will be stored.

        Attributes
        ----------
        precursor_name: str
            Level of quantification.

        """
        super().__init__(
            token,
            proteobot_repo_name=proteobot_repo_name,
            proteobench_repo_name=proteobench_repo_name,
            parse_settings_dir=parse_settings_dir,
            module_id=module_id,
        )
        self.precursor_name = "precursor ion"
