"""
Variables for the DIA quantification - precursor ions module - lowinput.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


@dataclass
class VariablesDIAQuantLI:
    """
    Variables for the DIA quantification - precursor ions module - low input.
    """

    all_datapoints: str = "all_datapoints_dia_quant_lowinput"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_lowinput"
    input_df_submission: str = "input_df_submission_dia_quant_lowinput"
    result_performance_submission: str = "result_performance_submission_dia_quant_lowinput"
    submit: str = "submit_dia_quant_lowinput"
    fig_logfc: str = "fig_logfc_dia_quant_lowinput"
    fig_metric: str = "fig_metric_dia_quant_lowinput"
    fig_cv: str = "fig_CV_violinplot_dia_quant_lowinput"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_lowinput"
    fig_prefix: str = "fig_dia_quant_lowinput_"
    result_perf: str = "result_perf_dia_quant_lowinput"
    meta_data: str = "meta_data_dia_quant_lowinput"
    input_df: str = "input_df_dia_quant_lowinput"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_lowinput"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_lowinput"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_lowinput"
    meta_data_text: str = "comments_for_submission_dia_quant_lowinput"
    check_submission: str = "heck_submission_dia_quant_lowinput"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_lowinput"
    df_head: str = "df_head_dia_quant_lowinput"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_lowinput"
    placeholder_table: str = "placeholder_table_dia_quant_lowinput"
    placeholder_slider: str = "placeholder_slider_dia_quant_lowinput"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_lowinput"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 3
    max_nr_observed: int = 6
    alpha_warning: bool = True
    beta_warning: bool = False
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_lowinput.git"

    # Sidebar metadata
    sidebar_label: str = "Quant LFQ DIA ion Low Input"
    documentation_description: str = "Benchmark identification and quantification workflows for low-input and single-cell proteomics using DIA acquisitions."
    sidebar_path: str = "/Quant_LFQ_DIA_ion_lowinput"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: [
            "DIA",
            "quantification",
            "low_input",
            "Astral",
            "precursor",
            "ion",
            "LFQ",
            "single-cell",
        ]
    )
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_lowinput"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_lowinput"
    selectbox_id_indepth_uuid: str = "selectbox_id_indepth_dia_quant_lowinput"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_lowinput"
    slider_id_uuid: str = "slider_id_dia_quant_lowinput"
    slider_id_indepth_uuid: str = "slider_id_indepth_dia_quant_lowinput"
    colorblind_mode_selector_uuid: str = "colorblind_mode_selector_dia_quant_lowinput"
    colorblind_mode_selector_submitted_uuid: str = "colorblind_mode_selector_submitted_dia_quant_lowinput"
    colorblind_mode_selector_indepth_uuid: str = "colorblind_mode_selector_indepth_dia_quant_lowinput"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_lowinput"
    table_id_uuid: str = "table_id_dia_quant_lowinput"
    table_new_results_uuid: str = "table_new_results_uuid_dia_quant_lowinput"
    result_plot_uuid: str = "result_figure_uuid_dia_quant_lowinput"
    result_submitted_plot_uuid: str = "result_submitted_figure_uuid_dia_quant_lowinput"
    metric_selector_uuid: str = "metric_selector_uuid_dia_quant_lowinput"
    metric_selector_submitted_uuid: str = "metric_selector_submitted_uuid_dia_quant_lowinput"
    metric_selector_indepth_uuid: str = "metric_selector_indepth_uuid_dia_quant_lowinput"
    metric_calc_approach_selector_submitted_uuid: str = (
        "metric_calc_approach_selector_submitted_uuid_dia_quant_lowinput"
    )
    metric_calc_approach_selector_uuid: str = "metric_calc_approach_selector_uuid_dia_quant_lowinput"
    metric_calc_approach_selector_indepth_uuid: str = "metric_calc_approach_selector_indepth_uuid_dia_quant_lowinput"

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

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/lowinput/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_lowinput"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_lowinput"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_lowinput"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_lowinput"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_lowinput"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/lowinput"

    texts: Type[WebpageTexts] = WebpageTexts
    doc_url: str = (
        "https://proteobench.readthedocs.io/en/latest/available-modules/active-modules/9-quant-lfq-ion-dia-lowinput/"
    )

    title: str = "DIA Precursor quantification - Low Input"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_lowinput_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dia_lowinput_quant_lowinput"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_lowinput_quant_lowinput"
