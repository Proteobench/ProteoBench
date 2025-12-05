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


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Benchmark Metrics Analysis for ProteoBench

    This notebook analyzes **all benchmark metrics** across different proteomics software tools:

    **ROC-AUC Metrics:**
    - **ROC-AUC**: Measures separation of changed vs unchanged species using `abs(log2_FC)`
    - **Directional ROC-AUC**: Uses direction-aware scoring (YEAST positive, ECOLI negative)

    **Epsilon Metrics** (deviation from expected ratio - measures **accuracy**):
    - **Median/Mean Abs Epsilon (Global)**: Overall accuracy across all species
    - **Median/Mean Abs Epsilon (Equal Species)**: Weighted equally per species

    **Epsilon Precision Metrics** (deviation from empirical center - measures **consistency**):
    - **Median/Mean Abs Epsilon Precision (Global)**: How tightly grouped measurements are
    - **Median/Mean Abs Epsilon Precision (Equal Species)**: Per-species consistency, weighted equally

    **CV Metrics** (coefficient of variation):
    - **CV Median/Q75/Q90/Q95**: Reproducibility at different quantiles
    """
    )
    return


@app.cell(hide_code=True)
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

    # Color palette for software tools
    SOFTWARE_COLORS = [
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
    ]

    return NOTEBOOK_DIR, SOFTWARE_COLORS, defaultdict, os, pd, px


@app.cell(hide_code=True)
def _(px, SOFTWARE_COLORS):
    def create_boxplot(df, y_col, y_label, title):
        """Create a box plot for a metric by software tool."""
        fig = px.box(
            df.reset_index(),
            x="software_name",
            y=y_col,
            color="software_name",
            points="all",
            hover_name="dataset_id",
            labels={y_col: y_label, "software_name": "Software"},
            title=title,
            color_discrete_sequence=SOFTWARE_COLORS,
        )
        fig.update_traces(marker=dict(size=8))
        fig.update_layout(showlegend=False)
        return fig

    def create_scatter(df, x_col, x_label, title):
        """Create a scatter plot: metric vs n_precursors."""
        fig = px.scatter(
            df.reset_index(),
            x=x_col,
            y="n_precursors",
            color="software_name",
            hover_name="dataset_id",
            labels={"n_precursors": "Number of Precursors", x_col: x_label, "software_name": "Software"},
            title=title,
            color_discrete_sequence=SOFTWARE_COLORS,
        )
        fig.update_traces(marker=dict(size=10))
        return fig

    return create_boxplot, create_scatter


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1. Load Benchmark Results

    Fetches all benchmark metadata from the GitHub results repository.
    """
    )
    return


@app.cell(hide_code=True)
def _(get_merged_json, mo):
    df_all = get_merged_json(
        repo_url="https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip"
    )
    mo.md(f"**Loaded {len(df_all)} benchmark results from GitHub**")
    return (df_all,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2. Download Raw Datasets

    Downloads missing raw datasets from the server and tracks available files locally.
    """
    )
    return


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3. Select Software Tools

    Choose which software tools to include in the analysis.
    """
    )
    return


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def _(df_available, mo, software_selector):
    selected_software = software_selector.value
    df_selected = df_available[df_available["software_name"].isin(selected_software)]
    mo.md(f"**Selected {len(df_selected)} datasets from {len(selected_software)} software tools**")
    return (df_selected,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4. Compute All Benchmark Metrics

    Recomputes all benchmark metrics (ROC-AUC, epsilon, CV) for each selected dataset.
    """
    )
    return


@app.cell(hide_code=True)
def _(
    DDAQuantIonModuleQExactive,
    QuantDatapoint,
    defaultdict,
    df_selected,
    hash_vis_dirs,
    mo,
    os,
    pd,
):
    metrics_results = {}
    errors = []
    min_prec = 3  # Minimum precursor quantifications required

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
                    # Epsilon metrics (accuracy - deviation from expected ratio)
                    "median_abs_epsilon_global": m["median_abs_epsilon_global"],
                    "mean_abs_epsilon_global": m["mean_abs_epsilon_global"],
                    "variance_epsilon_global": m["variance_epsilon_global"],
                    "median_abs_epsilon_eq_species": m["median_abs_epsilon_eq_species"],
                    "mean_abs_epsilon_eq_species": m["mean_abs_epsilon_eq_species"],
                    # Epsilon precision metrics (consistency - deviation from empirical center)
                    "median_abs_epsilon_precision_global": m["median_abs_epsilon_precision_global"],
                    "mean_abs_epsilon_precision_global": m["mean_abs_epsilon_precision_global"],
                    "median_abs_epsilon_precision_eq_species": m["median_abs_epsilon_precision_eq_species"],
                    "mean_abs_epsilon_precision_eq_species": m["mean_abs_epsilon_precision_eq_species"],
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5. Global Metrics: Accuracy vs Precision

    Comparing accuracy (deviation from expected ratio) vs precision (deviation from empirical center) using global weighting.
    """
    )
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_eps_global = mo.md("**No data to display.**")
    else:
        box_eps_global = create_boxplot(
            metrics_df,
            "median_abs_epsilon_global",
            "Median Abs Epsilon (Global)",
            "Accuracy: Median Abs Epsilon (Global)",
        )
    box_eps_global
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_prec_global = mo.md("**No data to display.**")
    else:
        box_prec_global = create_boxplot(
            metrics_df,
            "median_abs_epsilon_precision_global",
            "Median Abs Epsilon Precision (Global)",
            "Precision: Median Abs Epsilon (Global)",
        )
    box_prec_global
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_mean_eps_global = mo.md("**No data to display.**")
    else:
        box_mean_eps_global = create_boxplot(
            metrics_df,
            "mean_abs_epsilon_global",
            "Mean Abs Epsilon (Global)",
            "Accuracy: Mean Abs Epsilon (Global)",
        )
    box_mean_eps_global
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_mean_prec_global = mo.md("**No data to display.**")
    else:
        box_mean_prec_global = create_boxplot(
            metrics_df,
            "mean_abs_epsilon_precision_global",
            "Mean Abs Epsilon Precision (Global)",
            "Precision: Mean Abs Epsilon (Global)",
        )
    box_mean_prec_global
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_eps_global = mo.md("**No data to display.**")
    else:
        scatter_eps_global = create_scatter(
            metrics_df,
            "median_abs_epsilon_global",
            "Median Abs Epsilon (Global)",
            "Accuracy: Median (Global) vs Precursors",
        )
    scatter_eps_global
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_prec_global = mo.md("**No data to display.**")
    else:
        scatter_prec_global = create_scatter(
            metrics_df,
            "median_abs_epsilon_precision_global",
            "Median Abs Epsilon Precision (Global)",
            "Precision: Median (Global) vs Precursors",
        )
    scatter_prec_global
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_mean_eps_global = mo.md("**No data to display.**")
    else:
        scatter_mean_eps_global = create_scatter(
            metrics_df,
            "mean_abs_epsilon_global",
            "Mean Abs Epsilon (Global)",
            "Accuracy: Mean (Global) vs Precursors",
        )
    scatter_mean_eps_global
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_mean_prec_global = mo.md("**No data to display.**")
    else:
        scatter_mean_prec_global = create_scatter(
            metrics_df,
            "mean_abs_epsilon_precision_global",
            "Mean Abs Epsilon Precision (Global)",
            "Precision: Mean (Global) vs Precursors",
        )
    scatter_mean_prec_global
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6. Equal Species Metrics: Accuracy vs Precision

    Comparing accuracy vs precision using equal species weighting (each species contributes equally).
    """
    )
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_eps_eq = mo.md("**No data to display.**")
    else:
        box_eps_eq = create_boxplot(
            metrics_df,
            "median_abs_epsilon_eq_species",
            "Median Abs Epsilon (Equal Species)",
            "Accuracy: Median Abs Epsilon (Equal Species)",
        )
    box_eps_eq
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_prec_eq = mo.md("**No data to display.**")
    else:
        box_prec_eq = create_boxplot(
            metrics_df,
            "median_abs_epsilon_precision_eq_species",
            "Median Abs Epsilon Precision (Equal Species)",
            "Precision: Median Abs Epsilon (Equal Species)",
        )
    box_prec_eq
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_eps_eq = mo.md("**No data to display.**")
    else:
        scatter_eps_eq = create_scatter(
            metrics_df,
            "median_abs_epsilon_eq_species",
            "Median Abs Epsilon (Equal Species)",
            "Accuracy (Equal Species) vs Precursors",
        )
    scatter_eps_eq
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_prec_eq = mo.md("**No data to display.**")
    else:
        scatter_prec_eq = create_scatter(
            metrics_df,
            "median_abs_epsilon_precision_eq_species",
            "Median Abs Epsilon Precision (Equal Species)",
            "Precision (Equal Species) vs Precursors",
        )
    scatter_prec_eq
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7. ROC-AUC Metrics: Species Separation

    Comparing ROC-AUC (abs-based) vs Directional ROC-AUC for species separation.
    """
    )
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_roc = mo.md("**No data to display.**")
    else:
        box_roc = create_boxplot(
            metrics_df,
            "roc_auc",
            "ROC-AUC (Abs-based)",
            "ROC-AUC (Abs-based)",
        )
    box_roc
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        box_roc_dir = mo.md("**No data to display.**")
    else:
        box_roc_dir = create_boxplot(
            metrics_df,
            "roc_auc_directional",
            "Directional ROC-AUC",
            "Directional ROC-AUC",
        )
    box_roc_dir
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_roc = mo.md("**No data to display.**")
    else:
        scatter_roc = create_scatter(
            metrics_df,
            "roc_auc",
            "ROC-AUC (Abs-based)",
            "ROC-AUC (Abs-based) vs Precursors",
        )
    scatter_roc
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        scatter_roc_dir = mo.md("**No data to display.**")
    else:
        scatter_roc_dir = create_scatter(
            metrics_df,
            "roc_auc_directional",
            "Directional ROC-AUC",
            "Directional ROC-AUC vs Precursors",
        )
    scatter_roc_dir
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8. Export Results

    Download all computed metrics as a CSV file.
    """
    )
    return


@app.cell(hide_code=True)
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
