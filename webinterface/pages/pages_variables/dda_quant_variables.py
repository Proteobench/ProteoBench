from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDDAQuant:
    all_datapoints: str = "all_datapoints"
    all_datapoints_submission: str = "all_datapoints_submission"
    input_df_submission: str = "input_df_submission"
    result_performance_submission: str = "result_performance_submission"
    submit: str = "submit"
    fig_logfc: str = "fig_logfc"
    fig_metric: str = "fig_metric"
    fig_cv: str = "fig_CV_violinplot"
    result_perf: str = "result_perf"
    meta_data: str = "meta_data"
    input_df: str = "input_df"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid"
    comments_submission_uuid: str = "comments_submission_uuid"
    check_submission_uuid: str = "check_submission_uuid"
    meta_data_text: str = "comments_for_submission"
    check_submission: str = "heck_submission"
    button_submission_uuid: str = "button_submission_uuid"
    df_head: str = "df_head"
    placeholder_fig_compare: str = "placeholder_fig_compare"
    placeholder_table: str = "placeholder_table"
    placeholder_slider: str = "placeholder_slider"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True

    additional_params_json: str = "../webinterface/configuration/dda_quant.json"

    description_module_md: str = "pages/markdown_files/DDA_Quant/introduction.md"
    description_files_md: str = "pages/markdown_files/DDA_Quant/file_description.md"
    description_input_file_md: str = "pages/markdown_files/DDA_Quant/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/DDA_Quant/slider_description.md"
    description_table_md: str = "pages/markdown_files/DDA_Quant/table_description.md"
    description_results_md: str = "pages/markdown_files/DDA_Quant/result_description.md"
    description_submission_md: str = "pages/markdown_files/DDA_Quant/submit_description.md"

    texts: Type[WebpageTexts] = WebpageTexts
