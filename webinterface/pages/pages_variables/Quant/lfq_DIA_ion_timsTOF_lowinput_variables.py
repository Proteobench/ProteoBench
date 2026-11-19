"""
Variables for the DIA quantification module using timsTOF on low-input.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.quant import QuantUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.quant.quant_modules import DIAQuantIonModuletimsTOFLowInput


@dataclass
class VariablesDIAQuanttimsTOFLowinput(VariablesBase):
    """
    Variables for the DIA quantification module using timsTOF on low-input.
    """

    key: str = "dia_quant_timsTOF_lowinput"
    markdown_dir: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput"
    ionmodule = DIAQuantIonModuletimsTOFLowInput
    uiobjects = QuantUIObjects
    default_val_slider: int = 6
    max_nr_observed: int = 12
    alpha_warning: bool = True
    beta_warning: bool = False
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_timsTOF_lowinput.git"
    sidebar_label: str = "Quant LFQ DIA ion timsTOF (low-input)"
    homepage_title: str = "LFQ Quantification on a timsTOF Ultra 2 on low-input (200 pg)"
    graphical_abstract: str = "Graphical_abstract_Quant_timsTOF.png"  # TODO change!
    documentation_description: str = (
        "Benchmark ion-level label-free quantification accuracy of DIA-PASEF workflows using a low-input (200pg) multi-species (HYE) sample on a timsTOF instrument."
    )
    sidebar_path: str = "/Quant_LFQ_DIA_ion_timsTOF_lowinput"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: [
            "DIA",
            "quantification",
            "timsTOF",
            "precursor",
            "ion",
            "LFQ",
            "PASEF",
            "single-cell",
            "low-input",
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
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/timsTOF_lowinput"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-timstof-lowinput/"
    raw_data_url: str = (
        "https://proteobench.cubimed.rub.de/raws/DIA-timstof-lowinput/all_data_LFQ_Quant_DIA_timsTOF_lowinput.tar.gz"
    )
    title: str = "DIA Precursor quantification - timsTOF (low-input)"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"
    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
