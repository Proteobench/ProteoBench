# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "plotly",
#     "requests",
#     "beautifulsoup4",
#     "tqdm",
#     "proteobench",
# ]
# ///

import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
    # Benchmark Metrics Analysis for ProteoBench

    This notebook analyzes **all benchmark metrics** across different proteomics software tools:

    **ROC-AUC Metrics:**
    - **ROC-AUC**: Measures separation of changed vs unchanged species using `abs(log2_FC)`
    - **Directional ROC-AUC**: Uses direction-aware scoring (YEAST positive, ECOLI negative)

    **Epsilon Metrics** (deviation from expected ratio):
    - **Median/Mean Abs Epsilon (Global)**: Overall accuracy across all species
    - **Median/Mean Abs Epsilon (Equal Species)**: Weighted equally per species

    **CV Metrics** (coefficient of variation):
    - **CV Median/Q75/Q90/Q95**: Reproducibility at different quantiles
    """
    )
    return


@app.cell
def _():
    import pandas as pd
    import os
    from pathlib import Path
    from collections import defaultdict
    import plotly.express as px
    import plotly.io as pio

    pio.templates.default = "plotly"

    # Get the directory where this notebook lives
    NOTEBOOK_DIR = Path(__file__).parent
    return NOTEBOOK_DIR, defaultdict, os, pd, px


@app.cell
def _():
    from proteobench.utils.server_io import get_merged_json, get_raw_data
    from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive
    from proteobench.datapoint.quant_datapoint import QuantDatapoint

    return (
        DDAQuantIonModuleQExactive,
        QuantDatapoint,
        get_merged_json,
        get_raw_data,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 1. Load Benchmark Results

    Fetches all benchmark metadata from the GitHub results repository.
    """
    )
    return


@app.cell
def _(get_merged_json, mo):
    df_all = get_merged_json(
        repo_url="https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip"
    )
    mo.md(f"**Loaded {len(df_all)} benchmark results from GitHub**")
    return (df_all,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 2. Download Raw Datasets

    Downloads missing raw datasets from the server and tracks available files locally.
    """
    )
    return


@app.cell
def _(NOTEBOOK_DIR, df_all, get_raw_data, os):
    OUTPUT_DIR = NOTEBOOK_DIR.resolve() / "temp_results"

    def get_datasets_to_download(df, output_directory):
        """Check which datasets need to be downloaded."""
        hash_list = df["intermediate_hash"].tolist()
        existing_hashes = []
        hash_vis_dir = {}

        output_dir_str = str(output_directory)
        if os.path.exists(output_dir_str):
            for hash_dir in os.listdir(output_dir_str):
                if hash_dir in hash_list:
                    existing_hashes.append(hash_dir)
                    hash_vis_dir[hash_dir] = os.path.join(output_dir_str, hash_dir)

        if existing_hashes:
            df_to_download = df[~df["intermediate_hash"].isin(existing_hashes)]
            return df_to_download, hash_vis_dir
        else:
            return df, hash_vis_dir

    df_to_download, hash_vis_dirs = get_datasets_to_download(df_all, OUTPUT_DIR)

    # Download missing datasets
    if len(df_to_download) > 0:
        hash_vis_dirs_new = get_raw_data(
            df_to_download, base_url="https://proteobench.cubimed.rub.de/datasets/", output_directory=str(OUTPUT_DIR)
        )
        hash_vis_dirs.update(hash_vis_dirs_new)

    # Filter to only available datasets
    df_available = df_all[df_all["intermediate_hash"].isin(hash_vis_dirs)]
    print(f"Available datasets: {len(df_available)}")
    print(f"Hash dirs found: {len(hash_vis_dirs)}")
    return df_available, hash_vis_dirs


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 3. Select Software Tools

    Choose which software tools to include in the analysis.
    """
    )
    return


@app.cell
def _(df_available, mo):
    available_software = sorted(df_available["software_name"].unique().tolist())

    # Default to all available software
    default_selection = available_software

    software_selector = mo.ui.multiselect(
        options=available_software,
        value=default_selection,
        label="Select software tools to analyze",
    )
    software_selector
    return (software_selector,)


@app.cell
def _(mo):
    mo.md(
        r"""
    Set the minimum number of samples a precursor must be quantified in.
    """
    )
    return


@app.cell
def _(mo):
    min_precursor_slider = mo.ui.slider(
        start=1,
        stop=6,
        step=1,
        value=3,
        label="Minimum precursor quantifications (# samples)",
    )
    min_precursor_slider
    return (min_precursor_slider,)


@app.cell
def _(df_available, mo, software_selector):
    selected_software = software_selector.value
    df_selected = df_available[df_available["software_name"].isin(selected_software)]
    mo.md(f"**Selected {len(df_selected)} datasets from {len(selected_software)} software tools**")
    return (df_selected,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 4. Compute All Benchmark Metrics

    Recomputes all benchmark metrics (ROC-AUC, epsilon, CV) for each selected dataset.
    """
    )
    return


@app.cell
def _(
    DDAQuantIonModuleQExactive,
    QuantDatapoint,
    defaultdict,
    df_selected,
    hash_vis_dirs,
    min_precursor_slider,
    mo,
    os,
    pd,
):
    metrics_results = {}
    errors = []
    min_prec = min_precursor_slider.value

    with mo.status.spinner(title="Computing benchmark metrics..."):
        for _, row in df_selected.iterrows():
            location = hash_vis_dirs.get(row["intermediate_hash"])
            if not location:
                errors.append(f"{row['id']}: No location found")
                continue

            software_name = row["software_name"]
            all_files = os.listdir(location)

            if len(all_files) == 0:
                errors.append(f"{row['id']}: Empty directory")
                continue

            # Find input file
            matching_files = [
                f for f in all_files if f.startswith("input_file") and os.path.isfile(os.path.join(location, f))
            ]
            if not matching_files:
                errors.append(f"{row['id']}: No input file found")
                continue

            matching_file = os.path.join(location, matching_files[0])
            user_config = defaultdict(lambda: "")
            module_obj = DDAQuantIonModuleQExactive(token="")

            try:
                # benchmarking() returns (results_performance, all_datapoints, result_df)
                # results_performance contains the data needed for metrics
                results_performance, _, _ = module_obj.benchmarking(
                    matching_file, software_name, user_input=user_config, all_datapoints=[]
                )

                # Compute all metrics using QuantDatapoint.get_metrics()
                metrics = QuantDatapoint.get_metrics(results_performance, min_nr_observed=min_prec)
                m = metrics[min_prec]

                metrics_results[row["id"]] = {
                    "software_name": software_name,
                    "dataset_id": row["id"],
                    "n_precursors": m["nr_prec"],
                    # Per-species precursor counts (dynamically extracted)
                    "n_precursors_HUMAN": m.get("nr_prec_HUMAN", 0),
                    "n_precursors_YEAST": m.get("nr_prec_YEAST", 0),
                    "n_precursors_ECOLI": m.get("nr_prec_ECOLI", 0),
                    # ROC-AUC metrics
                    "roc_auc": m["roc_auc"],
                    "roc_auc_directional": m["roc_auc_directional"],
                    # Epsilon metrics
                    "median_abs_epsilon_global": m["median_abs_epsilon_global"],
                    "mean_abs_epsilon_global": m["mean_abs_epsilon_global"],
                    "variance_epsilon_global": m["variance_epsilon_global"],
                    "median_abs_epsilon_eq_species": m["median_abs_epsilon_eq_species"],
                    "mean_abs_epsilon_eq_species": m["mean_abs_epsilon_eq_species"],
                    # CV metrics
                    "CV_median": m["CV_median"],
                    "CV_q75": m["CV_q75"],
                    "CV_q90": m["CV_q90"],
                    "CV_q95": m["CV_q95"],
                }

            except KeyError as e:
                # Re-raise KeyError - these are programming errors that should crash loudly
                raise KeyError(f"Missing metric key {e} for {row['id']}. Check get_metrics() implementation.") from e
            except (FileNotFoundError, IOError) as e:
                # Expected errors - file/IO issues can be skipped
                errors.append(f"{row['id']}: {str(e)[:80]}")
                continue
            except Exception as e:
                # Other unexpected errors - log but continue to help diagnose
                errors.append(f"{row['id']}: {type(e).__name__}: {str(e)[:60]}")
                continue

    metrics_df = pd.DataFrame(metrics_results).T

    if len(metrics_df) == 0:
        status_msg = mo.md(f"**No data processed.** Errors ({len(errors)}): {'; '.join(errors[:5])}")
    elif errors:
        status_msg = mo.md(f"**Processed {len(metrics_df)} datasets** ({len(errors)} errors)")
    else:
        status_msg = mo.md(f"**Processed {len(metrics_df)} datasets successfully**")
    status_msg
    return (metrics_df,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 5. ROC-AUC Box Plots

    Distribution of ROC-AUC scores (abs-based and directional) by software tool.
    """
    )
    return


@app.cell
def _(mo, px, metrics_df):
    if len(metrics_df) == 0:
        box_plot_output = mo.md("**No data to display. Select software tools above.**")
    else:
        fig_box = px.box(
            metrics_df.reset_index(),
            x="software_name",
            y="roc_auc",
            color="software_name",
            points="all",
            hover_name="dataset_id",
            labels={
                "roc_auc": "ROC-AUC Score (Abs-based)",
                "software_name": "Software",
            },
            title="ROC-AUC Scores by Software Tool (Abs-based)",
            color_discrete_sequence=[
                "#e41a1c",
                "#377eb8",
                "#4daf4a",
                "#984ea3",
                "#ff7f00",
                "#ffff33",
                "#a65628",
                "#f781bf",
                "#999999",
                "#66c2a5",
            ],
        )
        fig_box.update_traces(marker=dict(size=8))
        fig_box.update_layout(showlegend=False)
        box_plot_output = fig_box
    box_plot_output
    return


@app.cell
def _(mo, px, metrics_df):
    if len(metrics_df) == 0:
        box_plot_dir_output = mo.md("**No data to display.**")
    else:
        fig_box_dir = px.box(
            metrics_df.reset_index(),
            x="software_name",
            y="roc_auc_directional",
            color="software_name",
            points="all",
            hover_name="dataset_id",
            labels={
                "roc_auc_directional": "Directional ROC-AUC Score",
                "software_name": "Software",
            },
            title="Directional ROC-AUC Scores by Software Tool",
            color_discrete_sequence=[
                "#e41a1c",
                "#377eb8",
                "#4daf4a",
                "#984ea3",
                "#ff7f00",
                "#ffff33",
                "#a65628",
                "#f781bf",
                "#999999",
                "#66c2a5",
            ],
        )
        fig_box_dir.update_traces(marker=dict(size=8))
        fig_box_dir.update_layout(showlegend=False)
        box_plot_dir_output = fig_box_dir
    box_plot_dir_output
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 6. Scatter Plots: Total Precursors

    Relationship between metrics and total number of quantified precursors.
    """
    )
    return


@app.cell
def _(mo, px, metrics_df):
    if len(metrics_df) == 0:
        scatter_epsilon_total = mo.md("**No data to display.**")
    else:
        fig_eps_total = px.scatter(
            metrics_df.reset_index(),
            x="median_abs_epsilon_global",
            y="n_precursors",
            color="software_name",
            hover_name="dataset_id",
            labels={
                "n_precursors": "Number of Precursors (Total)",
                "median_abs_epsilon_global": "Median Abs Epsilon",
                "software_name": "Software",
            },
            title="Median Abs Epsilon vs Total Precursors",
            color_discrete_sequence=[
                "#e41a1c",
                "#377eb8",
                "#4daf4a",
                "#984ea3",
                "#ff7f00",
                "#ffff33",
                "#a65628",
                "#f781bf",
                "#999999",
                "#66c2a5",
            ],
        )
        fig_eps_total.update_traces(marker=dict(size=10))
        scatter_epsilon_total = fig_eps_total
    scatter_epsilon_total
    return


@app.cell
def _(mo, px, metrics_df):
    if len(metrics_df) == 0:
        scatter_roc_total = mo.md("**No data to display.**")
    else:
        fig_roc_total = px.scatter(
            metrics_df.reset_index(),
            x="roc_auc_directional",
            y="n_precursors",
            color="software_name",
            hover_name="dataset_id",
            labels={
                "n_precursors": "Number of Precursors (Total)",
                "roc_auc_directional": "Directional ROC-AUC",
                "software_name": "Software",
            },
            title="Directional ROC-AUC vs Total Precursors",
            color_discrete_sequence=[
                "#e41a1c",
                "#377eb8",
                "#4daf4a",
                "#984ea3",
                "#ff7f00",
                "#ffff33",
                "#a65628",
                "#f781bf",
                "#999999",
                "#66c2a5",
            ],
        )
        fig_roc_total.update_traces(marker=dict(size=10))
        scatter_roc_total = fig_roc_total
    scatter_roc_total
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 7. Scatter Plots: Non-Human Precursors (YEAST + ECOLI)

    Relationship between metrics and the number of non-human (changed species) precursors.
    """
    )
    return


@app.cell
def _(mo, px, metrics_df):
    if len(metrics_df) == 0:
        scatter_epsilon_nonhuman = mo.md("**No data to display.**")
    else:
        df_eps_nh = metrics_df.reset_index().copy()
        df_eps_nh["n_precursors_nonhuman"] = df_eps_nh["n_precursors_YEAST"] + df_eps_nh["n_precursors_ECOLI"]

        fig_eps_nh = px.scatter(
            df_eps_nh,
            x="median_abs_epsilon_global",
            y="n_precursors_nonhuman",
            color="software_name",
            hover_name="dataset_id",
            labels={
                "n_precursors_nonhuman": "Number of Non-Human Precursors (YEAST + ECOLI)",
                "median_abs_epsilon_global": "Median Abs Epsilon",
                "software_name": "Software",
            },
            title="Median Abs Epsilon vs Non-Human Precursors",
            color_discrete_sequence=[
                "#e41a1c",
                "#377eb8",
                "#4daf4a",
                "#984ea3",
                "#ff7f00",
                "#ffff33",
                "#a65628",
                "#f781bf",
                "#999999",
                "#66c2a5",
            ],
        )
        fig_eps_nh.update_traces(marker=dict(size=10))
        scatter_epsilon_nonhuman = fig_eps_nh
    scatter_epsilon_nonhuman
    return


@app.cell
def _(mo, px, metrics_df):
    if len(metrics_df) == 0:
        scatter_roc_nonhuman = mo.md("**No data to display.**")
    else:
        df_roc_nh = metrics_df.reset_index().copy()
        df_roc_nh["n_precursors_nonhuman"] = df_roc_nh["n_precursors_YEAST"] + df_roc_nh["n_precursors_ECOLI"]

        fig_roc_nh = px.scatter(
            df_roc_nh,
            x="roc_auc_directional",
            y="n_precursors_nonhuman",
            color="software_name",
            hover_name="dataset_id",
            labels={
                "n_precursors_nonhuman": "Number of Non-Human Precursors (YEAST + ECOLI)",
                "roc_auc_directional": "Directional ROC-AUC",
                "software_name": "Software",
            },
            title="Directional ROC-AUC vs Non-Human Precursors",
            color_discrete_sequence=[
                "#e41a1c",
                "#377eb8",
                "#4daf4a",
                "#984ea3",
                "#ff7f00",
                "#ffff33",
                "#a65628",
                "#f781bf",
                "#999999",
                "#66c2a5",
            ],
        )
        fig_roc_nh.update_traces(marker=dict(size=10))
        scatter_roc_nonhuman = fig_roc_nh
    scatter_roc_nonhuman
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 8. Export Results

    Download all computed metrics as a CSV file.
    """
    )
    return


@app.cell
def _(mo, metrics_df):
    if len(metrics_df) > 0:
        csv_data = metrics_df.to_csv(index=True)
        download_output = mo.download(
            data=csv_data.encode("utf-8"),
            filename="benchmark_metrics_results.csv",
            label="Download All Metrics Results (CSV)",
        )
    else:
        download_output = mo.md("**No data to download.**")
    download_output
    return


if __name__ == "__main__":
    app.run()
