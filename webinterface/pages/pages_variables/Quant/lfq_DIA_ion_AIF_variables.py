"""
Variables for the DIA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDIAQuant:
    """
    Variables for the DIA quantification - precursor ions module.
    """

    all_datapoints: str = "all_datapoints_dia_quant"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant"
    input_df_submission: str = "input_df_submission_dia_quant"
    result_performance_submission: str = "result_performance_submission_dia_quant"
    submit: str = "submit_dia_quant"
    fig_logfc: str = "fig_logfc_dia_quant"
    fig_metric: str = "fig_metric_dia_quant"
    fig_cv: str = "fig_CV_violinplot_dia_quant"
    fig_ma_plot: str = "fig_ma_plot_dia_quant"
    result_perf: str = "result_perf_dia_quant"
    meta_data: str = "meta_data_dia_quant"
    input_df: str = "input_df_dia_quant"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant"
    check_submission_uuid: str = "check_submission_uuid_dia_quant"
    meta_data_text: str = "comments_for_submission_dia_quant"
    check_submission: str = "heck_submission_dia_quant"
    button_submission_uuid: str = "button_submission_uuid_dia_quant"
    df_head: str = "df_head_dia_quant"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant"
    placeholder_table: str = "placeholder_table_dia_quant"
    placeholder_slider: str = "placeholder_slider_dia_quant"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA.git"
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant"
    selectbox_id_uuid: str = "selectbox_id_dia_quant"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant"
    slider_id_uuid: str = "slider_id_dia_quant"
    download_selector_id_uuid: str = "download_selector_id_dia_quant"
    table_id_uuid: str = "table_id_dia_quant"
    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/AIF/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/AIF"

    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/available-modules/4-quant-lfq-ion-dia-aif/"

    title: str = "DIA Precursor quantification - AIF"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_aif_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_aif_quant"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_aif_quant"
