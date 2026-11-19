"""
Variables for the DIA quantification - precursor ions module - lowinput.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DIAQuantIonModulediaSC


@dataclass
class VariablesDIAQuantLI(VariablesBase):
    """
    Variables for the DIA quantification - precursor ions module - low input.
    """

    key: str = "dia_quant_lowinput"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput"
    ionmodule = DIAQuantIonModulediaSC
    uiobjects = QuantUIObjects
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = False
    beta_warning: bool = False
    archived_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_lowinput.git"
    sidebar_label: str = "Quant LFQ DIA ion Low Input"
    homepage_title: str = "LFQ Quantification for Low-Input"
    graphical_abstract: str = "Graphical_abstract_low_input.png"
    documentation_description: str = (
        "Archived: benchmarked low-input (close to single-cell level) DIA quantification workflows on an "
        "Orbitrap Astral. Superseded by the Astral and timsTOF low-input (200 pg) modules."
    )
    sidebar_path: str = "/Quant_LFQ_DIA_ion_lowinput"
    sidebar_category: str = "Archived"
    keywords: List[str] = field(
        default_factory=lambda: [
            "DIA",
            "quantification",
            "low_input",
            "Astral",
            "precursor",
            "ion",
            "LFQ",
            "single-cell",
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
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/lowinput"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-lowinput/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DIA-SingleCell/all_data_LFQ_Quant_DIA_SC.tar.gz"
    title: str = "DIA Precursor quantification - Low Input"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
