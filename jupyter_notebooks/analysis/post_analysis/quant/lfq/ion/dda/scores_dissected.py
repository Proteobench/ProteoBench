# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "plotly",
#     "requests",
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
    # Accuracy vs Precision Analysis

    This notebook compares **accuracy** (deviation from expected ratio) vs **precision** (deviation from empirical center) for each species across all software tools.

    **Key Metrics:**
    - **Accuracy (epsilon)**: `log2_A_vs_B - log2_expectedRatio` - deviation from theoretical ratio
    - **Precision (epsilon_precision)**: `log2_A_vs_B - log2_empirical_median` - deviation from observed center

    **Why this matters:**
    - If accuracy ≈ precision → software is accurate (empirical ≈ expected)
    - If precision << accuracy → systematic bias exists (empirical ≠ expected)
    """
    )
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import numpy as np
    import os
    from pathlib import Path
    from collections import defaultdict
    import plotly.express as px
    import plotly.graph_objects as go

    NOTEBOOK_DIR = Path(__file__).parent

    return NOTEBOOK_DIR, defaultdict, go, np, os, pd, px


@app.cell(hide_code=True)
def _():
    from proteobench.utils.server_io import get_merged_json, get_raw_data
    from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive

    return (
        DDAQuantIonModuleQExactive,
        get_merged_json,
        get_raw_data,
    )


@app.cell(hide_code=True)
def _(get_merged_json, mo):
    df_all = get_merged_json(
        repo_url="https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip"
    )
    mo.md(f"**Loaded {len(df_all)} benchmark results from GitHub**")
    return (df_all,)


@app.cell(hide_code=True)
def _(NOTEBOOK_DIR, df_all, get_raw_data, os):
    OUTPUT_DIR = NOTEBOOK_DIR.resolve() / "temp_results"

    def _get_datasets(df, output_directory):
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

    df_to_download, hash_vis_dirs = _get_datasets(df_all, OUTPUT_DIR)

    if len(df_to_download) > 0:
        hash_vis_dirs_new = get_raw_data(
            df_to_download,
            base_url="https://proteobench.cubimed.rub.de/datasets/",
            output_directory=str(OUTPUT_DIR),
        )
        hash_vis_dirs.update(hash_vis_dirs_new)

    df_available = df_all[df_all["intermediate_hash"].isin(hash_vis_dirs)]
    return df_available, hash_vis_dirs


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Per-Species Accuracy vs Precision

    For each software and species, comparing:
    - **median_abs_dev_expected**: Median |log2_A_vs_B - expected| (accuracy)
    - **median_abs_dev_empirical**: Median |log2_A_vs_B - empirical_median| (precision)
    - **reduction_%**: How much precision improves over accuracy
    """
    )
    return


@app.cell(hide_code=True)
def _(
    DDAQuantIonModuleQExactive,
    defaultdict,
    df_available,
    hash_vis_dirs,
    mo,
    np,
    os,
    pd,
):
    def _compute_species_stats(results_df, software_name, dataset_id):
        """Compute per-species accuracy vs precision stats."""
        if results_df is None or "species" not in results_df.columns:
            return []

        stats = []
        for sp_name in results_df["species"].unique():
            sp_data = results_df[results_df["species"] == sp_name]
            if len(sp_data) == 0:
                continue

            log2_expected = (
                sp_data["log2_expectedRatio"].iloc[0]
                if "log2_expectedRatio" in sp_data.columns
                else np.nan
            )
            log2_empirical = sp_data["log2_A_vs_B"].median()

            # Accuracy: deviation from expected ratio
            accuracy = sp_data["epsilon"].abs().median() if "epsilon" in sp_data.columns else np.nan

            # Precision: deviation from empirical center
            precision = (
                sp_data["epsilon_precision_median"].abs().median()
                if "epsilon_precision_median" in sp_data.columns
                else np.nan
            )

            # Reduction percentage
            reduction = (1 - precision / accuracy) * 100 if accuracy > 0 else np.nan

            stats.append(
                {
                    "software": software_name,
                    "dataset_id": dataset_id,
                    "species": sp_name,
                    "n_precursors": len(sp_data),
                    "log2_expected": round(log2_expected, 3),
                    "log2_empirical_median": round(log2_empirical, 3),
                    "bias": round(log2_empirical - log2_expected, 3),
                    "median_abs_dev_expected": round(accuracy, 4),
                    "median_abs_dev_empirical": round(precision, 4),
                    "reduction_%": round(reduction, 1),
                }
            )
        return stats

    # Process ALL datasets
    all_species_stats = []
    errors = []

    with mo.status.spinner(title="Processing all datasets..."):
        for _, row in df_available.iterrows():
            location = hash_vis_dirs.get(row["intermediate_hash"])
            if not location or not os.path.exists(location):
                continue

            all_files = os.listdir(location)
            matching_files = [f for f in all_files if f.startswith("input_file")]
            if not matching_files:
                continue

            matching_file = os.path.join(location, matching_files[0])
            user_config = defaultdict(lambda: "")
            module_obj = DDAQuantIonModuleQExactive(token="")

            try:
                results_df, _, _ = module_obj.benchmarking(
                    matching_file, row["software_name"], user_input=user_config, all_datapoints=[]
                )
                stats = _compute_species_stats(results_df, row["software_name"], row["id"])
                all_species_stats.extend(stats)
            except Exception as e:
                errors.append(f"{row['id']}: {str(e)[:50]}")

    species_stats_df = pd.DataFrame(all_species_stats)
    mo.md(f"**Processed {len(df_available)} datasets, {len(errors)} errors**")
    return (species_stats_df,)


@app.cell(hide_code=True)
def _(mo, species_stats_df):
    if len(species_stats_df) > 0:
        # Show each dataset separately (not averaged)
        display_df = species_stats_df.sort_values(["software", "species", "dataset_id"])
        table_html = display_df.to_html(index=False, classes="dataframe")
        table_output = mo.vstack([
            mo.md("### Per-Software Per-Species Summary (each dataset)"),
            mo.Html(table_html),
        ])
    else:
        table_output = mo.md("**No data available**")
    table_output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Accuracy vs Precision Scatter Plot

    Each point is one dataset. Faceted by species.
    Points below the diagonal line have better precision than accuracy.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, px, species_stats_df):
    if len(species_stats_df) > 0:
        scatter_fig = px.scatter(
            species_stats_df,
            x="median_abs_dev_expected",
            y="median_abs_dev_empirical",
            color="software",
            facet_col="species",
            hover_data=["software", "dataset_id", "bias", "reduction_%"],
            labels={
                "median_abs_dev_expected": "Accuracy (median |ε expected|)",
                "median_abs_dev_empirical": "Precision (median |ε empirical|)",
            },
            title="Accuracy vs Precision by Species (each point = one dataset)",
            color_discrete_sequence=px.colors.qualitative.Plotly,
        )

        # Add diagonal line to each facet
        max_val = max(
            species_stats_df["median_abs_dev_expected"].max(),
            species_stats_df["median_abs_dev_empirical"].max()
        )
        scatter_fig.add_shape(
            type="line", x0=0, y0=0, x1=max_val, y1=max_val,
            line=dict(dash="dash", color="gray"),
            row="all", col="all"
        )

        scatter_fig.update_layout(height=400)
        scatter_output = scatter_fig
    else:
        scatter_output = mo.md("**No data for scatter plot**")
    scatter_output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Reduction by Species

    Box plot showing reduction percentage (how much precision improves over accuracy) by species.
    Higher reduction = larger bias between expected and empirical ratios.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, px, species_stats_df):
    if len(species_stats_df) > 0:
        box_fig = px.box(
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
        box_fig.update_layout(height=500)
        box_output = box_fig
    else:
        box_output = mo.md("**No data for box plot**")
    box_output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Bias Distribution

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
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Interpretation

    **If reduction is small (< 10%):**
    - The software is **accurate** - empirical centers are close to expected ratios
    - Precision and accuracy measure similar things in this case
    - This is good news for the software!

    **If reduction is large (> 30%):**
    - There's systematic bias between expected and observed ratios
    - Precision removes this bias component
    - Worth investigating why bias exists

    **Key insight:** Small reduction ≠ bug in computation. It means expected ≈ empirical.
    """
    )
    return


if __name__ == "__main__":
    app.run()
