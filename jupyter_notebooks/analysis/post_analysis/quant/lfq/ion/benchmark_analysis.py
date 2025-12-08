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
    # Get CLI args for module selection
    args = mo.cli_args()
    module_key = args.get("module", "dda_qexactive")

    # Module configurations
    CONFIGS = {
        # DDA ion-level modules
        "dda_qexactive": {
            "title": "DDA Q-Exactive Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DDA_QExactive",
            "module_class": "DDAQuantIonModuleQExactive",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        "dda_astral": {
            "title": "DDA Astral Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DDA_Astral",
            "module_class": "DDAQuantIonAstralModule",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DDA_Astral/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        # DDA peptidoform-level module
        "dda_peptidoform": {
            "title": "DDA Peptidoform Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_peptidoform_DDA",
            "module_class": "DDAQuantPeptidoformModule",
            "repo_url": "https://github.com/Proteobench/Results_quant_peptidoform_DDA/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        # DIA ion-level modules
        "dia_astral": {
            "title": "DIA Astral Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DIA_Astral",
            "module_class": "DIAQuantIonModuleAstral",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        "dia_diapasef": {
            "title": "DIA diaPASEF Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF",
            "module_class": "DIAQuantIonModulediaPASEF",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_diaPASEF/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        "dia_aif": {
            "title": "DIA AIF Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DIA_AIF",
            "module_class": "DIAQuantIonModuleAIF",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_AIF/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        "dia_zenotof": {
            "title": "DIA ZenoTOF Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DIA_ZenoTOF",
            "module_class": "DIAQuantIonModuleZenoTOF",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_ZenoTOF/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
        "dia_singlecell": {
            "title": "DIA Single-Cell Ion Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_ion_DIA_singlecell",
            "module_class": "DIAQuantIonModulediaSC",
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_singlecell/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST"],
        },
        # DIA peptidoform-level module
        "dia_peptidoform": {
            "title": "DIA Peptidoform Benchmark Analysis",
            "module_import": "proteobench.modules.quant.quant_lfq_peptidoform_DIA",
            "module_class": "DIAQuantPeptidoformModule",
            "repo_url": "https://github.com/Proteobench/Results_quant_peptidoform_DIA/archive/refs/heads/main.zip",
            "species": ["HUMAN", "YEAST", "ECOLI"],
        },
    }

    if module_key not in CONFIGS:
        raise ValueError(f"Unknown module: {module_key}. Available: {list(CONFIGS.keys())}")

    config = CONFIGS[module_key]

    return CONFIGS, args, config, module_key


@app.cell(hide_code=True)
def _(config, mo):
    _species_display = ", ".join(config["species"])
    mo.md(
        f"""
    # {config["title"]}

    This notebook analyzes **all benchmark metrics** across different proteomics software tools.

    **Module:** `{config["module_class"]}`
    **Species:** {_species_display}

    **ROC-AUC Metrics:**
    - **ROC-AUC**: Measures separation of changed vs unchanged species using `abs(log2_FC)`
    - **Directional ROC-AUC**: Uses direction-aware scoring

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
    import importlib
    import io
    import os
    import sys
    from collections import defaultdict
    from pathlib import Path

    import numpy as np
    import pandas as pd
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

    return (
        NOTEBOOK_DIR,
        SOFTWARE_COLORS,
        defaultdict,
        importlib,
        io,
        np,
        os,
        pd,
        px,
        sys,
    )


@app.cell(hide_code=True)
def _(SOFTWARE_COLORS, px):
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
def _(config, importlib):
    # Dynamic module loading
    from proteobench.datapoint.quant_datapoint import QuantDatapoint
    from proteobench.utils.server_io import get_merged_json, get_raw_data

    mod = importlib.import_module(config["module_import"])
    ModuleClass = getattr(mod, config["module_class"])

    return ModuleClass, QuantDatapoint, get_merged_json, get_raw_data, mod


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
def _(config, get_merged_json, mo):
    df_all = get_merged_json(repo_url=config["repo_url"])
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
def _(NOTEBOOK_DIR, df_all, get_raw_data, module_key, os):
    OUTPUT_DIR = NOTEBOOK_DIR.resolve() / "temp_results" / module_key

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
    return OUTPUT_DIR, df_available, df_to_download, get_datasets_to_download, hash_vis_dirs


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3. Compute All Benchmark Metrics

    Recomputes all benchmark metrics (ROC-AUC, epsilon, CV) for each dataset.
    """
    )
    return


@app.cell(hide_code=True)
def _(
    ModuleClass,
    QuantDatapoint,
    config,
    defaultdict,
    df_available,
    hash_vis_dirs,
    io,
    mo,
    np,
    os,
    pd,
    sys,
):
    def _extract_species_stats_from_metrics(metrics_dict, results_df, software_name, dataset_id, species_list):
        """Extract per-species stats from get_metrics() output and results_df."""
        stats = []
        for sp in species_list:
            # Get accuracy and precision from metrics dict
            accuracy = metrics_dict.get(f"median_abs_epsilon_{sp}", np.nan)
            precision = metrics_dict.get(f"median_abs_epsilon_precision_{sp}", np.nan)
            log2_empirical = metrics_dict.get(f"median_log2_empirical_{sp}", np.nan)
            n_prec = metrics_dict.get(f"nr_prec_{sp}", 0)

            if n_prec == 0:
                continue

            # Get expected ratio from results_df
            sp_data = results_df[results_df["species"] == sp]
            log2_expected = (
                sp_data["log2_expectedRatio"].iloc[0] if len(sp_data) > 0 and "log2_expectedRatio" in sp_data.columns
                else np.nan
            )

            # Compute bias and reduction
            bias = log2_empirical - log2_expected if not (np.isnan(log2_empirical) or np.isnan(log2_expected)) else np.nan
            reduction = (1 - precision / accuracy) * 100 if accuracy > 0 else np.nan

            stats.append({
                "software": software_name,
                "dataset_id": dataset_id,
                "species": sp,
                "n_precursors": n_prec,
                "log2_expected": round(log2_expected, 3) if not np.isnan(log2_expected) else np.nan,
                "log2_empirical_median": round(log2_empirical, 3) if not np.isnan(log2_empirical) else np.nan,
                "bias": round(bias, 3) if not np.isnan(bias) else np.nan,
                "median_abs_dev_expected": round(accuracy, 4) if not np.isnan(accuracy) else np.nan,
                "median_abs_dev_empirical": round(precision, 4) if not np.isnan(precision) else np.nan,
                "reduction_%": round(reduction, 1) if not np.isnan(reduction) else np.nan,
            })
        return stats

    metrics_results = {}
    all_species_stats = []
    errors = []
    min_prec = 3  # Minimum precursor quantifications required
    species_list = config["species"]

    # Capture warnings during processing
    warnings_buffer = io.StringIO()
    old_stdout = sys.stdout

    with mo.status.spinner(title="Computing benchmark metrics..."):
        sys.stdout = warnings_buffer
        for _, row in df_available.iterrows():
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
            module_obj = ModuleClass(token="")

            try:
                # benchmarking() returns (results_performance, all_datapoints, result_df)
                results_performance, _, _ = module_obj.benchmarking(
                    matching_file, software_name, user_input=user_config, all_datapoints=[]
                )

                # Compute all metrics using QuantDatapoint.get_metrics()
                metrics = QuantDatapoint.get_metrics(results_performance, min_nr_observed=min_prec)
                m = metrics[min_prec]

                result_entry = {
                    "software_name": software_name,
                    "dataset_id": row["id"],
                    "n_precursors": m["nr_prec"],
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

                # Add per-species precursor counts
                for sp in species_list:
                    result_entry[f"n_precursors_{sp}"] = m.get(f"nr_prec_{sp}", 0)

                metrics_results[row["id"]] = result_entry

                # Extract per-species stats from metrics dict (no separate computation needed)
                species_stats = _extract_species_stats_from_metrics(
                    m, results_performance, software_name, row["id"], species_list
                )
                all_species_stats.extend(species_stats)

            except KeyError as e:
                sys.stdout = old_stdout
                raise KeyError(f"Missing metric key {e} for {row['id']}. Check get_metrics() implementation.") from e
            except (FileNotFoundError, IOError) as e:
                errors.append(f"{row['id']}: {str(e)[:80]}")
                continue
            except Exception as e:
                errors.append(f"{row['id']}: {type(e).__name__}: {str(e)[:60]}")
                continue
        sys.stdout = old_stdout

    captured_warnings = warnings_buffer.getvalue()
    metrics_df = pd.DataFrame(metrics_results).T
    species_stats_df = pd.DataFrame(all_species_stats)

    if len(metrics_df) == 0:
        status_msg = mo.md(f"**No data processed.** Errors ({len(errors)}): {'; '.join(errors[:5])}")
    elif errors:
        status_msg = mo.md(f"**Processed {len(metrics_df)} datasets** ({len(errors)} errors)")
    else:
        status_msg = mo.md(f"**Processed {len(metrics_df)} datasets successfully**")

    # Display status and collapsible warnings
    if captured_warnings.strip():
        output = mo.vstack([
            status_msg,
            mo.accordion({"Processing Warnings (click to expand)": mo.md(f"```\n{captured_warnings}\n```")})
        ])
    else:
        output = status_msg
    output
    return (
        _extract_species_stats_from_metrics,
        all_species_stats,
        errors,
        metrics_df,
        metrics_results,
        min_prec,
        species_stats_df,
        status_msg,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4. Global Metrics: Accuracy vs Precision

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
    return (box_eps_global,)


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
    return (box_prec_global,)


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
    return (box_mean_eps_global,)


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
    return (box_mean_prec_global,)


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
    return (scatter_eps_global,)


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
    return (scatter_prec_global,)


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
    return (scatter_mean_eps_global,)


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
    return (scatter_mean_prec_global,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5. Equal Species Metrics: Accuracy vs Precision

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
    return (box_eps_eq,)


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
    return (box_prec_eq,)


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
    return (scatter_eps_eq,)


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
    return (scatter_prec_eq,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6. ROC-AUC Metrics: Species Separation

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
    return (box_roc,)


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
    return (box_roc_dir,)


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
    return (scatter_roc,)


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
    return (scatter_roc_dir,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7. Export Results

    Download all computed metrics as a CSV file.
    """
    )
    return


@app.cell(hide_code=True)
def _(metrics_df, mo, module_key):
    if len(metrics_df) > 0:
        csv_data = metrics_df.to_csv(index=True)
        download_output = mo.download(
            data=csv_data.encode("utf-8"),
            filename=f"{module_key}_benchmark_metrics.csv",
            label="Download All Metrics Results (CSV)",
        )
    else:
        download_output = mo.md("**No data to download.**")
    download_output
    return (csv_data, download_output)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---

    ## 8. Per-Species Accuracy vs Precision Analysis

    This section compares **accuracy** (deviation from expected ratio) vs **precision** (deviation from empirical center) for each species.

    **Key Metrics:**
    - **Accuracy (epsilon)**: `log2_A_vs_B - log2_expectedRatio` - deviation from theoretical ratio
    - **Precision (epsilon_precision)**: `log2_A_vs_B - log2_empirical_median` - deviation from observed center

    **Why this matters:**
    - If accuracy ~ precision: software is accurate (empirical ~ expected)
    - If precision << accuracy: systematic bias exists (empirical != expected)
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, species_stats_df):
    if len(species_stats_df) > 0:
        display_df = species_stats_df.sort_values(["software", "species", "dataset_id"])
        table_html = display_df.to_html(index=False, classes="dataframe")
        table_output = mo.vstack(
            [
                mo.md("### Per-Software Per-Species Summary (each dataset)"),
                mo.Html(table_html),
            ]
        )
    else:
        table_output = mo.md("**No data available**")
    table_output
    return (display_df, table_html, table_output)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9. Accuracy vs Precision Scatter Plot

    Each point is one dataset. Faceted by species.
    Points below the diagonal line have better precision than accuracy.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, px, species_stats_df):
    if len(species_stats_df) > 0:
        scatter_acc_prec = px.scatter(
            species_stats_df,
            x="median_abs_dev_expected",
            y="median_abs_dev_empirical",
            color="software",
            facet_col="species",
            hover_data=["software", "dataset_id", "bias", "reduction_%"],
            labels={
                "median_abs_dev_expected": "Accuracy (median |eps expected|)",
                "median_abs_dev_empirical": "Precision (median |eps empirical|)",
            },
            title="Accuracy vs Precision by Species (each point = one dataset)",
            color_discrete_sequence=px.colors.qualitative.Plotly,
        )

        # Add diagonal line to each facet
        max_val = max(
            species_stats_df["median_abs_dev_expected"].max(), species_stats_df["median_abs_dev_empirical"].max()
        )
        scatter_acc_prec.add_shape(
            type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(dash="dash", color="gray"), row="all", col="all"
        )

        scatter_acc_prec.update_layout(height=400)
        scatter_acc_prec_output = scatter_acc_prec
    else:
        scatter_acc_prec_output = mo.md("**No data for scatter plot**")
    scatter_acc_prec_output
    return (max_val, scatter_acc_prec, scatter_acc_prec_output)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 10. Reduction by Species

    Box plot showing reduction percentage (how much precision improves over accuracy) by species.
    Higher reduction = larger bias between expected and empirical ratios.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, px, species_stats_df):
    if len(species_stats_df) > 0:
        box_reduction = px.box(
            species_stats_df,
            x="species",
            y="reduction_%",
            color="software",
            points="all",
            hover_data=["dataset_id", "bias"],
            labels={"reduction_%": "Reduction %", "species": "Species"},
            title="Precision Improvement over Accuracy by Species",
            color_discrete_sequence=px.colors.qualitative.Plotly,
        )
        box_reduction.update_layout(height=500)
        box_reduction_output = box_reduction
    else:
        box_reduction_output = mo.md("**No data for box plot**")
    box_reduction_output
    return (box_reduction, box_reduction_output)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 11. Bias Distribution

    Shows the systematic bias (empirical_median - expected) by species and software.
    Bias close to 0 means the software accurately estimates the expected fold change.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, px, species_stats_df):
    if len(species_stats_df) > 0:
        bias_fig = px.box(
            species_stats_df,
            x="species",
            y="bias",
            color="software",
            points="all",
            hover_data=["dataset_id"],
            labels={"bias": "Bias (empirical - expected)", "species": "Species"},
            title="Systematic Bias by Species and Software",
            color_discrete_sequence=px.colors.qualitative.Plotly,
        )
        bias_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        bias_fig.update_layout(height=500)
        bias_output = bias_fig
    else:
        bias_output = mo.md("**No data for bias plot**")
    bias_output
    return (bias_fig, bias_output)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 12. Interpretation

    **If reduction is small (< 10%):**
    - The software is **accurate** - empirical centers are close to expected ratios
    - Precision and accuracy measure similar things in this case

    **If reduction is large (> 30%):**
    - There's systematic bias between expected and observed ratios
    - Precision removes this bias component
    - Worth investigating why bias exists

    **Key insight:** Small reduction != bug in computation. It means expected ~ empirical.
    """
    )
    return


if __name__ == "__main__":
    app.run()
