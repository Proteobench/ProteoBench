"""
Variables for the DDA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDIAEntrapmentAstral:
    """
    Variables for the DIA entrapment - precursor ions Astral module.
    """

    all_datapoints: str = "all_datapoints_Astral"
    all_datapoints_submission: str = "all_datapoints_submission_dia_entrapment_Astral"
    input_df_submission: str = "input_df_submission_dia_entrapment_Astral"
    result_performance_submission: str = "result_performance_submission_dia_entrapment_Astral"
    submit: str = "submit_dia_entrapment_Astral"
    fig_logfc: str = "fig_logfc_dia_entrapment_Astral"
    fig_metric: str = "fig_metric_dia_entrapment_Astral"
    fig_cv: str = "fig_CV_violinplot_dia_entrapment_Astral"
    fig_ma_plot: str = "fig_ma_plot_dia_entrapment_Astral"
    fig_prefix: str = "fig_dia_entrapment_Astral_"
    result_perf: str = "result_perf_dia_entrapment_Astral"
    meta_data: str = "meta_data_dia_entrapment_Astral"
    input_df: str = "input_df_dia_entrapment_Astral"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_entrapment_Astral"
    comments_submission_uuid: str = "comments_submission_uuid_dia_entrapment_Astral"
    check_submission_uuid: str = "check_submission_uuid_dia_entrapment_Astral"
    meta_data_text: str = "comments_for_submission_dia_entrapment_Astral"
    check_submission: str = "heck_submission_dia_entrapment_Astral"
    button_submission_uuid: str = "button_submission_uuid_dia_entrapment_Astral"
    df_head: str = "df_head_dia_entrapment_Astral"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_entrapment_Astral"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_entrapment_Astral"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_entrapment_Astral"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_entrapment_Astral"
    highlight_list_submitted: List[str] = field(default_factory=list)
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_entrapment_Astral"
    selectbox_id_uuid: str = "selectbox_id_dia_entrapment_Astral"
    selectbox_id_indepth_uuid: str = "selectbox_id_indepth_dia_entrapment_Astral"
    colorblind_mode_selector_uuid: str = "colorblind_mode_selector_dia_entrapment_Astral"
    colorblind_mode_selector_submitted_uuid: str = "colorblind_mode_selector_submitted_dia_entrapment_Astral"
    colorblind_mode_selector_indepth_uuid: str = "colorblind_mode_selector_indepth_dia_entrapment_Astral"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_entrapment_Astral"
    slider_id_uuid: str = "slider_id_dia_entrapment_Astral"
    slider_id_indepth_uuid: str = "slider_id_indepth_dia_entrapment_Astral"
    download_selector_id_uuid: str = "download_selector_id_dia_entrapment_Astral"
    table_id_uuid: str = "table_id_dia_entrapment_Astral"
    table_new_results_uuid: str = "table_new_results_uuid_dia_entrapment_Astral"
    result_plot_uuid: str = "result_figure_uuid_dia_entrapment_Astral"
    result_submitted_plot_uuid: str = "result_submitted_figure_uuid_dia_entrapment_Astral"
    metric_selector_uuid: str = "metric_selector_uuid_dia_entrapment_Astral"
    metric_selector_submitted_uuid: str = "metric_selector_submitted_uuid_dia_entrapment_Astral"
    metric_selector_indepth_uuid: str = "metric_selector_indepth_uuid_dia_entrapment_Astral"
    metric_calc_approach_selector_submitted_uuid: str = (
        "metric_calc_approach_selector_submitted_uuid_dia_entrapment_Astral"
    )
    metric_calc_approach_selector_uuid: str = "metric_calc_approach_selector_uuid_dia_entrapment_Astral"
    metric_calc_approach_selector_indepth_uuid: str = "metric_calc_approach_selector_indepth_uuid_dia_entrapment_Astral"
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

    placeholder_table: str = "placeholder_table_dia_entrapment_Astral"
    placeholder_slider: str = "placeholder_slider_dia_entrapment_Astral"

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_entrapment_Astral"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_entrapment_Astral"

    placeholder_downloads_container: str = "placeholder_downloads_container_dia_entrapment_Astral"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = True
    beta_warning: bool = False
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_entrapment_ion_DIA_Astral.git"

    # Sidebar metadata
    sidebar_label: str = "Entrapment DIA ion Astral"
    sidebar_path: str = "/Entrapment_DIA_ion_Astral"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "entrapment", "Astral", "orbitrap", "precursor", "ion", "FDR"]
    )

    description_module_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/introduction_DIA_quan_ions.md"
    description_files_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/slider_description.md"
    description_table_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/table_description.md"
    description_results_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/result_description.md"
    description_submission_md: str = "pages/markdown_files/Entrapment/DIA/ion/Astral/submit_description.md"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/Astral"

    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = (
        "https://proteobench.readthedocs.io/en/latest/available-modules/active-modules/13-entrapment-ion-dia-astral/"
    )
    raw_data_url: str = (
        "https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/all_data_Entrapment_DIA_Astral.tar.gz"
    )

    additional_params_json: str = "../proteobench/io/params/json/Entrapment/entrapment_DIA_ion.json"
    title: str = "FDRBench - DIA Ion Entrapment (Astral)"
    prefix_params: str = "ion_dia_entrapment_Astral_"
    params_json_dict: str = "params_json_dict_lfq_ion_dia_entrapment_astral"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_entrapment_astral"
