"""
Variables for the DDA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DDAQuantIonModuleQExactive


@dataclass
class VariablesDDAQuant(VariablesBase):
    """
    Variables for the DDA quantification - precursor ions module.
    """

    key: str = "dda_quant_QExactive"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DDA/ion/QExactive"
    ionmodule = DDAQuantIonModuleQExactive
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
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DDA.git"
    sidebar_label: str = "Quant LFQ DDA ion QExactive"
    homepage_title: str = "LFQ Quantification on a QExactive"
    graphical_abstract: str = "Graphical_abstract_Quant_QExactive.png"
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DDA workflows using a multi-species (HYE) sample on an Orbitrap QExactive instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DDA_ion_QExactive"
    sidebar_category: str = "DDA"
    keywords: List[str] = field(
        default_factory=lambda: ["DDA", "quantification", "QExactive", "orbitrap", "precursor", "ion", "LFQ"]
    )
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/QExactive"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dda/dda-ion-qexactive/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DDA/all_data_LFQ_Quant_DDA_QExactive.tar.gz"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DDA_ion.json"
    title: str = "DDA Precursor quantification (QExactive)"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
