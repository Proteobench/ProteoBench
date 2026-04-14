# /// script
# dependencies = ["matplotlib", "pandas", "tqdm", "wget"]
# ///

import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    # packages added via marimo's package management: matplotlib pandas wget tqdm !uv pip install matplotlib pandas wget tqdm
    return


@app.cell
def _():
    import warnings
    warnings.filterwarnings('ignore')
    warnings.simplefilter('ignore')

    from tqdm import tqdm

    import os
    from proteobench.utils.quant_datapoint import (
        filter_df_numquant_median_abs_epsilon,
        filter_df_numquant_nr_prec,
    )
    from proteobench.modules.template.parse_settings import INPUT_FORMATS, LOCAL_DEVELOPMENT, TEMPLATE_RESULTS_PATH
    from proteobench.utils.plotting.plot import PlotDataPoint
    from proteobench.modules.dda_quant_ion.module import IonModule

    import pandas as pd
    from matplotlib import pyplot as plt
    from proteobench.io.params.sage import extract_params
    import zipfile

    return (
        IonModule,
        PlotDataPoint,
        extract_params,
        filter_df_numquant_median_abs_epsilon,
        filter_df_numquant_nr_prec,
        os,
        pd,
        tqdm,
        zipfile,
    )


@app.cell
def _(os):
    import wget
    local_file = "sage_results.zip"
    url = "https://figshare.com/ndownloader/files/44571985"
    if not os.path.exists(local_file):
        print("File not found locally. Downloading...")
        f = wget.download(url, local_file)
    else:
        print("File already exists. Skipping download.")
        f = local_file
    return (local_file,)


@app.cell
def _(local_file, os, zipfile):
    extract_to_path = "result_dir"
    if not os.path.exists(extract_to_path) or not os.listdir(extract_to_path):
        if not os.path.exists(extract_to_path):
            os.makedirs(extract_to_path)
        print("Extracting files...")
        with zipfile.ZipFile(local_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to_path)
    else:
        print("Files already extracted. Skipping extraction.")
    return (extract_to_path,)


@app.cell
def _(IonModule, extract_params, extract_to_path, os, pd, tqdm):
    ionmod = IonModule()
    all_datapoints = pd.DataFrame()
    all_comments = []
    for f_1 in tqdm(os.listdir(extract_to_path)):
        lfq_file = os.path.join(os.path.join(extract_to_path, f_1), 'lfq.tsv')
        params = extract_params(os.path.join(os.path.join(extract_to_path, f_1), 'results.json')).__dict__
        params['comments'] = f_1
        all_comments.append(f_1)
        result_performance, all_datapoints, input_df = ionmod.benchmarking(lfq_file, 'Sage', user_input=params, all_datapoints=all_datapoints, default_cutoff_min_prec=3)
    all_datapoints['comments'] = all_comments
    return (all_datapoints,)


@app.cell
def _(
    all_datapoints,
    filter_df_numquant_median_abs_epsilon,
    filter_df_numquant_nr_prec,
):
    min_quant = 6

    all_datapoints["median_abs_epsilon"] = [
        filter_df_numquant_median_abs_epsilon(v, min_quant=min_quant)
        for v in all_datapoints["results"]
    ]

    all_datapoints["nr_prec"] = [
        filter_df_numquant_nr_prec(v, min_quant=min_quant)
        for v in all_datapoints["results"]
    ]
    return


@app.cell
def _(PlotDataPoint, all_datapoints):
    fig_metric = PlotDataPoint.plot_metric(all_datapoints)
    return (fig_metric,)


@app.cell
def _(fig_metric):
    fig_metric.show()
    return


if __name__ == "__main__":
    app.run()
