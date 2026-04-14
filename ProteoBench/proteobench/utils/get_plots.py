import os
from collections import defaultdict

import pandas as pd
import plotly.express as px

from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.quant_lfq_ion_DDA import DDAQuantIonModule
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModule
from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import (
    DIAQuantIonModulediaPASEF,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_singlecell import (
    DIAQuantIonModulediaSC,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import (
    DDAQuantPeptidoformModule,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DIA import (
    DIAQuantPeptidoformModule,
)
from proteobench.plotting import plot_quant

# Dictionary mapping module name strings to their classes
MODULE_CLASSES = {
    "DDAQuantIonModule": DDAQuantIonModule,
    "DIAQuantIonModule": DIAQuantIonModule,
    "DIAQuantIonModuleAstral": DIAQuantIonModuleAstral,
    "DIAQuantIonModulediaPASEF": DIAQuantIonModulediaPASEF,
    "DIAQuantIonModulediaSC": DIAQuantIonModulediaSC,
    "DDAQuantPeptidoformModule": DDAQuantPeptidoformModule,
    "DIAQuantPeptidoformModule": DIAQuantPeptidoformModule,
}


def make_indepth_plots(hash_vis_dirs, intermediate_hash, filtered_df, module_name="DDAQuantIonModule"):
    """
    Parameters
    ----------
    hash_vis_dirs : dict
        Dictionary mapping hash strings to Path objects.
    intermediate_hash : str
        The hash key to identify the visualization directory.
    filtered_df : pd.DataFrame
        Concatenated JSON data as a DataFrame.
    module_name : str, optional
        The name of the quantification module class to instantiate, by default "DDAQuantIonModule".

    Returns
    -------
    tuple
        Two matplotlib figures, parameters file path, and results DataFrame.
    """

    location = hash_vis_dirs[intermediate_hash]
    software_name = filtered_df["software_name"]

    all_files = os.listdir(location)

    matching_file = os.path.join(
        location,
        [f for f in all_files if f.startswith("input_file") and os.path.isfile(os.path.join(location, f))][0],
    )
    matching_file_params = os.path.join(
        location,
        [f for f in all_files if f.startswith("param") and os.path.isfile(os.path.join(location, f))][0],
    )

    user_config = defaultdict(lambda: "")

    # Dynamically instantiate the module class
    if module_name not in MODULE_CLASSES:
        raise ValueError(f"Module {module_name} not recognized. Available modules: {list(MODULE_CLASSES.keys())}")

    module_class = MODULE_CLASSES[module_name]
    module_obj = module_class(token="")

    results_df = module_obj.obtain_all_data_points(all_datapoints=None)

    results_performance, all_datapoints, result_df = module_obj.benchmarking(
        matching_file, software_name, user_input=user_config, all_datapoints=[]
    )

    fig1 = plot_quant.PlotDataPoint.plot_CV_violinplot(results_performance)

    parse_settings = ParseSettingsBuilder(
        parse_settings_dir="../../proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/",
        module_id="quant_lfq_DDA_ion",
    ).build_parser(software_name)

    fig2 = plot_quant.PlotDataPoint.plot_fold_change_histogram(
        results_performance, parse_settings.species_expected_ratio()
    )

    return fig1, fig2, matching_file_params, result_df


def get_plot_dict(hash_vis_dirs, intermediate_hash, df, module_name="DDAQuantIonModule"):
    performance_dict = {}

    for idx, row in df.iterrows():
        location = hash_vis_dirs[row["intermediate_hash"]]
        software_name = row["software_name"]

        # List all files in the directory
        all_files = os.listdir(location)
        if len(all_files) == 0:
            print(f"Directory {location} is empty.")
            continue

        # Filter for files that start with 'input_file' and ignore their extensions
        matching_file = os.path.join(
            location,
            [f for f in all_files if f.startswith("input_file") and os.path.isfile(os.path.join(location, f))][0],
        )
        matching_file_params = os.path.join(
            location, [f for f in all_files if f.startswith("param") and os.path.isfile(os.path.join(location, f))][0]
        )

        user_config = defaultdict(lambda: "")

        module_obj = DDAQuantIonModule(token="")
        results_df = module_obj.obtain_all_data_points(all_datapoints=None)

        input_df = load_input_file(matching_file, software_name)

        parse_settings = ParseSettingsBuilder(
            parse_settings_dir=MODULE_SETTINGS_DIRS["quant_lfq_DDA_ion"], module_id="quant_lfq_DDA_ion"
        ).build_parser(software_name)
        standard_format, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)
        runs = replicate_to_raw["A"]
        runs.extend(replicate_to_raw["B"])

        results_performance, all_datapoints, result_df = module_obj.benchmarking(
            matching_file, software_name, user_input=user_config, all_datapoints=[]
        )

        results_performance_runs = results_performance.loc[:, runs]
        total_missing = results_performance.loc[:, runs].isna().sum().sum()
        total_max = results_performance_runs.shape[0] * results_performance_runs.shape[1]
        total_peptide_ions = results_performance_runs.shape[0]
        total_runs = results_performance_runs.shape[1]

        performance_dict[row["id"]] = {
            "total_missing": total_missing,
            "total_max": total_max,
            "total_peptide_ions": total_peptide_ions,
            "total_runs": total_runs,
            "total_missing_ratio": total_missing / total_max,
            "total_missing_percentage": (total_missing / total_max) * 100,
        }

    return performance_dict


def get_missing_percentage_plot(performance_df):
    performance_df["IDX"] = performance_df.index
    # Creating an interactive scatter plot using Plotly
    fig = px.scatter(
        performance_df,
        x="total_peptide_ions",
        y="total_missing_percentage",
        hover_name="IDX",
        labels={"total_missing": "Total Missing", "total_missing_percentage": "Total Missing Percentage"},
        title="Interactive Scatter Plot of Missing Data",
    )

    fig.update_layout(hovermode="closest")
    fig.show()
