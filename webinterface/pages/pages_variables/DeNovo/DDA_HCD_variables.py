"""
Variables for the DDA de novo identification module.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.base_pages.denovo import DeNovoUIObjects
from pages.pages_variables.base import VariablesBase
from pages.texts.generic_texts_denovo import WebpageTexts

from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule


@dataclass
class VariablesDDADeNovo(VariablesBase):
    """
    Variables for the DDA de novo identification module.
    """

    has_slider = False

    key: str = "dda_hcd_denovo"
    markdown_dir: str = "pages/markdown_files/DeNovo/DDA"
    ionmodule = DDAHCDDeNovoModule
    uiobjects = DeNovoUIObjects
    tabs = [
        ("View Public Results", "display_all_data_results_main"),
        ("Upload New Results (Private)", "display_submission_form"),
        ("View Public + New Results", "display_all_data_results_submitted"),
        ("Compare Results", "display_indepth_plots"),
        ("Submit New Results", "display_public_submission_ui"),
    ]
    fig_pc_curve: str = "fig_pc_curve_dda_hcd_denovo"
    metric_plot_labels: List[str] = field(
        default_factory=lambda: ["None", "checkpoint", "n_beams", "precursor_mass_tolerance", "decoding_strategy"]
    )
    fig_species_overview: str = "fig_species_overview_dda_hcd_denovo"
    evaluation_mode_toggle_tab3_features: str = "evaluation_mode_toggle_tab3_features_dda_hcd_denovo"
    evaluation_mode_toggle_tab3_species: str = "evaluation_mode_toggle_tab3_species_dda_hcd_denovo"
    fig_metric_submitted: str = "fig_metric_dda_hcd_denovo_submitted"
    fig_pc_curve_submitted: str = "fig_pc_curve_dda_hcd_denovo_submitted"
    radio_level_id_uuid: str = "radio_level_id_dda_hcd_denovo"
    radio_evaluation_id_uuid: str = "radio_evaluation_id_dda_hcd_denovo"
    radio_level_id_submitted_uuid: str = "radio_level_id_submitted_dda_hcd_denovo"
    radio_evaluation_id_submitted_uuid: str = "radio_evaluation_id_submitted_dda_hcd_denovo"
    il_toggle_id_uuid: str = "il_toggle_id_dda_hcd_denovo"
    il_toggle_id_submitted_uuid: str = "il_toggle_id_submitted_dda_hcd_denovo"
    deamidation_toggle_id_uuid: str = "deamidation_toggle_id_dda_hcd_denovo"
    deamidation_toggle_id_submitted_uuid: str = "deamidation_toggle_id_submitted_dda_hcd_denovo"
    default_level = "Precision"
    default_evaluation = "Mass-based"
    beta_warning: bool = False
    alpha_warning: bool = True
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_denovo_lfq_DDA_HCD.git"
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/denovo/DDA/HCD"
    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dda/denovo-dda-hcd/"
    additional_params_json: str = "../proteobench/io/params/json/denovo/denovo_DDA_HCD.json"
    title: str = "De Novo Identification (DDA - HCD) Module"
    sidebar_label: str = "De novo DDA peptidoform"
    homepage_title: str = "De Novo Sequencing on DDA-HCD"
    graphical_abstract: str = "Graphical_abstract_denovo_smaller.png"
    documentation_description: str = (
        "Benchmark the identification sensitivity and specificity of de novo sequencing workflows using DDA-HCD data."
    )
    sidebar_path: str = "/denovo_DDA_HCD"
    sidebar_category: str = "DDA"
    keywords: List[str] = field(default_factory=lambda: ["DDA", "de novo", "orbitrap", "precursor", "identification"])
