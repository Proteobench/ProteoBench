"""
Variables for the DDA quantification - peptidoform module.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DDAQuantPeptidoformModule


@dataclass
class VariablesDDAQuant(VariablesBase):
    """
    Variables for the DDA quantification - peptidoform module.
    """

    key: str = "dda_quant_peptidoform"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DDA/peptidoform"
    ionmodule = DDAQuantPeptidoformModule
    uiobjects = QuantUIObjects
    metric_plot_labels: List[str] = field(
        default_factory=lambda: [
            "None",
            "precursor_mass_tolerance",
            "fragment_mass_tolerance",
            "enable_match_between_runs",
            "max_mods",
            "enzyme",
            "ident_fdr_psm",
            "ident_fdr_peptide",
            "allowed_miscleavages",
        ]
    )
    default_val_slider: int = 3
    max_nr_observed: int = 6
    beta_warning: bool = True
    alpha_warning: bool = False
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_peptidoform_DDA.git"
    sidebar_label: str = "Quant LFQ DDA peptidoform"
    homepage_title: str = "LFQ Quantification at the Peptidoform Level"
    graphical_abstract: str = "Graphical_abstract_Quant_QExactive.png"
    documentation_description: str = (
        "Benchmark peptidoform-level label-free quantification accuracy of DDA workflows using a multi-species (HYE) sample on an Orbitrap QExactive instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DDA_peptidoform"
    sidebar_category: str = "DDA"
    keywords: List[str] = field(
        default_factory=lambda: ["DDA", "quantification", "peptidoform", "modified peptide", "LFQ", "QExactive"]
    )
    additional_params_json: str = "../webinterface/configuration/dda_quant.json"
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/peptidoform/"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dda/dda-peptidoform/"
    title: str = "DDA peptidoform quantification"
    y_axis_title: str = "Total number of peptidoforms quantified in the selected number of raw files"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DDA_peptidoform.json"
