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
            "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_Astral/archive/refs/heads/main.zip",
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

    ---

    ## Metrics Overview

    **Epsilon Metrics** (deviation from expected ratio - measures **accuracy**):
    - **Median/Mean Abs Epsilon**: How close measurements are to theoretical ratios (lower = better)
    - Available with *global weighting* (each precursor equal) or *equal species weighting* (each species equal)

    **Epsilon Precision Metrics** (deviation from empirical center - measures **consistency**):
    - **Median/Mean Abs Epsilon Precision**: How tightly grouped measurements are around observed center
    - Same weighting options as epsilon metrics

    **ROC-AUC Metrics** (measures **species separation**):
    - **Directional ROC-AUC**: Ability to distinguish changed vs unchanged species (higher = better)

    **CV Metrics** (coefficient of variation - measures **reproducibility**):
    - **CV Median/Q75/Q90/Q95**: Reproducibility at different quantiles (lower = better)

    ---

    ## Table of Contents

    1. [Load Benchmark Results](#1-load-benchmark-results) - Fetch metadata from GitHub
    2. [Download Raw Datasets](#2-download-raw-datasets) - Download missing datasets
    3. [Compute All Benchmark Metrics](#3-compute-all-benchmark-metrics) - Recompute ROC-AUC, epsilon, CV
    4. [Epsilon Metrics (Global Weighting)](#4-epsilon-metrics-global-weighting) - Each precursor weighted equally
    5. [Epsilon Metrics (Equal Species Weighting)](#5-epsilon-metrics-equal-species-weighting) - Each species weighted equally
    6. [ROC-AUC Metrics: Species Separation](#6-roc-auc-metrics-species-separation) - Directional ROC-AUC
    7. [CV Metrics: Reproducibility](#7-cv-metrics-reproducibility) - CV at Median, Q75, Q90, Q95
    8. [Per-Species Accuracy vs Precision Analysis](#8-per-species-accuracy-vs-precision-analysis) - Per-species breakdown
    9. [Accuracy vs Precision Scatter Plot](#9-accuracy-vs-precision-scatter-plot) - Faceted by species
    10. [Reduction by Species](#10-reduction-by-species) - Precision improvement
    11. [Bias Distribution](#11-bias-distribution) - Systematic bias analysis
    12. [Export Results](#12-export-results) - Download CSV
    """
    )
    return


@app.cell(hide_code=True)
def _():
    import importlib
    import io
    import json
    import os
    import shutil
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

    # Color mapping for software tools - consistent with proteobench/plotting/plot_quant.py
    SOFTWARE_COLOR_MAP = {
        "MaxQuant": "#8bc6fd",
        "AlphaPept": "#17212b",
        "ProlineStudio": "#8b26ff",
        "MSAngel": "#C0FA7D",
        "FragPipe": "#F89008",
        "i2MassChroQ": "#108E2E",
        "Sage": "#E43924",
        "WOMBAT": "#663200",
        "DIA-NN": "#d42f2f",
        "AlphaDIA": "#1D2732",
        "Custom": "#000000",
        "Spectronaut": "#007548",
        "FragPipe (DIA-NN quant)": "#F89008",
        "MSAID": "#bfef45",
        "MetaMorpheus": "#637C7A",
        "Proteome Discoverer": "#911eb4",
        "PEAKS": "#f032e6",
        "quantms": "#f5e830",
    }
    # Fallback color palette for unknown software
    FALLBACK_COLORS = [
        "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
        "#ffff33", "#a65628", "#f781bf", "#999999", "#66c2a5",
    ]

    return (
        FALLBACK_COLORS,
        NOTEBOOK_DIR,
        SOFTWARE_COLOR_MAP,
        defaultdict,
        importlib,
        io,
        json,
        np,
        os,
        pd,
        px,
        shutil,
        sys,
    )


@app.cell(hide_code=True)
def _(FALLBACK_COLORS, SOFTWARE_COLOR_MAP, px):
    def _get_color_map(df):
        """Build color map for software tools in the dataframe."""
        software_names = df["software_name"].unique()
        color_map = {}
        fallback_idx = 0
        for name in sorted(software_names):  # Sort for consistency
            if name in SOFTWARE_COLOR_MAP:
                color_map[name] = SOFTWARE_COLOR_MAP[name]
            else:
                color_map[name] = FALLBACK_COLORS[fallback_idx % len(FALLBACK_COLORS)]
                fallback_idx += 1
        return color_map

    def create_boxplot(df, y_col, y_label, title):
        """Create a box plot for a metric by software tool."""
        color_map = _get_color_map(df)
        sorted_software = sorted(df["software_name"].unique())
        fig = px.box(
            df.reset_index(),
            x="software_name",
            y=y_col,
            color="software_name",
            points="all",
            hover_name="dataset_id",
            hover_data=["software_version", "enzyme", "enable_match_between_runs", "ident_fdr_psm"],
            labels={y_col: y_label, "software_name": "Software"},
            title=title,
            color_discrete_map=color_map,
            category_orders={"software_name": sorted_software},
        )
        fig.update_traces(marker=dict(size=8))
        fig.update_layout(showlegend=False)
        return fig

    def create_scatter(df, x_col, x_label, title):
        """Create a scatter plot: metric vs n_precursors."""
        color_map = _get_color_map(df)
        fig = px.scatter(
            df.reset_index(),
            x=x_col,
            y="n_precursors",
            color="software_name",
            hover_name="dataset_id",
            hover_data=["software_version", "enzyme", "enable_match_between_runs", "ident_fdr_psm"],
            labels={"n_precursors": "Number of Precursors", x_col: x_label, "software_name": "Software"},
            title=title,
            color_discrete_map=color_map,
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
def _(NOTEBOOK_DIR, config, get_merged_json, json, mo, pd, shutil):
    # Extract repo name from URL (e.g., "Results_quant_ion_DIA_AIF")
    repo_name = config["repo_url"].split("/")[-5]
    results_dir = NOTEBOOK_DIR / "temp_results" / repo_name
    json_dir = results_dir / f"{repo_name}-main"

    # Check if JSONs already exist locally
    if json_dir.exists() and any(json_dir.glob("*.json")):
        # Load from local files
        combined_json = []
        for json_file in json_dir.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                try:
                    combined_json.append(json.load(f))
                except json.JSONDecodeError as e:
                    print(f"Error reading {json_file}: {e}")
        if not combined_json:
            raise RuntimeError(f"No valid JSON files found in {json_dir}")
        df_all = pd.DataFrame(combined_json)
        source_msg = f"**Loaded {len(df_all)} benchmark results from local cache**"
    else:
        # Download from GitHub - wrap in try/except to provide clear error
        try:
            df_all = get_merged_json(repo_url=config["repo_url"])
        except Exception as e:
            raise RuntimeError(
                f"Failed to download data from GitHub: {e}\n"
                f"Run 'make refresh' to retry or check your network connection."
            ) from e

        if df_all is None or len(df_all) == 0:
            raise RuntimeError(f"No data returned from GitHub for {repo_name}")

        # Move extracted folder to temp_results
        extracted_dir = NOTEBOOK_DIR / repo_name
        if extracted_dir.exists():
            results_dir.mkdir(parents=True, exist_ok=True)
            if json_dir.exists():
                shutil.rmtree(json_dir)
            shutil.move(str(extracted_dir / f"{repo_name}-main"), str(json_dir))
            # Remove empty parent if exists
            if extracted_dir.exists() and not any(extracted_dir.iterdir()):
                extracted_dir.rmdir()
        source_msg = f"**Loaded {len(df_all)} benchmark results from GitHub**"

    mo.md(source_msg)
    return (df_all, repo_name, results_dir)


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
def _(df_all, get_raw_data, os, results_dir):
    OUTPUT_DIR = results_dir.resolve()

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
                    "software_version": row.get("software_version", ""),
                    "enzyme": row.get("enzyme", ""),
                    "enable_match_between_runs": row.get("enable_match_between_runs", ""),
                    "ident_fdr_psm": row.get("ident_fdr_psm", ""),
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
    ## 4. Epsilon Metrics (Global Weighting)

    This section compares **accuracy** (deviation from expected ratio) vs **precision** (deviation from empirical center)
    using **global weighting**, where each precursor contributes equally regardless of species.

    - **Accuracy (epsilon)**: How close are measurements to the theoretical/expected ratio?
    - **Precision (epsilon_precision)**: How tightly grouped are measurements around the observed center?

    Lower values indicate better performance.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### 4.1 Median Epsilon (Global)""")
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "median_abs_epsilon_global",
            "Median Abs Epsilon (Global)",
            "Accuracy: Median Abs Epsilon (Global)",
        )
    mo.vstack([_fig, mo.md("*Figure 4.1: Distribution of median absolute epsilon (accuracy) by software.*")])
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "median_abs_epsilon_precision_global",
            "Median Abs Epsilon Precision (Global)",
            "Precision: Median Abs Epsilon (Global)",
        )
    mo.vstack([_fig, mo.md("*Figure 4.2: Distribution of median absolute epsilon precision by software.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "median_abs_epsilon_global",
            "Median Abs Epsilon (Global)",
            "Accuracy: Median (Global) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 4.3: Median accuracy vs number of precursors.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "median_abs_epsilon_precision_global",
            "Median Abs Epsilon Precision (Global)",
            "Precision: Median (Global) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 4.4: Median precision vs number of precursors.*")])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### 4.2 Mean Epsilon (Global)""")
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "mean_abs_epsilon_global",
            "Mean Abs Epsilon (Global)",
            "Accuracy: Mean Abs Epsilon (Global)",
        )
    mo.vstack([_fig, mo.md("*Figure 4.5: Mean absolute epsilon (accuracy) by software. Mean is more sensitive to outliers than median.*")])
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "mean_abs_epsilon_precision_global",
            "Mean Abs Epsilon Precision (Global)",
            "Precision: Mean Abs Epsilon (Global)",
        )
    mo.vstack([_fig, mo.md("*Figure 4.6: Mean absolute epsilon precision by software.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "mean_abs_epsilon_global",
            "Mean Abs Epsilon (Global)",
            "Accuracy: Mean (Global) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 4.7: Mean accuracy vs number of precursors.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "mean_abs_epsilon_precision_global",
            "Mean Abs Epsilon Precision (Global)",
            "Precision: Mean (Global) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 4.8: Mean precision vs number of precursors.*")])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5. Epsilon Metrics (Equal Species Weighting)

    Unlike global weighting where each precursor contributes equally, **equal species weighting** ensures each species
    contributes equally to the final metric regardless of how many precursors were identified per species.

    This prevents the dominant species (typically HUMAN with more identifications) from overshadowing performance on minority species.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### 5.1 Median Epsilon (Equal Species)""")
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "median_abs_epsilon_eq_species",
            "Median Abs Epsilon (Equal Species)",
            "Accuracy: Median Abs Epsilon (Equal Species)",
        )
    mo.vstack([_fig, mo.md("*Figure 5.1: Accuracy with equal species weighting.*")])
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "median_abs_epsilon_precision_eq_species",
            "Median Abs Epsilon Precision (Equal Species)",
            "Precision: Median Abs Epsilon (Equal Species)",
        )
    mo.vstack([_fig, mo.md("*Figure 5.2: Precision with equal species weighting.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "median_abs_epsilon_eq_species",
            "Median Abs Epsilon (Equal Species)",
            "Accuracy (Equal Species) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 5.3: Equal-species accuracy vs precursor count.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "median_abs_epsilon_precision_eq_species",
            "Median Abs Epsilon Precision (Equal Species)",
            "Precision (Equal Species) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 5.4: Equal-species precision vs precursor count.*")])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### 5.2 Mean Epsilon (Equal Species)""")
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "mean_abs_epsilon_eq_species",
            "Mean Abs Epsilon (Equal Species)",
            "Accuracy: Mean Abs Epsilon (Equal Species)",
        )
    mo.vstack([_fig, mo.md("*Figure 5.5: Mean accuracy with equal species weighting.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "mean_abs_epsilon_eq_species",
            "Mean Abs Epsilon (Equal Species)",
            "Mean Accuracy (Equal Species) vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 5.6: Mean equal-species accuracy vs precursor count.*")])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6. ROC-AUC Metrics: Species Separation

    **Directional ROC-AUC** measures how well software can distinguish between species with different expected fold changes.
    It uses signed fold changes to test both magnitude and direction of change.

    - **ROC-AUC = 1.0**: Perfect separation of changed vs unchanged species
    - **ROC-AUC = 0.5**: Random classification (no discrimination ability)

    Higher values indicate better species separation ability.
    """
    )
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "roc_auc_directional",
            "Directional ROC-AUC",
            "Directional ROC-AUC",
        )
    mo.vstack([_fig, mo.md("*Figure 6.1: Directional ROC-AUC by software. Values closer to 1.0 indicate better separation of changed vs unchanged species.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "roc_auc_directional",
            "Directional ROC-AUC",
            "Directional ROC-AUC vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 6.2: Directional ROC-AUC vs number of precursors.*")])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7. CV Metrics: Reproducibility

    The Coefficient of Variation (CV) measures reproducibility across technical replicates. CV = standard deviation / mean,
    expressed as a fraction. Lower CV values indicate more reproducible quantification.

    We show CV at different quantiles of the distribution:
    - **CV Median**: Typical reproducibility (50% of precursors have CV below this)
    - **CV Q75**: 75th percentile - shows reproducibility including moderately variable precursors
    - **CV Q90**: 90th percentile - includes most precursors except outliers
    - **CV Q95**: 95th percentile - near-worst-case reproducibility
    """
    )
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "CV_median",
            "CV Median",
            "CV Median by Software",
        )
    mo.vstack([_fig, mo.md("*Figure 7.1: Median CV by software. Represents typical reproducibility - 50% of precursors have CV below this value.*")])
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "CV_q75",
            "CV Q75",
            "CV 75th Percentile by Software",
        )
    mo.vstack([_fig, mo.md("*Figure 7.2: 75th percentile CV. 75% of precursors have CV below this value.*")])
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "CV_q90",
            "CV Q90",
            "CV 90th Percentile by Software",
        )
    mo.vstack([_fig, mo.md("*Figure 7.3: 90th percentile CV. Shows variability including most precursors except top 10% outliers.*")])
    return


@app.cell(hide_code=True)
def _(create_boxplot, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_boxplot(
            metrics_df,
            "CV_q95",
            "CV Q95",
            "CV 95th Percentile by Software",
        )
    mo.vstack([_fig, mo.md("*Figure 7.4: 95th percentile CV. Near-worst-case reproducibility.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "CV_median",
            "CV Median",
            "CV Median vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 7.5: Median CV vs number of precursors. Shows if identifying more precursors affects reproducibility.*")])
    return


@app.cell(hide_code=True)
def _(create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _fig = mo.md("**No data to display.**")
    else:
        _fig = create_scatter(
            metrics_df,
            "CV_q75",
            "CV Q75",
            "CV 75th Percentile vs Precursors",
        )
    mo.vstack([_fig, mo.md("*Figure 7.6: 75th percentile CV vs number of precursors.*")])
    return


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
                mo.Html(table_html),
                mo.md("*Table 8.1: Per-species breakdown showing expected vs empirical ratios, bias, and reduction percentage for each dataset.*"),
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

    The scatter plot below shows accuracy (x-axis) vs precision (y-axis) for each dataset, faceted by species.
    Points **below the diagonal** indicate precision is better than accuracy (systematic bias exists).
    Points **on the diagonal** indicate similar accuracy and precision (no systematic bias).
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
        _output = mo.vstack([scatter_acc_prec, mo.md("*Figure 9.1: Accuracy vs precision scatter plot. Diagonal line = equal accuracy and precision. Points below line have systematic bias.*")])
    else:
        _output = mo.md("**No data for scatter plot**")
    _output
    return (max_val, scatter_acc_prec)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 10. Reduction by Species

    The **reduction percentage** quantifies how much better precision is compared to accuracy:
    `reduction = (1 - precision/accuracy) × 100%`

    - **Small reduction (< 10%)**: Software is accurate - no systematic bias
    - **Large reduction (> 30%)**: Systematic bias exists between expected and observed ratios
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
        _output = mo.vstack([box_reduction, mo.md("*Figure 10.1: Reduction percentage by species. Higher values indicate larger systematic bias.*")])
    else:
        _output = mo.md("**No data for box plot**")
    _output
    return (box_reduction,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 11. Bias Distribution

    The **bias** is the difference between the observed empirical median and the expected fold change:
    `bias = log2_empirical_median - log2_expected`

    Bias close to 0 indicates the software accurately recovers the expected fold change.
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
        _output = mo.vstack([bias_fig, mo.md("*Figure 11.1: Bias distribution by species. Dashed line at 0 = no bias. Values above = over-estimation, below = under-estimation.*")])
    else:
        _output = mo.md("**No data for bias plot**")
    _output
    return (bias_fig,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---

    ## 12. Export Results

    Download all computed benchmark metrics as a CSV file for further analysis.
    The file includes all metrics for each dataset: ROC-AUC, epsilon, CV, and per-species counts.
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


if __name__ == "__main__":
    app.run()
