"""
Variables for the DIA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DIAQuantIonModuleAIF


@dataclass
class VariablesDIAQuant(VariablesBase):
    """
    Variables for the DIA quantification - precursor ions module.
    """

    key: str = "dia_quant"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF"
    ionmodule = DIAQuantIonModuleAIF
    uiobjects = QuantUIObjects
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA.git"
    sidebar_label: str = "Quant LFQ DIA ion AIF"
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DIA (All-Ion Fragmentation) workflows using a multi-species (HYE) sample on an Orbitrap instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DIA_ion_AIF"
    sidebar_category: str = "Archived"
    keywords: List[str] = field(
        default_factory=lambda: [
            "DIA",
            "quantification",
            "AIF",
            "all ion fragmentation",
            "precursor",
            "ion",
            "LFQ",
            "QExactive",
        ]
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
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/AIF"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-aif/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DIA/all_data_LFQ_Quant_DIA_AIF.tar.gz"
    title: str = "DIA Precursor quantification - AIF"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
