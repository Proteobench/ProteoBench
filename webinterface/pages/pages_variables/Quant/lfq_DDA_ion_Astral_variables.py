"""
Variables for the DDA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DDAQuantIonAstralModule


@dataclass
class VariablesDDAQuantAstral(VariablesBase):
    """
    Variables for the DDA quantification - precursor ions Astral module.
    """

    key: str = "dda_quant_Astral"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral"
    ionmodule = DDAQuantIonAstralModule
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
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DDA_Astral.git"
    sidebar_label: str = "Quant LFQ DDA ion Astral"
    homepage_title: str = "LFQ Quantification on an Astral"
    graphical_abstract: str = "Graphical_abstract_Quant_astral.png"
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DDA workflows using a multi-species (HYE) sample on an Orbitrap Astral instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DDA_ion_Astral"
    sidebar_category: str = "DDA"
    keywords: List[str] = field(
        default_factory=lambda: ["DDA", "quantification", "Astral", "orbitrap", "precursor", "ion", "LFQ"]
    )
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/Astral"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dda/dda-ion-astral/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DDA-astral/all_data_LFQ_Quant_DDA_Astral.tar.gz"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DDA_ion.json"
    title: str = "DDA Ion quantification (Astral)"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
