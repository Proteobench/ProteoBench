"""
Variables for the DDA de novo identification module.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts_denovo import WebpageTexts


@dataclass
class VariablesDDADeNovo:
    """
    Variables for the DDA de novo identification module.
    """

    all_datapoints: str = "all_datapoints_dda_hcd_denovo"
    all_datapoints_submission: str = "all_datapoints_submission_dda_hcd_denovo"
    input_df_submission: str = "input_df_submission_dda_hcd_denovo"
    result_performance_submission: str = "result_performance_submission_dda_hcd_denovo"
    submit: str = "submit_dda_hcd_denovo"
    fig_metric: str = "fig_metric_dda_hcd_denovo"
    fig_metric_submitted: str = "fig_metric_dda_hcd_denovo_submitted"
    # fig_logfc: str = "fig_logfc_dda_hcd_denovo"
    # fig_metric: str = "fig_metric_dda_hcd_denovo"
    # fig_cv: str = "fig_CV_violinplot_dda_hcd_denovo"
    # fig_ma_plot: str = "fig_ma_plot_dda_hcd_denovo"
    result_perf: str = "result_perf_dda_hcd_denovo"
    meta_data: str = "meta_data_dda_hcd_denovo"
    input_df: str = "input_df_dda_hcd_denovo"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dda_hcd_denovo"
    comments_submission_uuid: str = "comments_submission_uuid_dda_hcd_denovo"
    check_submission_uuid: str = "check_submission_uuid_dda_hcd_denovo"
    meta_data_text: str = "comments_for_submission_dda_hcd_denovo"
    check_submission: str = "heck_submission_dda_hcd_denovo"
    button_submission_uuid: str = "button_submission_uuid_dda_hcd_denovo"
    df_head: str = "df_head_dda_hcd_denovo"
    placeholder_fig_compare: str = "placeholder_fig_compare_dda_hcd_denovo"

    all_datapoints_submitted: str = "all_datapoints_submitted_dda_hcd_denovo"
    placeholder_table_submitted: str = "placeholder_table_submitted_dda_hcd_denovo"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dda_hcd_denovo"
    highlight_list_submitted: List[str] = field(default_factory=list)
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dda_hcd_denovo"
    selectbox_id_uuid: str = "selectbox_id_dda_hcd_denovo"

    radio_level_id_uuid: str = "radio_level_id_dda_hcd_denovo"
    radio_evaluation_id_uuid: str = "radio_evaluation_id_dda_hcd_denovo"
    radio_level_id_submitted_uuid: str = "radio_level_id_submitted_dda_hcd_denovo"
    radio_evaluation_id_submitted_uuid: str = "radio_evaluation_id_submitted_dda_hcd_denovo"
    
    download_selector_id_uuid: str = "download_selector_id_dda_hcd_denovo"
    table_id_uuid: str = "table_id_dda_hcd_denovo"

    placeholder_table: str = "placeholder_table_dda_hcd_denovo"
    placeholder_slider: str = "placeholder_slider_dda_hcd_denovo"

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dda_hcd_denovo"
    dataset_selector_id_uuid: str = "dataset_selector_id_dda_hcd_denovo"

    placeholder_downloads_container: str = "placeholder_downloads_container_dda_hcd_denovo"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True

    default_level = "Peptide"
    default_evaluation = "Mass-based"

    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_denovo_lfq_DDA_HCD.git"

    description_module_md: str = "pages/markdown_files/DeNovo/DDA/introduction_DDA_quan_ions.md"
    description_files_md: str = "pages/markdown_files/DeNovo/DDA/file_description.md"
    description_input_file_md: str = "pages/markdown_files/DeNovo/DDA/input_file_description.md"
    description_radios_md: str = "pages/markdown_files/DeNovo/DDA/radios_description.md"
    description_table_md: str = "pages/markdown_files/DeNovo/DDA/table_description.md"
    description_results_md: str = "pages/markdown_files/DeNovo/DDA/result_description.md"
    description_submission_md: str = "pages/markdown_files/DeNovo/DDA/submit_description.md"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/denovo/lfq/DDA/HCD"

    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/available-modules/8-quant-lfq-precursor-dda-Astral/"

    additional_params_json: str = "../proteobench/io/params/json/denovo/denovo_lfq_DDA_HCD.json"
    title: str = "De Novo Identification (DDA - HCD) Module"
    prefix_params: str = "lfq_ion_dda_hcd_denovo_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_hcd_denovo"
    params_file_dict: str = "params_file_dict_lfq_ion_dda_hcd_denovo"
