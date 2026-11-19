"""
Variables for the DIA quantification module using Plasma.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DIAQuantIonModulePlasma


@dataclass
class VariablesDIAQuantPlasma(VariablesBase):
    """
    Variables for the DIA quantification module using Plasma.
    """

    key: str = "dia_quant_Plasma"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma"
    ionmodule = DIAQuantIonModulePlasma
    uiobjects = QuantUIObjects
    tour = False  # the Plasma page has never offered the quant guided tour
    default_val_slider: int = 6
    max_nr_observed: int = 12
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_Plasma.git"
    sidebar_label: str = "Quant LFQ DIA ion Plasma"
    homepage_title: str = "LFQ Quantification on Human Plasma"
    graphical_abstract: str = "Graphical_abstract_Quant_plasma.png"
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DIA workflows using a high dynamic range human plasma multi-species (PYE) sample aquired on a timsTOF."
    )
    sidebar_path: str = "/Quant_LFQ_DIA_ion_Plasma"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "quantification", "Plasma", "precursor", "ion", "LFQ", "spike-in", "timsTOF"]
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
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/plasma"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-plasma/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DIA-plasma/all_data_LFQ_Quant_DIA_Plasma.tar.gz"
    title: str = "DIA Precursor quantification - Plasma"
    y_axis_title: str = "Number of quantified spike-in precursors"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
