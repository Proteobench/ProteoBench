from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDDAQuant:
    all_datapoints: str = "all_datapoints_dda_quant_peptidoform"
    all_datapoints_submission: str = "all_datapoints_submission_dda_quant_peptidoform"
    input_df_submission: str = "input_df_submission_dda_quant_peptidoform"
    result_performance_submission: str = "result_performance_submission_dda_quant_peptidoform"
    submit: str = "submit_dda_quant_peptidoform"
    fig_logfc: str = "fig_logfc_dda_quant_peptidoform"
    fig_metric: str = "fig_metric_dda_quant_peptidoform"
    fig_cv: str = "fig_CV_violinplot_dda_quant_peptidoform"
    result_perf: str = "result_perf_dda_quant_peptidoform"
    meta_data: str = "meta_data_dda_quant_peptidoform"
    input_df: str = "input_df_dda_quant_peptidoform"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dda_quant_peptidoform"
    comments_submission_uuid: str = "comments_submission_uuid_dda_quant_peptidoform"
    check_submission_uuid: str = "check_submission_uuid_dda_quant_peptidoform"
    meta_data_text: str = "comments_for_submission_dda_quant_peptidoform"
    check_submission: str = "heck_submission_dda_quant_peptidoform"
    button_submission_uuid: str = "button_submission_uuid_dda_quant_peptidoform"
    df_head: str = "df_head_dda_quant_peptidoform"
    placeholder_fig_compare: str = "placeholder_fig_compare_dda_quant_peptidoform"
    placeholder_table: str = "placeholder_table_dda_quant_peptidoform"
    placeholder_slider: str = "placeholder_slider_dda_quant_peptidoform"
    placeholder_downloads_container: str = "placeholder_downloads_container"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_peptidoform_DDA.git"

    additional_params_json: str = "../webinterface/configuration/dda_quant.json"

    description_module_md: str = "pages/markdown_files/DDA_Quant/introduction.md"
    description_files_md: str = "pages/markdown_files/DDA_Quant/file_description.md"
    description_input_file_md: str = "pages/markdown_files/DDA_Quant/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/DDA_Quant/slider_description.md"
    description_table_md: str = "pages/markdown_files/DDA_Quant/table_description.md"
    description_results_md: str = "pages/markdown_files/DDA_Quant/result_description.md"
    description_submission_md: str = "pages/markdown_files/DDA_Quant/submit_description.md"

    texts: Type[WebpageTexts] = WebpageTexts
