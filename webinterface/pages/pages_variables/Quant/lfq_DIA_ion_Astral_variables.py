"""
Variables for the DIA quantification module using Astral.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


# TODO: restructure the variable names. Do this for the other pages_variables as well.
@dataclass
class VariablesDIAQuantAstral:
    """
    Variables for the DIA quantification module using Astral.
    """

    all_datapoints: str = "all_datapoints_dia_quant_Astral"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_Astral"
    input_df_submission: str = "input_df_submission_dia_quant_Astral"
    result_performance_submission: str = "result_performance_submission_dia_quant_Astral"
    submit: str = "submit_dia_quant_Astral"
    fig_logfc: str = "fig_logfc_dia_quant_Astral"
    fig_metric: str = "fig_metric_dia_quant_Astral"
    fig_cv: str = "fig_CV_violinplot_dia_quant_Astral"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_Astral"
    result_perf: str = "result_perf_dia_quant_Astral"
    meta_data: str = "meta_data_dia_quant_Astral"
    input_df: str = "input_df_dia_quant_Astral"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_Astral"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_Astral"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_Astral"
    meta_data_text: str = "comments_for_submission_dia_quant_Astral"
    check_submission: str = "check_submission_dia_quant_Astral"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_Astral"
    df_head: str = "df_head_dia_quant_Astral"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_diPASEF"
    placeholder_table: str = "placeholder_table_dia_quant_Astral"
    placeholder_slider: str = "placeholder_slider_dia_quant_Astral"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_Astral"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_Astral.git"
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_Astral"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_Astral"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_Astral"
    slider_id_uuid: str = "slider_id_dia_quant_Astral"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_Astral"
    table_id_uuid: str = "table_id_dia_quant_Astral"

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Astral/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_Astral"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_Astral"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_Astral"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_Astral"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_Astral"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/Astral"

    texts: Type[WebpageTexts] = WebpageTexts

    doc_url: str = (
        "https://proteobench.readthedocs.io/en/latest/available-modules/7-quant-lfq-precursor-dia-Astral_2Th/"
    )

    title: str = "DIA Precursor ion quantification - Astral 2 Th"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_Astral_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_Astral_quant"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_Astral_quant"
