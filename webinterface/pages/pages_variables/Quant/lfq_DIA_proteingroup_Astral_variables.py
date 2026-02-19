"""
Variables for the DIA quantification module using Astral.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


# TODO: restructure the variable names. Do this for the other pages_variables as well.
@dataclass
class VariablesDIAQuantProteingroupAstral:
    """
    Variables for the DIA quantification module using Astral.
    """

    all_datapoints: str = "all_datapoints_dia_quant_proteingroup_Astral"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_proteingroup_Astral"
    input_df_submission: str = "input_df_submission_dia_quant_proteingroup_Astral"
    result_performance_submission: str = "result_performance_submission_dia_quant_proteingroup_Astral"
    submit: str = "submit_dia_quant_proteingroup_Astral"
    fig_logfc: str = "fig_logfc_dia_quant_proteingroup_Astral"
    fig_metric: str = "fig_metric_dia_quant_proteingroup_Astral"
    fig_cv: str = "fig_CV_violinplot_dia_quant_proteingroup_Astral"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_proteingroup_Astral"
    fig_prefix: str = "fig_dia_quant_proteingroup_Astral_"
    result_perf: str = "result_perf_dia_quant_proteingroup_Astral"
    meta_data: str = "meta_data_dia_quant_proteingroup_Astral"
    input_df: str = "input_df_dia_quant_proteingroup_Astral"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_proteingroup_Astral"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_proteingroup_Astral"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_proteingroup_Astral"
    meta_data_text: str = "comments_for_submission_dia_quant_proteingroup_Astral"
    check_submission: str = "check_submission_dia_quant_proteingroup_Astral"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_proteingroup_Astral"
    df_head: str = "df_head_dia_quant_proteingroup_Astral"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_proteingroup_Astral"
    placeholder_table: str = "placeholder_table_dia_quant_proteingroup_Astral"
    placeholder_slider: str = "placeholder_slider_dia_quant_proteingroup_Astral"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_proteingroup_Astral"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    alpha_warning: bool = True
    beta_warning: bool = False
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_proteingroup_DIA_Astral.git"

    # Sidebar metadata
    sidebar_label: str = "Quant LFQ DIA protein group Astral"
    sidebar_path: str = "/Quant_LFQ_DIA_proteingroup_Astral"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "quantification", "Astral", "orbitrap", "protein groups", "LFQ"]
    )
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_proteingroup_Astral"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_proteingroup_Astral"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_proteingroup_Astral"
    slider_id_uuid: str = "slider_id_dia_quant_proteingroup_Astral"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_proteingroup_Astral"
    table_id_uuid: str = "table_id_dia_quant_proteingroup_Astral"
    table_new_results_uuid: str = "table_new_results_uuid_dia_quant_proteingroup_Astral"
    result_plot_uuid: str = "result_figure_uuid_dia_quant_proteingroup_Astral"
    result_submitted_plot_uuid: str = "result_submitted_figure_uuid_dia_quant_proteingroup_Astral"
    metric_selector_uuid: str = "metric_selector_uuid_dia_quant_proteingroup_Astral"
    metric_selector_submitted_uuid: str = "metric_selector_submitted_uuid_dia_quant_proteingroup_Astral"
    metric_calc_approach_selector_submitted_uuid: str = "metric_calc_approach_selector_submitted_uuid_dia_quant_proteingroup_Astral"
    metric_calc_approach_selector_uuid: str = "metric_calc_approach_selector_uuid_dia_quant_proteingroup_Astral"

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

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/proteingroup/Astral/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_proteingroup_Astral"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_proteingroup_Astral"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_proteingroup_Astral"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_proteingroup_Astral"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_proteingroup_Astral"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/proteingroup/Astral"

    texts: Type[WebpageTexts] = WebpageTexts

    doc_url: str = (
        "https://proteobench.readthedocs.io/en/latest/available-modules/active-modules/11-quant-lfq-proteingroup-dia-Astral_2Th/"
    )

    title: str = "DIA Protein group quantification - Astral 2 Th"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_proteingroup.json"
    prefix_params: str = "lfq_proteingroup_dia_Astral_quant_"
    params_json_dict: str = "params_json_dict_lfq_proteingroup_dia_Astral_quant"
    params_file_dict: str = "params_file_dict_lfq_proteingroup_dia_Astral_quant"
