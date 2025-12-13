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

    # Create sticky sidebar with Table of Contents (must be last expression in cell)
    mo.sidebar(
        [
            mo.md("## Navigation"),
            mo.md("""
- [Overview: Heatmaps](#overview-score-heatmaps)
- [1. Epsilon (Global)](#1-epsilon-metrics-global-weighting)
- [2. Epsilon (Equal Species)](#2-epsilon-metrics-equal-species-weighting)
- [3. ROC-AUC](#3-roc-auc-metrics-species-separation)
- [4. CV Metrics](#4-cv-metrics-reproducibility)
- [5. Per-Species Analysis](#5-per-species-accuracy-vs-precision-analysis)
- [6. Acc vs Prec Scatter](#6-accuracy-vs-precision-scatter-plot)
- [7. Export](#7-export-results)
"""),
            mo.md("---"),
            mo.md(f"**Module:**<br>`{config['module_class']}`"),
            mo.md(f"**Species:** {_species_display}"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(config, mo):
    _species_display = ", ".join(config["species"])
    mo.md(
        f"""
    # {config["title"]}

    This notebook analyzes **all benchmark metrics** across different proteomics software tools.

    **Module:** `{config["module_class"]}`
    **Species:** {_species_display}
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
    import warnings
    from collections import defaultdict
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.io as pio

    # Suppress warnings from proteobench parsing (e.g., MaxQuant proforma warnings)
    warnings.filterwarnings("ignore", category=UserWarning)
    # Suppress pandas FutureWarning about replace() downcasting (from proteobench internals)
    warnings.filterwarnings("ignore", category=FutureWarning, message=".*Downcasting.*")

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

    def create_faceted_boxplot(df, score_col, score_label, title):
        """Create a faceted box plot with precursor counts (top) and score metric (bottom)."""
        color_map = _get_color_map(df)
        sorted_software = sorted(df["software_name"].unique())

        # Melt data to long format for faceting
        df_reset = df.reset_index()
        df_long = df_reset.melt(
            id_vars=["software_name", "dataset_id", "software_version", "enzyme",
                     "enable_match_between_runs", "ident_fdr_psm"],
            value_vars=["n_precursors", score_col],
            var_name="metric_type",
            value_name="value"
        )
        # Rename for display (precursors first so it appears on left)
        metric_labels = {
            "n_precursors": "1. Number of Precursors",
            score_col: f"2. {score_label}"
        }
        df_long["metric_type"] = df_long["metric_type"].map(metric_labels)

        fig = px.box(
            df_long,
            x="software_name",
            y="value",
            color="software_name",
            facet_col="metric_type",
            points="all",
            hover_name="dataset_id",
            hover_data=["software_version", "enzyme", "enable_match_between_runs", "ident_fdr_psm"],
            labels={"value": "", "software_name": "Software"},
            title=title,
            color_discrete_map=color_map,
            category_orders={"software_name": sorted_software},
        )
        fig.update_traces(marker=dict(size=8))
        fig.update_yaxes(matches=None)  # Independent y-axes for each facet
        # Add Y-axis labels for each facet (col 1 = left, col 2 = right in Plotly)
        fig.update_yaxes(title_text="Count", col=1)  # Left facet (precursors)
        fig.update_yaxes(title_text=score_label, col=2)  # Right facet (score)
        fig.update_layout(showlegend=False, autosize=True, height=450)
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
            labels={"software_name": "Software"},
            title=title,
            color_discrete_map=color_map,
        )
        fig.update_traces(marker=dict(size=10))
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text="Number of Precursors")
        fig.update_layout(autosize=True, height=400)
        return fig

    return _get_color_map, create_faceted_boxplot, create_scatter


@app.cell(hide_code=True)
def _(create_faceted_boxplot, create_scatter, mo):
    def create_metric_tabs(df, metrics_config, selected_tab_state=None):
        """Create two linked tab groups: one for boxplots, one for scatterplots.

        Args:
            df: DataFrame with metrics
            metrics_config: List of tuples (metric_col, metric_label, tab_name)
            selected_tab_state: Optional mo.state tuple (get, set) for syncing tabs

        Returns:
            Tuple of (boxplot_tabs, scatter_tabs)
        """
        if len(df) == 0:
            empty = mo.md("**No data to display.**")
            return empty, empty

        boxplot_tabs = {}
        scatter_tabs = {}

        for metric_col, metric_label, tab_name in metrics_config:
            boxplot_tabs[tab_name] = create_faceted_boxplot(
                df, metric_col, metric_label, f"{tab_name}: Distribution"
            )
            scatter_tabs[tab_name] = create_scatter(
                df, metric_col, metric_label, f"{tab_name} vs Precursors"
            )

        # If state provided, create linked tabs; otherwise independent tabs
        if selected_tab_state is not None:
            get_tab, set_tab = selected_tab_state
            return (
                mo.ui.tabs(boxplot_tabs, value=get_tab(), on_change=set_tab),
                mo.ui.tabs(scatter_tabs, value=get_tab(), on_change=set_tab),
            )
        return mo.ui.tabs(boxplot_tabs), mo.ui.tabs(scatter_tabs)

    return (create_metric_tabs,)


@app.cell(hide_code=True)
def _(mo, px):
    def create_bias_improvement_tabs(species_stats_df, metrics_df, weighting="global"):
        """Create 4 tabs: Median Bias, Mean Bias, Median Acc vs Prec, Mean Acc vs Prec.

        Args:
            species_stats_df: DataFrame with per-species stats (for bias plots)
            metrics_df: DataFrame with aggregated metrics (for improvement plots)
            weighting: "global" or "eq_species" to select which epsilon columns to use
        """
        if len(species_stats_df) == 0:
            return mo.md("**No species data available.**")

        def _create_bias_plot(df, bias_col, title):
            """Create single bias boxplot (per-species)."""
            fig = px.box(
                df, x="species", y=bias_col, color="software", points="all",
                hover_data=["dataset_id"],
                labels={"software": "Software", "species": "Species"},
                title=title,
                color_discrete_sequence=px.colors.qualitative.Plotly,
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_yaxes(title_text="Bias (log2 Empirical - Expected)")
            fig.update_layout(autosize=True, height=450)
            return fig

        def _create_acc_vs_prec_plot(mdf, acc_col, prec_col, title):
            """Create single accuracy vs precision comparison boxplot."""
            df_reset = mdf.reset_index()
            df_long = df_reset.melt(
                id_vars=["software_name", "dataset_id"],
                value_vars=[acc_col, prec_col],
                var_name="metric_type",
                value_name="value"
            )
            metric_labels = {
                acc_col: "Accuracy (vs Expected)",
                prec_col: "Precision (vs Empirical)"
            }
            df_long["metric_type"] = df_long["metric_type"].map(metric_labels)

            fig = px.box(
                df_long, x="software_name", y="value", color="metric_type", points="all",
                hover_data=["dataset_id"],
                labels={"software_name": "Software", "metric_type": "Metric"},
                title=title,
                color_discrete_sequence=px.colors.qualitative.Set1,
            )
            fig.update_yaxes(title_text="Absolute Epsilon")
            fig.update_layout(autosize=True, height=450, legend=dict(orientation="h", yanchor="bottom", y=1.02))
            return fig

        # Column names based on weighting
        acc_median = f"median_abs_epsilon_{weighting}"
        prec_median = f"median_abs_epsilon_precision_{weighting}"
        acc_mean = f"mean_abs_epsilon_{weighting}"
        prec_mean = f"mean_abs_epsilon_precision_{weighting}"

        return mo.ui.tabs({
            "Median Bias": _create_bias_plot(species_stats_df, "bias_median", "Bias by Species (Median-based)"),
            "Mean Bias": _create_bias_plot(species_stats_df, "bias_mean", "Bias by Species (Mean-based)"),
            "Median Acc vs Prec": _create_acc_vs_prec_plot(metrics_df, acc_median, prec_median, "Accuracy vs Precision (Median-based)"),
            "Mean Acc vs Prec": _create_acc_vs_prec_plot(metrics_df, acc_mean, prec_mean, "Accuracy vs Precision (Mean-based)"),
        })

    return (create_bias_improvement_tabs,)


@app.cell(hide_code=True)
def _(config, importlib):
    # Dynamic module loading
    from proteobench.datapoint.quant_datapoint import QuantDatapoint
    from proteobench.utils.server_io import get_merged_json, get_raw_data

    mod = importlib.import_module(config["module_import"])
    ModuleClass = getattr(mod, config["module_class"])

    return ModuleClass, QuantDatapoint, get_merged_json, get_raw_data, mod


@app.cell(hide_code=True)
def _(NOTEBOOK_DIR, config, get_merged_json, json, pd, shutil):
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
                except json.JSONDecodeError:
                    pass  # Silently skip invalid JSON files
        if not combined_json:
            raise RuntimeError(f"No valid JSON files found in {json_dir}")
        df_all = pd.DataFrame(combined_json)
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

    return (df_all, repo_name, results_dir)


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
    return OUTPUT_DIR, df_available, df_to_download, get_datasets_to_download, hash_vis_dirs


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
            # Get median-based accuracy and precision from metrics dict
            accuracy_median = metrics_dict.get(f"median_abs_epsilon_{sp}", np.nan)
            precision_median = metrics_dict.get(f"median_abs_epsilon_precision_{sp}", np.nan)
            log2_empirical_median = metrics_dict.get(f"median_log2_empirical_{sp}", np.nan)

            # Get mean-based accuracy and precision from metrics dict
            accuracy_mean = metrics_dict.get(f"mean_abs_epsilon_{sp}", np.nan)
            precision_mean = metrics_dict.get(f"mean_abs_epsilon_precision_{sp}", np.nan)
            log2_empirical_mean = metrics_dict.get(f"mean_log2_empirical_{sp}", np.nan)

            n_prec = metrics_dict.get(f"nr_prec_{sp}", 0)

            if n_prec == 0:
                continue

            # Get expected ratio from results_df
            sp_data = results_df[results_df["species"] == sp]
            log2_expected = (
                sp_data["log2_expectedRatio"].iloc[0] if len(sp_data) > 0 and "log2_expectedRatio" in sp_data.columns
                else np.nan
            )

            # Compute median-based bias and reduction
            bias_median = log2_empirical_median - log2_expected if not (np.isnan(log2_empirical_median) or np.isnan(log2_expected)) else np.nan
            reduction_median = (1 - precision_median / accuracy_median) * 100 if accuracy_median > 0 else np.nan

            # Compute mean-based bias and reduction
            bias_mean = log2_empirical_mean - log2_expected if not (np.isnan(log2_empirical_mean) or np.isnan(log2_expected)) else np.nan
            reduction_mean = (1 - precision_mean / accuracy_mean) * 100 if accuracy_mean > 0 else np.nan

            stats.append({
                "software": software_name,
                "dataset_id": dataset_id,
                "species": sp,
                "n_precursors": n_prec,
                "log2_expected": round(log2_expected, 3) if not np.isnan(log2_expected) else np.nan,
                # Median-based metrics
                "log2_empirical_median": round(log2_empirical_median, 3) if not np.isnan(log2_empirical_median) else np.nan,
                "bias_median": round(bias_median, 3) if not np.isnan(bias_median) else np.nan,
                "median_abs_dev_expected": round(accuracy_median, 4) if not np.isnan(accuracy_median) else np.nan,
                "median_abs_dev_empirical": round(precision_median, 4) if not np.isnan(precision_median) else np.nan,
                "reduction_%_median": round(reduction_median, 1) if not np.isnan(reduction_median) else np.nan,
                # Mean-based metrics
                "log2_empirical_mean": round(log2_empirical_mean, 3) if not np.isnan(log2_empirical_mean) else np.nan,
                "bias_mean": round(bias_mean, 3) if not np.isnan(bias_mean) else np.nan,
                "mean_abs_dev_expected": round(accuracy_mean, 4) if not np.isnan(accuracy_mean) else np.nan,
                "mean_abs_dev_empirical": round(precision_mean, 4) if not np.isnan(precision_mean) else np.nan,
                "reduction_%_mean": round(reduction_mean, 1) if not np.isnan(reduction_mean) else np.nan,
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

                # Compute per-species bias for heatmap (both median and mean based)
                # Bias = log2_empirical - log2_expected (per species)
                for sp in species_list:
                    sp_data = results_performance[results_performance["species"] == sp]
                    if len(sp_data) > 0 and "log2_expectedRatio" in sp_data.columns:
                        log2_exp = sp_data["log2_expectedRatio"].iloc[0]
                        # Median-based bias
                        log2_emp_median = m.get(f"median_log2_empirical_{sp}", np.nan)
                        if not (np.isnan(log2_emp_median) or np.isnan(log2_exp)):
                            result_entry[f"bias_med_{sp}"] = log2_emp_median - log2_exp
                        else:
                            result_entry[f"bias_med_{sp}"] = np.nan
                        # Mean-based bias
                        log2_emp_mean = m.get(f"mean_log2_empirical_{sp}", np.nan)
                        if not (np.isnan(log2_emp_mean) or np.isnan(log2_exp)):
                            result_entry[f"bias_mean_{sp}"] = log2_emp_mean - log2_exp
                        else:
                            result_entry[f"bias_mean_{sp}"] = np.nan
                    else:
                        result_entry[f"bias_med_{sp}"] = np.nan
                        result_entry[f"bias_mean_{sp}"] = np.nan

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
    ## Overview: Score Heatmaps

    Six heatmaps showing benchmark metrics grouped by type, using **raw values** (each group on its own scale).
    Rows are sorted by number of precursors for easier comparison.

    | Heatmap | Metrics | Color Scale | Interpretation |
    |---------|---------|-------------|----------------|
    | **N Precursors** | Count of identified precursors | Blues | Higher (darker) = more IDs = better |
    | **Epsilon (Accuracy)** | Deviation from expected ratio | Reds | Lower (lighter) = better accuracy |
    | **Prec - Acc** | Precision - Accuracy (bias indicator) | RdBu (divergent) | Negative (blue) = precision better = systematic bias |
    | **CV** | Coefficient of variation (4 quantiles) | Oranges | Lower (lighter) = more reproducible |
    | **ROC-AUC** | Species separation (directional) | Greens | Higher (darker) = better discrimination |
    | **Bias** | Per-species bias (median & mean empirical) | RdBu (divergent) | 0 = no bias, red = positive, blue = negative |

    **Improvement interpretation**: Negative values (blue) mean precision < accuracy, i.e., measurements cluster tightly around an empirical center that differs from expected - indicating systematic bias. Values near 0 (white) mean no systematic bias.
    """
    )
    return


@app.cell(hide_code=True)
def _(SOFTWARE_COLOR_MAP, FALLBACK_COLORS, metrics_df, mo, np):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    def _create_grouped_heatmaps(df):
        """Create 6 grouped heatmaps: software colors + 5 metric groups, sorted by n_precursors."""
        if len(df) == 0:
            return mo.md("**No data for heatmaps.**")

        # Compute improvement columns: precision - accuracy (negative = precision better than accuracy = improvement)
        df = df.copy()
        df["improve_med_global"] = df["median_abs_epsilon_precision_global"] - df["median_abs_epsilon_global"]
        df["improve_mean_global"] = df["mean_abs_epsilon_precision_global"] - df["mean_abs_epsilon_global"]
        df["improve_med_eq_species"] = df["median_abs_epsilon_precision_eq_species"] - df["median_abs_epsilon_eq_species"]
        df["improve_mean_eq_species"] = df["mean_abs_epsilon_precision_eq_species"] - df["mean_abs_epsilon_eq_species"]

        # Dynamically detect per-species bias columns
        # Format: bias_med_SPECIES, bias_mean_SPECIES
        bias_med_cols = sorted([c for c in df.columns if c.startswith("bias_med_")])
        bias_mean_cols = sorted([c for c in df.columns if c.startswith("bias_mean_")])
        bias_cols = bias_med_cols + bias_mean_cols
        # Labels: "med:HUMAN", "med:YEAST", ..., "mean:HUMAN", "mean:YEAST", ...
        bias_labels = [c.replace("bias_med_", "med:") for c in bias_med_cols] + \
                      [c.replace("bias_mean_", "mean:") for c in bias_mean_cols]

        # Define metric groups with their columns, labels, and color scales
        # Format: (title, columns, short_labels, colorscale, zmid)
        groups = [
            (
                "N Precursors",
                ["n_precursors"],
                ["N Prec"],
                "Blues",
                None,
            ),
            (
                "Epsilon (Accuracy)",
                [
                    "median_abs_epsilon_global",
                    "mean_abs_epsilon_global",
                    "median_abs_epsilon_eq_species",
                    "mean_abs_epsilon_eq_species",
                ],
                ["Med(G)", "Mean(G)", "Med(ES)", "Mean(ES)"],
                "Reds",
                None,
            ),
            (
                "Prec - Acc",
                [
                    "improve_med_global",
                    "improve_mean_global",
                    "improve_med_eq_species",
                    "improve_mean_eq_species",
                ],
                ["Med(G)", "Mean(G)", "Med(ES)", "Mean(ES)"],
                "RdBu_r",  # Reversed: blue for negative (good), red for positive
                0,  # Divergent scale centered at 0
            ),
            (
                "CV",
                ["CV_median", "CV_q75", "CV_q90", "CV_q95"],
                ["Med", "Q75", "Q90", "Q95"],
                "Oranges",
                None,
            ),
            (
                "ROC-AUC",
                ["roc_auc_directional"],
                ["Dir."],
                "Greens",
                None,
            ),
            (
                "Bias (per species)",
                bias_cols,
                bias_labels,
                "RdBu_r",
                0,  # Divergent scale centered at 0
            ),
        ]

        # Sort by n_precursors ascending so largest appears at top (Plotly renders y[0] at bottom)
        sort_order = df["n_precursors"].argsort()  # Ascending: smallest at bottom, largest at top

        # Create row labels
        row_labels = df["software_name"].astype(str) + " | " + df["dataset_id"].astype(str)
        sorted_labels = row_labels.iloc[sort_order].tolist()

        # Ensure labels are unique by adding index suffix if needed
        seen = {}
        unique_labels = []
        for label in sorted_labels:
            if label in seen:
                seen[label] += 1
                unique_labels.append(f"{label} ({seen[label]})")
            else:
                seen[label] = 0
                unique_labels.append(label)
        sorted_labels = unique_labels

        n_rows = len(df)
        height = max(500, 25 * n_rows)  # More height per row

        # Prepare hover metadata (sorted in same order as rows)
        hover_meta = df[["software_name", "software_version", "enzyme", "enable_match_between_runs", "ident_fdr_psm"]].iloc[sort_order]

        # Build software color mapping for the first column
        # Assign each unique software a numeric index for the heatmap
        software_names_sorted = df["software_name"].iloc[sort_order].tolist()
        unique_software = sorted(set(software_names_sorted))

        # Build color assignment: map software -> index -> color
        software_to_idx = {sw: i for i, sw in enumerate(unique_software)}
        software_indices = np.array([[software_to_idx[sw]] for sw in software_names_sorted])

        # Create discrete colorscale from software colors
        fallback_idx = 0
        software_colors = []
        for sw in unique_software:
            if sw in SOFTWARE_COLOR_MAP:
                software_colors.append(SOFTWARE_COLOR_MAP[sw])
            else:
                software_colors.append(FALLBACK_COLORS[fallback_idx % len(FALLBACK_COLORS)])
                fallback_idx += 1

        # Build discrete colorscale: [(0, color0), (0.5, color0), (0.5, color1), (1, color1), ...]
        n_sw = len(unique_software)
        discrete_colorscale = []
        for i, color in enumerate(software_colors):
            lower = i / n_sw
            upper = (i + 1) / n_sw
            discrete_colorscale.append([lower, color])
            discrete_colorscale.append([upper, color])

        # Create subplots - software color column + metric groups
        col_widths = [0.5] + [max(1, len(g[1])) for g in groups]  # Narrow first column
        fig = make_subplots(
            rows=1,
            cols=len(groups) + 1,
            subplot_titles=["Software"] + [g[0] for g in groups],
            horizontal_spacing=0.02,
            column_widths=col_widths,
        )

        # Add software color heatmap (first column)
        software_customdata = np.array([
            [[row["software_name"], row["software_version"], row["enzyme"],
              row["enable_match_between_runs"], row["ident_fdr_psm"]]]
            for _, row in hover_meta.iterrows()
        ])
        fig.add_trace(
            go.Heatmap(
                z=software_indices,
                x=[""],
                y=sorted_labels,
                colorscale=discrete_colorscale,
                showscale=False,
                customdata=software_customdata,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Software: %{customdata[0][0]}<br>"
                    "Version: %{customdata[0][1]}<br>"
                    "Enzyme: %{customdata[0][2]}<br>"
                    "MBR: %{customdata[0][3]}<br>"
                    "FDR: %{customdata[0][4]}"
                    "<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )
        fig.update_yaxes(tickfont=dict(size=9), row=1, col=1)
        fig.update_xaxes(showticklabels=False, row=1, col=1)

        # Add metric group heatmaps (columns 2+)
        for i, (_, cols, labels, colorscale, zmid) in enumerate(groups):
            col_idx = i + 2  # Offset by 1 for software column

            # Filter to available columns
            available_cols = [c for c in cols if c in df.columns]
            if not available_cols:
                continue

            # Get data and sort
            data = df[available_cols].iloc[sort_order].values
            col_labels = [labels[cols.index(c)] for c in available_cols]
            n_cols = len(available_cols)

            # Build customdata: repeat metadata for each column in the heatmap
            # Shape: (n_rows, n_cols, 4) where 4 = number of metadata fields
            customdata = np.array([
                [[row["software_version"], row["enzyme"],
                  row["enable_match_between_runs"], row["ident_fdr_psm"]] for _ in range(n_cols)]
                for _, row in hover_meta.iterrows()
            ])

            # For divergent scale (bias), compute symmetric range
            if zmid is not None:
                max_abs = np.nanmax(np.abs(data))
                zmin, zmax = -max_abs, max_abs
            else:
                zmin, zmax = None, None

            # Add heatmap - always pass y labels for proper alignment, no colorbar
            heatmap = go.Heatmap(
                z=data,
                x=col_labels,
                y=sorted_labels,  # Always pass y for proper row alignment
                colorscale=colorscale,
                zmid=zmid,
                zmin=zmin,
                zmax=zmax,
                showscale=False,  # No colorbar
                customdata=customdata,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "%{x}: <b>%{z:.4f}</b><br>"
                    "Version: %{customdata[0]}<br>"
                    "Enzyme: %{customdata[1]}<br>"
                    "MBR: %{customdata[2]}<br>"
                    "FDR: %{customdata[3]}"
                    "<extra></extra>"
                ),
            )
            fig.add_trace(heatmap, row=1, col=col_idx)

            # Update axes
            fig.update_xaxes(
                tickangle=-45,
                tickfont=dict(size=9),
                row=1,
                col=col_idx,
            )
            # Hide y-axis tick labels for all columns except first
            fig.update_yaxes(showticklabels=False, row=1, col=col_idx)

        fig.update_layout(
            height=height,
            width=1200,
            showlegend=False,
            margin=dict(l=250, r=50, t=80, b=100),
        )

        # Rotate subplot titles (annotations) by 45 degrees
        for annotation in fig['layout']['annotations']:
            annotation['textangle'] = -45
            annotation['font'] = dict(size=10)

        return fig

    _heatmap_fig = _create_grouped_heatmaps(metrics_df)
    _heatmap_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1. Epsilon Metrics (Global Weighting)

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
    # Shared state for syncing tab selection across tab groups
    get_global_tab, set_global_tab = mo.state("Median Accuracy")
    return get_global_tab, set_global_tab


@app.cell(hide_code=True)
def _(create_metric_tabs, get_global_tab, metrics_df, mo, set_global_tab):
    _global_metrics_config = [
        ("median_abs_epsilon_global", "Median Abs Epsilon (Global)", "Median Accuracy"),
        ("median_abs_epsilon_precision_global", "Median Abs Epsilon Precision (Global)", "Median Precision"),
        ("mean_abs_epsilon_global", "Mean Abs Epsilon (Global)", "Mean Accuracy"),
        ("mean_abs_epsilon_precision_global", "Mean Abs Epsilon Precision (Global)", "Mean Precision"),
    ]
    _boxplot_tabs, _scatter_tabs = create_metric_tabs(
        metrics_df, _global_metrics_config, selected_tab_state=(get_global_tab, set_global_tab)
    )

    mo.vstack([
        mo.md("### Distributions (with Precursor Counts)"),
        _boxplot_tabs,
        mo.md("### Score vs Precursors"),
        _scatter_tabs,
    ])
    return


@app.cell(hide_code=True)
def _(create_bias_improvement_tabs, metrics_df, mo, species_stats_df):
    mo.md("### Bias & Accuracy vs Precision (Global)")
    _bias_tabs = create_bias_improvement_tabs(species_stats_df, metrics_df, weighting="global")
    _bias_tabs
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2. Epsilon Metrics (Equal Species Weighting)

    Unlike global weighting where each precursor contributes equally, **equal species weighting** ensures each species
    contributes equally to the final metric regardless of how many precursors were identified per species.

    This prevents the dominant species (typically HUMAN with more identifications) from overshadowing performance on minority species.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # Shared state for syncing tab selection across equal species tab groups
    get_eq_species_tab, set_eq_species_tab = mo.state("Median Accuracy")
    return get_eq_species_tab, set_eq_species_tab


@app.cell(hide_code=True)
def _(create_metric_tabs, get_eq_species_tab, metrics_df, mo, set_eq_species_tab):
    _eq_species_metrics_config = [
        ("median_abs_epsilon_eq_species", "Median Abs Epsilon (Equal Species)", "Median Accuracy"),
        ("median_abs_epsilon_precision_eq_species", "Median Abs Epsilon Precision (Equal Species)", "Median Precision"),
        ("mean_abs_epsilon_eq_species", "Mean Abs Epsilon (Equal Species)", "Mean Accuracy"),
        ("mean_abs_epsilon_precision_eq_species", "Mean Abs Epsilon Precision (Equal Species)", "Mean Precision"),
    ]
    _boxplot_tabs, _scatter_tabs = create_metric_tabs(
        metrics_df, _eq_species_metrics_config, selected_tab_state=(get_eq_species_tab, set_eq_species_tab)
    )

    mo.vstack([
        mo.md("### Distributions (with Precursor Counts)"),
        _boxplot_tabs,
        mo.md("### Score vs Precursors"),
        _scatter_tabs,
    ])
    return


@app.cell(hide_code=True)
def _(create_bias_improvement_tabs, metrics_df, mo, species_stats_df):
    mo.md("### Bias & Accuracy vs Precision (Equal Species)")
    _bias_tabs = create_bias_improvement_tabs(species_stats_df, metrics_df, weighting="eq_species")
    _bias_tabs
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3. ROC-AUC Metrics: Species Separation

    **Directional ROC-AUC** measures how well software can distinguish between species with different expected fold changes.
    It uses signed fold changes to test both magnitude and direction of change.

    - **ROC-AUC = 1.0**: Perfect separation of changed vs unchanged species
    - **ROC-AUC = 0.5**: Random classification (no discrimination ability)

    Higher values indicate better species separation ability.
    """
    )
    return


@app.cell(hide_code=True)
def _(create_faceted_boxplot, create_scatter, metrics_df, mo):
    if len(metrics_df) == 0:
        _output = mo.md("**No data to display.**")
    else:
        _boxplot = create_faceted_boxplot(
            metrics_df, "roc_auc_directional", "Directional ROC-AUC", "ROC-AUC Distribution"
        )
        _scatter = create_scatter(
            metrics_df, "roc_auc_directional", "Directional ROC-AUC", "ROC-AUC vs Precursors"
        )
        _output = mo.vstack([
            mo.md("### Distribution (with Precursor Counts)"),
            _boxplot,
            mo.md("### ROC-AUC vs Precursors"),
            _scatter,
        ])
    _output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4. CV Metrics: Reproducibility

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
def _(mo):
    # Shared state for syncing tab selection across CV tab groups
    get_cv_tab, set_cv_tab = mo.state("CV Median")
    return get_cv_tab, set_cv_tab


@app.cell(hide_code=True)
def _(create_metric_tabs, get_cv_tab, metrics_df, mo, set_cv_tab):
    _cv_metrics_config = [
        ("CV_median", "CV Median", "CV Median"),
        ("CV_q75", "CV Q75", "CV Q75"),
        ("CV_q90", "CV Q90", "CV Q90"),
        ("CV_q95", "CV Q95", "CV Q95"),
    ]
    _boxplot_tabs, _scatter_tabs = create_metric_tabs(
        metrics_df, _cv_metrics_config, selected_tab_state=(get_cv_tab, set_cv_tab)
    )

    mo.vstack([
        mo.md("### Distributions (with Precursor Counts)"),
        _boxplot_tabs,
        mo.md("### CV vs Precursors"),
        _scatter_tabs,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---

    ## 5. Per-Species Accuracy vs Precision Analysis

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
    ## 6. Accuracy vs Precision Scatter Plot

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
            hover_data=["software", "dataset_id", "bias_median", "reduction_%_median"],
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
    ---

    ## 7. Export Results

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
