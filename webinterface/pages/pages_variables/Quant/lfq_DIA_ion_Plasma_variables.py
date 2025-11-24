"""
Variables for the DIA quantification module using Plasma.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


# TODO: restructure the variable names. Do this for the other pages_variables as well.
@dataclass
class VariablesDIAQuantPlasma:
    """
    Variables for the DIA quantification module using Plasma.
    """

    all_datapoints: str = "all_datapoints_dia_quant_Plasma"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_Plasma"
    input_df_submission: str = "input_df_submission_dia_quant_Plasma"
    result_performance_submission: str = "result_performance_submission_dia_quant_Plasma"
    submit: str = "submit_dia_quant_Plasma"
    fig_logfc: str = "fig_logfc_dia_quant_Plasma"
    fig_metric: str = "fig_metric_dia_quant_Plasma"
    fig_cv: str = "fig_CV_violinplot_dia_quant_Plasma"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_Plasma"
    fig_prefix: str = "fig_dia_quant_Plasma_"
    result_perf: str = "result_perf_dia_quant_Plasma"
    meta_data: str = "meta_data_dia_quant_Plasma"
    input_df: str = "input_df_dia_quant_Plasma"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_Plasma"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_Plasma"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_Plasma"
    meta_data_text: str = "comments_for_submission_dia_quant_Plasma"
    check_submission: str = "heck_submission_dia_quant_Plasma"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_Plasma"
    df_head: str = "df_head_dia_quant_Plasma"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_diPASEF"
    placeholder_table: str = "placeholder_table_dia_quant_Plasma"
    placeholder_slider: str = "placeholder_slider_dia_quant_Plasma"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_Plasma"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    beta_warning: bool = True
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_Plasma.git"
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_Plasma"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_Plasma"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_Plasma"
    slider_id_uuid: str = "slider_id_dia_quant_Plasma"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_Plasma"
    table_id_uuid: str = "table_id_dia_quant_Plasma"
    table_new_results_uuid: str = "table_new_results_uuid_dia_quant_Plasma"
    result_plot_uuid: str = "result_figure_uuid_dia_quant_Plasma"
    result_submitted_plot_uuid: str = "result_submitted_figure_uuid_dia_quant_Plasma"
    metric_selector_uuid: str = "metric_selector_uuid_dia_quant_Plasma"
    metric_selector_submitted_uuid: str = "metric_selector_submitted_uuid_dia_quant_Plasma"
    metric_calc_approach_selector_submitted_uuid: str = "metric_calc_approach_selector_submitted_uuid_dia_quant_Plasma"
    metric_calc_approach_selector_uuid: str = "metric_calc_approach_selector_uuid_dia_quant_Plasma"
    metric_plot_labels: List[str] = field(
        default_factory=lambda: [
            "None",
            "enable_match_between_runs",
            "max_mods",
            "enzyme",
            "ident_fdr_psm",
            "ident_fdr_peptide",
            "allowed_miscleavages",
            "quantification_method",
        ]
    )

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/Plasma/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_Plasma"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_Plasma"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_Plasma"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_Plasma"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_Plasma"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/Plasma"

    texts: Type[WebpageTexts] = WebpageTexts

    doc_url: str = (
        "https://proteobench.readthedocs.io/en/latest/available-modules/active-modules/5-quant-lfq-ion-dia-Plasma/"
    )

    title: str = "DIA Precursor quantification - Plasma"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_Plasma_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_Plasma_quant"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_Plasma_quant"
