"""
Variables for the DIA quantification - precursor ions module - singlecell.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDIAQuantSC:
    """
    Variables for the DIA quantification - precursor ions module - single-cell.
    """

    all_datapoints: str = "all_datapoints_dia_quant_singlecell"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_singlecell"
    input_df_submission: str = "input_df_submission_dia_quant_singlecell"
    result_performance_submission: str = "result_performance_submission_dia_quant_singlecell"
    submit: str = "submit_dia_quant_singlecell"
    fig_logfc: str = "fig_logfc_dia_quant_singlecell"
    fig_metric: str = "fig_metric_dia_quant_singlecell"
    fig_cv: str = "fig_CV_violinplot_dia_quant_singlecell"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_singlecell"
    result_perf: str = "result_perf_dia_quant_singlecell"
    meta_data: str = "meta_data_dia_quant_singlecell"
    input_df: str = "input_df_dia_quant_singlecell"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_singlecell"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_singlecell"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_singlecell"
    meta_data_text: str = "comments_for_submission_dia_quant_singlecell"
    check_submission: str = "heck_submission_dia_quant_singlecell"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_singlecell"
    df_head: str = "df_head_dia_quant_singlecell"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_singlecell"
    placeholder_table: str = "placeholder_table_dia_quant_singlecell"
    placeholder_slider: str = "placeholder_slider_dia_quant_singlecell"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_singlecell"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA.git_singlecell"
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_singlecell"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_singlecell"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_singlecell"
    slider_id_uuid: str = "slider_id_dia_quant_singlecell"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_singlecell"
    table_id_uuid: str = "table_id_dia_quant_singlecell"

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/singlecell/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_singlecell"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_singlecell"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_singlecell"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_singlecell"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_singlecell"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/singlecell"

    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/available-modules/6-quant-lfq-ion-dia-singlecell/"

    title: str = "DIA Precursor quantification - singlecell"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_singlecell_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_singlecell_quant_singlecell"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_singlecell_quant_singlecell"
