"""
Variables for the DIA quantification module using timsTOF on low-input.
"""

from dataclasses import dataclass, field
from typing import List, Type

from pages.texts.generic_texts import WebpageTexts


# TODO: restructure the variable names. Do this for the other pages_variables as well.
@dataclass
class VariablesDIAQuanttimsTOFLowinput:
    """
    Variables for the DIA quantification module using timsTOF on low-input.
    """

    all_datapoints: str = "all_datapoints_dia_quant_timsTOF_lowinput"
    all_datapoints_submission: str = "all_datapoints_submission_dia_quant_timsTOF_lowinput"
    input_df_submission: str = "input_df_submission_dia_quant_timsTOF_lowinput"
    result_performance_submission: str = "result_performance_submission_dia_quant_timsTOF_lowinput"
    submit: str = "submit_dia_quant_timsTOF_lowinput"
    fig_logfc: str = "fig_logfc_dia_quant_timsTOF_lowinput"
    fig_metric: str = "fig_metric_dia_quant_timsTOF_lowinput"
    fig_cv: str = "fig_CV_violinplot_dia_quant_timsTOF_lowinput"
    fig_ma_plot: str = "fig_ma_plot_dia_quant_timsTOF_lowinput"
    fig_prefix: str = "fig_dia_quant_timsTOF_lowinput_"
    result_perf: str = "result_perf_dia_quant_timsTOF_lowinput"
    meta_data: str = "meta_data_dia_quant_timsTOF_lowinput"
    input_df: str = "input_df_dia_quant_timsTOF_lowinput"
    meta_file_uploader_uuid: str = "meta_file_uploader_uuid_dia_quant_timsTOF_lowinput"
    comments_submission_uuid: str = "comments_submission_uuid_dia_quant_timsTOF_lowinput"
    check_submission_uuid: str = "check_submission_uuid_dia_quant_timsTOF_lowinput"
    meta_data_text: str = "comments_for_submission_dia_quant_timsTOF_lowinput"
    check_submission: str = "check_submission_dia_quant_timsTOF_lowinput"
    button_submission_uuid: str = "button_submission_uuid_dia_quant_timsTOF_lowinput"
    df_head: str = "df_head_dia_quant_timsTOF_lowinput"
    placeholder_fig_compare: str = "placeholder_fig_compare_dia_quant_diPASEF"
    placeholder_table: str = "placeholder_table_dia_quant_timsTOF_lowinput"
    placeholder_slider: str = "placeholder_slider_dia_quant_timsTOF_lowinput"
    placeholder_downloads_container: str = "placeholder_downloads_container_dia_quant_timsTOF_lowinput"
    highlight_list: List[str] = field(default_factory=list)
    first_new_plot: bool = True
    default_val_slider: int = 6
    max_nr_observed: int = 12
    alpha_warning: bool = True
    beta_warning: bool = False
    archived_warning: bool = False
    github_link_pr: str = "github.com/Proteobot/Results_quant_ion_DIA_timsTOF_lowinput.git"

    # Sidebar metadata
    sidebar_label: str = "Quant LFQ DIA ion timsTOF (low-input)"
    homepage_title: str = "LFQ Quantification on a timsTOF Ultra 2 on low-input (200 pg)"
    graphical_abstract: str = "Graphical_abstract_Quant_timsTOF.png" # TODO change!
    documentation_description: str = "Benchmark ion-level label-free quantification accuracy of DIA-PASEF workflows using a low-input (200pg) multi-species (HYE) sample on a timsTOF instrument."
    sidebar_path: str = "/Quant_LFQ_DIA_ion_timsTOF_lowinput"
    sidebar_category: str = "DIA"
    keywords: List[str] = field(
        default_factory=lambda: ["DIA", "quantification", "timsTOF", "precursor", "ion", "LFQ", "PASEF", "single-cell", "low-input"]
    )
    selectbox_id_submitted_uuid: str = "selectbox_id_submitted_dia_quant_timsTOF_lowinput"
    selectbox_id_uuid: str = "selectbox_id_dia_quant_timsTOF_lowinput"
    selectbox_id_indepth_uuid: str = "selectbox_id_indepth_dia_quant_timsTOF_lowinput"
    colorblind_mode_selector_uuid: str = "colorblind_mode_selector_dia_quant_timsTOF_lowinput"
    colorblind_mode_selector_submitted_uuid: str = "colorblind_mode_selector_submitted_dia_quant_timsTOF_lowinput"
    colorblind_mode_selector_indepth_uuid: str = "colorblind_mode_selector_indepth_dia_quant_timsTOF_lowinput"
    slider_id_submitted_uuid: str = "slider_id_submitted_dia_quant_timsTOF_lowinput"
    slider_id_uuid: str = "slider_id_dia_quant_timsTOF_lowinput"
    slider_id_indepth_uuid: str = "slider_id_indepth_dia_quant_timsTOF_lowinput"
    download_selector_id_uuid: str = "download_selector_id_dia_quant_timsTOF_lowinput"
    table_id_uuid: str = "table_id_dia_quant_timsTOF_lowinput"
    table_new_results_uuid: str = "table_new_results_uuid_dia_quant_timsTOF_lowinput"
    result_plot_uuid: str = "result_figure_uuid_dia_quant_timsTOF_lowinput"
    result_submitted_plot_uuid: str = "result_submitted_figure_uuid_dia_quant_timsTOF_lowinput"
    metric_selector_uuid: str = "metric_selector_uuid_dia_quant_timsTOF_lowinput"
    metric_selector_submitted_uuid: str = "metric_selector_submitted_uuid_dia_quant_timsTOF_lowinput"
    metric_selector_indepth_uuid: str = "metric_selector_indepth_uuid_dia_quant_timsTOF_lowinput"
    metric_calc_approach_selector_submitted_uuid: str = (
        "metric_calc_approach_selector_submitted_uuid_dia_quant_timsTOF_lowinput"
    )
    metric_calc_approach_selector_uuid: str = "metric_calc_approach_selector_uuid_dia_quant_timsTOF_lowinput"
    metric_calc_approach_selector_indepth_uuid: str = "metric_calc_approach_selector_indepth_uuid_dia_quant_timsTOF_lowinput"

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

    description_module_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/introduction.md"
    description_files_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/file_description.md"
    description_input_file_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/input_file_description.md"
    description_slider_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/slider_description.md"
    description_table_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/table_description.md"
    description_results_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/result_description.md"
    description_submission_md: str = "pages/markdown_files/Quant/lfq/DIA/ion/timsTOF_lowinput/submit_description.md"

    all_datapoints_submitted: str = "all_datapoints_submitted_dia_quant_timsTOF_lowinput"
    placeholder_table_submitted: str = "placeholder_table_submitted_dia_quant_timsTOF_lowinput"
    placeholder_slider_submitted: str = "placeholder_slider_submitted_dia_quant_timsTOF_lowinput"
    highlight_list_submitted: List[str] = field(default_factory=list)

    placeholder_dataset_selection_container: str = "placeholder_dataset_selection_container_dia_quant_timsTOF_lowinput"
    dataset_selector_id_uuid: str = "dataset_selector_id_dia_quant_timsTOF_lowinput"

    parse_settings_dir: str = "../proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/timsTOF_lowinput"

    texts: Type[WebpageTexts] = WebpageTexts

    doc_url: str = "https://proteobench.readthedocs.io/en/latest/modules/dia/dia-ion-timstof-lowinput/"
    raw_data_url: str = "https://proteobench.cubimed.rub.de/raws/DIA-timstof-lowinput/all_data_LFQ_Quant_DIA_timsTOF_lowinput.tar.gz"

    title: str = "DIA Precursor quantification - timsTOF (low-input)"
    y_axis_title: str = "Total number of precursor ions quantified in the selected number of raw files"

    additional_params_json: str = "../proteobench/io/params/json/Quant/quant_lfq_DIA_ion.json"
    prefix_params: str = "lfq_ion_dia_timsTOF_lowinput_quant_"
    params_json_dict: str = "params_json_dict_lfq_ion_dda_timsTOF_lowinput_quant"
    params_file_dict: str = "params_file_dict_lfq_ion_dia_timsTOF_lowinput_quant"
