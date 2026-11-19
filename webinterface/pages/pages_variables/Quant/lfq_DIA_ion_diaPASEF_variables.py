"""
Variables for the DIA quantification module using diaPASEF.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DIAQuantIonModulediaPASEF


@dataclass
class VariablesDIAQuantdiaPASEF(VariablesBase):
    """
    Variables for the DIA quantification module using diaPASEF.
    """

    key: str = "dia_quant_diaPASEF"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DIA/ion/diaPASEF"
    ionmodule = DIAQuantIonModulediaPASEF
    uiobjects = QuantUIObjects
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_diaPASEF.git"
    sidebar_label: str = "Quant LFQ DIA ion diaPASEF"
    homepage_title: str = "LFQ Quantification on a timsTOF (diaPASEF)"
    graphical_abstract: str = "Graphical_abstract_Quant_timsTOF.png"
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DIA-PASEF workflows using a multi-species (HYE) sample on a timsTOF instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DIA_ion_diaPASEF"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "quantification", "diaPASEF", "timsTOF", "precursor", "ion", "LFQ", "PASEF"]
    )
    metric_plot_labels: List[str] = field(
        default_factory=lambda: [
            "None",
            "enable_match_between_runs",
            "max_mods",
            "enzyme",
            "ident_fdr_psm",
            "ident_fdr_peptide",
            "allowed_miscleavages",
            "quantification_method",
        ]
    )
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/diaPASEF"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-diapasef/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/diaPASEF/all_data_LFQ_Quant_DIA_diaPASEF.tar.gz"
    title: str = "DIA Precursor quantification - diaPASEF"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
