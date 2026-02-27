"""
Variables for the DIA quantification module using ZenoTOF.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


# TODO: restructure the variable names. Do this for the other pages_variables as well.
@dataclass
class VariablesDIAQuantZenoTOF:
    """
    Variables for the DIA quantification module using ZenoTOF.
    """

    all_datapoints: str = "all_datapoints_dia_quant_ZenoTOF"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_ZenoTOF"
    input_df_submission: str = "input_df_submission_dia_quant_ZenoTOF"
    result_performance_submission: str = "result_performance_submission_dia_quant_ZenoTOF"
    submit: str = "submit_dia_quant_ZenoTOF"
    fig_logfc: str = "fig_logfc_dia_quant_ZenoTOF"
    fig_metric: str = "fig_metric_dia_quant_ZenoTOF"
    fig_cv: str = "fig_CV_violinplot_dia_quant_ZenoTOF"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_ZenoTOF"
    result_perf: str = "result_perf_dia_quant_ZenoTOF"
    meta_data: str = "meta_data_dia_quant_ZenoTOF"
    input_df: str = "input_df_dia_quant_ZenoTOF"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_ZenoTOF"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_ZenoTOF"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_ZenoTOF"
    meta_data_text: str = "comments_for_submission_dia_quant_ZenoTOF"
    check_submission: str = "check_submission_dia_quant_ZenoTOF"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_ZenoTOF"
    df_head: str = "df_head_dia_quant_ZenoTOF"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_diPASEF"
    placeholder_table: str = "placeholder_table_dia_quant_ZenoTOF"
    placeholder_slider: str = "placeholder_slider_dia_quant_ZenoTOF"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_ZenoTOF"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    alpha_warning: bool = False
    beta_warning: bool = True
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_ZenoTOF.git"

    # Sidebar metadata
    sidebar_label: str = "Quant LFQ DIA ion ZenoTOF"
    sidebar_path: str = "/Quant_LFQ_DIA_ion_ZenoTOF"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "quantification", "ZenoTOF", "SCIEX", "precursor", "ion", "LFQ", "TOF"]
    )
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_ZenoTOF"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_ZenoTOF"
    colorblind_mode_selector_uuid: str = "colorblind_mode_selector_dia_quant_ZenoTOF"
    colorblind_mode_selector_submitted_uuid: str = "colorblind_mode_selector_submitted_dia_quant_ZenoTOF"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_ZenoTOF"
    slider_id_uuid: str = "slider_id_dia_quant_ZenoTOF"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_ZenoTOF"
    table_id_uuid: str = "table_id_dia_quant_ZenoTOF"
    table_new_results_uuid: str = "table_new_results_uuid_dia_quant_ZenoTOF"
    result_plot_uuid: str = "result_figure_uuid_dia_quant_ZenoTOF"
    result_submitted_plot_uuid: str = "result_submitted_figure_uuid_dia_quant_ZenoTOF"
    metric_selector_uuid: str = "metric_selector_uuid_dia_quant_ZenoTOF"
    metric_selector_submitted_uuid: str = "metric_selector_submitted_uuid_dia_quant_ZenoTOF"
    metric_calc_approach_selector_submitted_uuid: str = "metric_calc_approach_selector_submitted_uuid_dia_quant_ZenoTOF"
    metric_calc_approach_selector_uuid: str = "metric_calc_approach_selector_uuid_dia_quant_ZenoTOF"

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

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/ZenoTOF/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_ZenoTOF"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_ZenoTOF"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_ZenoTOF"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_ZenoTOF"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_ZenoTOF"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/ZenoTOF"

    texts: Type[WebpageTexts] = WebpageTexts

    doc_url: str = (
        "https://proteobench.readthedocs.io/en/latest/available-modules/active-modules/10-quant-lfq-ion-dia-ZenoTOF/"
    )

    title: str = "DIA Precursor ion quantification - ZenoTOF"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_ZenoTOF_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dia_ZenoTOF_quant"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_ZenoTOF_quant"
