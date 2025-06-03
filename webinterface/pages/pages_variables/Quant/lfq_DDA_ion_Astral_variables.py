"""
Variables for the DDA quantification - precursor ions module.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDDAQuantAstral:
    """
    Variables for the DDA quantification - precursor ions Astral module.
    """

    all_datapoints: str = "all_datapoints_Astral"
    all_datapoints_submission: str = "all_datapoints_submission_dda_quant_Astral"
    input_df_submission: str = "input_df_submission_dda_quant_Astral"
    result_performance_submission: str = "result_performance_submission_dda_quant_Astral"
    submit: str = "submit_dda_quant_Astral"
    fig_logfc: str = "fig_logfc_dda_quant_Astral"
    fig_metric: str = "fig_metric_dda_quant_Astral"
    fig_cv: str = "fig_CV_violinplot_dda_quant_Astral"
    fig_ma_plot: str = "fig_ma_plot_dda_quant_Astral"
    result_perf: str = "result_perf_dda_quant_Astral"
    meta_data: str = "meta_data_dda_quant_Astral"
    input_df: str = "input_df_dda_quant_Astral"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dda_quant_Astral"
    comments_submission_uuid: str = "comments_submission_uuid_dda_quant_Astral"
    check_submission_uuid: str = "check_submission_uuid_dda_quant_Astral"
    meta_data_text: str = "comments_for_submission_dda_quant_Astral"
    check_submission: str = "heck_submission_dda_quant_Astral"
    button_submission_uuid: str = "button_submission_uuid_dda_quant_Astral"
    df_head: str = "df_head_dda_quant_Astral"
    placeholder_fig_compare: str = "placeholder_fig_compare_dda_quant_Astral"

    all_datapoints_submitted: str = "all_datapoints_submitted_dda_quant_Astral"
    placeholder_table_submitted: str = "placeholder_table_submitted_dda_quant_Astral"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dda_quant_Astral"
    highlight_list_submitted: List[str] = field(default_factory=list)
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dda_quant_Astral"
    selectbox_id_uuid: str = "selectbox_id_dda_quant_Astral"
    slider_id_submitted_uuid: str = "slider_id_submitted_dda_quant_Astral"
    slider_id_uuid: str = "slider_id_dda_quant_Astral"
    download_selector_id_uuid: str = "download_selector_id_dda_quant_Astral"
    table_id_uuid: str = "table_id_dda_quant_Astral"

    placeholder_table: str = "placeholder_table_dda_quant_Astral"
    placeholder_slider: str = "placeholder_slider_dda_quant_Astral"

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dda_quant_Astral"
    dataset_selector_id_uuid: str = "dataset_selector_id_dda_quant_Astral"

    placeholder_downloads_container: str = "placeholder_downloads_container_dda_quant_Astral"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DDA_Astral.git"

    description_module_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/introduction_DDA_quan_ions.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DDA/ion/Astral/submit_description.md"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/Astral"

    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = "https://proteobench.readthedocs.io/en/latest/available-modules/8-quant-lfq-precursor-dda-Astral/"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DDA_ion.json"
    title: str = "DDA Ion quantification (Astral)"
    prefix_params: str = "lfq_ion_dda_quant_Astral_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_quant_astral"
    params_file_dict: str = "params_file_dict_lfq_ion_dda_quant_astral"
