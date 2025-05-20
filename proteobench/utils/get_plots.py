import os
from collections import defaultdict

from proteobench.modules.quant.quant_lfq_ion_DDA import DDAQuantIonModule
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModule
from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import DIAQuantIonModulediaPASEF
from proteobench.modules.quant.quant_lfq_ion_DIA_singlecell import DIAQuantIonModulediaSC
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import DDAQuantPeptidoformModule
from proteobench.modules.quant.quant_lfq_peptidoform_DIA import DIAQuantPeptidoformModule

from proteobench.plotting import plot_quant
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder


# Dictionary mapping module name strings to their classes
MODULE_CLASSES = {
    "DDAQuantIonModule": DDAQuantIonModule,
    "DIAQuantIonModule" : DIAQuantIonModule,
    "DIAQuantIonModuleAstral" : DIAQuantIonModuleAstral,
    "DIAQuantIonModulediaPASEF" : DIAQuantIonModulediaPASEF,
    "DIAQuantIonModulediaSC" : DIAQuantIonModulediaSC,
    "DDAQuantPeptidoformModule" : DDAQuantPeptidoformModule,
    "DIAQuantPeptidoformModule" : DIAQuantPeptidoformModule,
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

    fig2 = plot_quant.PlotDataPoint.plot_fold_change_histogram(results_performance, parse_settings.species_expected_ratio())

    return fig1, fig2, matching_file_params, result_df
