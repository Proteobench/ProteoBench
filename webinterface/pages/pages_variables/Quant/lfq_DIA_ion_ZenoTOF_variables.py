"""
Variables for the DIA quantification module using ZenoTOF.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DIAQuantIonModuleZenoTOF


@dataclass
class VariablesDIAQuantZenoTOF(VariablesBase):
    """
    Variables for the DIA quantification module using ZenoTOF.
    """

    key: str = "dia_quant_ZenoTOF"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF"
    ionmodule = DIAQuantIonModuleZenoTOF
    uiobjects = QuantUIObjects
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_ZenoTOF.git"
    sidebar_label: str = "Quant LFQ DIA ion ZenoTOF"
    homepage_title: str = "LFQ Quantification on a ZenoTOF"
    graphical_abstract: str = "Graphical_abstract_Quant_zenoTOF.png"
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DIA (Zeno SWATH) workflows using a multi-species (HYE) sample on a ZenoTOF 8600 instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DIA_ion_ZenoTOF"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "quantification", "ZenoTOF", "SCIEX", "precursor", "ion", "LFQ", "TOF"]
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
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/ZenoTOF"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-zenotof/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DIA-ZenoSWATH/all_data_LFQ_Quant_DIA_ZenoSWATH.tar.gz"
    title: str = "DIA Precursor ion quantification - ZenoTOF"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
