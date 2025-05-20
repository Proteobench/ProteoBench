import os
from collections import defaultdict
from proteobench.modules.quant.quant_lfq_ion_DDA import DDAQuantIonModule
from proteobench.plotting import plot_quant
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder


def make_indepth_plots(hash_vis_dirs, intermediate_hash, filtered_df):
    """
    hash_vis_dirs dict 
        dict[hash] = Path
    intermediate_hash str
        hash
    filtered_df pd.df
        concatenated jsons
    """
    location = hash_vis_dirs[intermediate_hash]
    software_name = filtered_df["software_name"].iloc[0]

    # List all files in the directory
    all_files = os.listdir(location)

    # Filter for files that start with 'input_file' and ignore their extensions
    matching_file = os.path.join(location,[f for f in all_files if f.startswith('input_file') and os.path.isfile(os.path.join(location, f))][0])
    matching_file_params = os.path.join(location,[f for f in all_files if f.startswith('param') and os.path.isfile(os.path.join(location, f))][0])

    user_config = defaultdict(lambda: "")

    module_obj = DDAQuantIonModule(token="")
    results_df = module_obj.obtain_all_data_points(all_datapoints=None)

    results_performance, all_datapoints, result_df = module_obj.benchmarking(
        matching_file, software_name, user_input=user_config, all_datapoints=[]
    )

    fig1 = plot_quant.PlotDataPoint.plot_CV_violinplot(results_performance)

    parse_settings = ParseSettingsBuilder(
                    parse_settings_dir="../../proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/", module_id="quant_lfq_DDA_ion"
                ).build_parser(software_name)

    fig2 = plot_quant.PlotDataPoint.plot_fold_change_histogram(results_performance,parse_settings.species_expected_ratio())

    return fig1, fig2, matching_file_params, result_df