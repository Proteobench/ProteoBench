from dataclasses import dataclass, field
from typing import List


@dataclass
class VariablesDDAQuant:
    all_datapoints: str = "all_datapoints"
    all_datapoints_submission: str = "all_datapoints_submission"
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
