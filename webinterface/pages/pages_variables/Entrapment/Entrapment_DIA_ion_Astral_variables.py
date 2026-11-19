"""
Variables for the DDA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List

from pages.base_pages.entrapment import EntrapmentUIObjects
from pages.pages_variables.base import VariablesBase

from proteobench.modules.entrapment.entrapment_ion_DIA_Astral import DIAEntrapmentIonModuleAstral


@dataclass
class VariablesDIAEntrapmentAstral(VariablesBase):
    """
    Variables for the DIA entrapment - precursor ions Astral module.
    """

    key: str = "dia_entrapment_Astral"
    markdown_dir: str = "pages/markdown_files/Entrapment/DIA/ion/Astral"
    ionmodule = DIAEntrapmentIonModuleAstral
    uiobjects = EntrapmentUIObjects
    metric_plot_labels: List[str] = field(
        default_factory=lambda: [
            "None",
            "precursor_mass_tolerance",
            "fragment_mass_tolerance",
            "enable_match_between_runs",
            "max_mods",
            "enzyme",
            "reported_fdr_parsed_from_input",
            "ident_fdr_peptide",
            "allowed_miscleavages",
        ]
    )
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = False
    enable_pmultiqc: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_entrapment_ion_DIA_Astral.git"
    sidebar_label: str = "Entrapment DIA ion Astral"
    homepage_title: str = "FDR Entrapment on an Astral"
    graphical_abstract: str = "Graphical_abstract_entrapment.png"
    documentation_description: str = (
        "Benchmark FDR Validation of workflows for DIA acquisitions using FDRBench entrapment on an Astral."
    )
    sidebar_path: str = "/Entrapment_DIA_ion_Astral"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "entrapment", "Astral", "orbitrap", "precursor", "ion", "FDR", "Validation"]
    )
    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/entrapment/DIA/ion/Astral"
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/entrapment-dia-astral/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/all_data_Entrapment_DIA_Astral.tar.gz"
    additional_params_json: str = "../proteobench/io/params/json/Entrapment/entrapment_DIA_ion.json"
    title: str = "FDRBench - DIA Ion Entrapment (Astral)"
