import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import warnings

    warnings.filterwarnings("ignore")
    warnings.simplefilter("ignore")
    import os
    import pathlib
    import pandas as pd
    import numpy as np
    import re
    import upsetplot
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import matplotlib
    import seaborn as sns
    from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
    from proteobench.io.params.alphadia import extract_params as extract_alphadia_params
    from proteobench.io.params.diann import extract_params as extract_diann_params
    from proteobench.io.params.fragger import extract_params as extract_fragpipe_params
    from proteobench.io.params.maxquant import extract_params as extract_maxquant_params
    from proteobench.io.params.msaid import extract_params as extract_msaid_params
    from proteobench.io.params.spectronaut import (
        read_spectronaut_settings as extract_spectronaut_params,
    )
    from proteobench.io.params.peaks import extract_params as extract_peaks_params
    from proteobench.datapoint.quant_datapoint import (
        filter_df_numquant_epsilon,
        filter_df_numquant_nr_prec,
    )
    from proteobench.plotting.plot_quant import PlotDataPoint
    from plotly.subplots import make_subplots
    from proteobench.utils.server_io import get_merged_json, get_raw_data

    from matplotlib.colors import to_rgba

    return (
        DIAQuantIonModuleAstral,
        PlotDataPoint,
        filter_df_numquant_epsilon,
        filter_df_numquant_nr_prec,
        get_merged_json,
        get_raw_data,
        make_subplots,
        matplotlib,
        np,
        pathlib,
        pd,
        plt,
        re,
        sns,
        to_rgba,
        upsetplot,
    )


@app.cell
def _():
    MAPPERS = {
        "FragPipe (DIA-NN quant)": {
            "LFQ_Astral_DIA_15min_50ng_Condition_A_REP1 Intensity": "LFQ_Astral_DIA_15min_50ng_Condition_A_REP1",
            "LFQ_Astral_DIA_15min_50ng_Condition_A_REP2 Intensity": "LFQ_Astral_DIA_15min_50ng_Condition_A_REP1",
            "LFQ_Astral_DIA_15min_50ng_Condition_A_REP3 Intensity": "LFQ_Astral_DIA_15min_50ng_Condition_A_REP3",
            "LFQ_Astral_DIA_15min_50ng_Condition_B_REP1 Intensity": "LFQ_Astral_DIA_15min_50ng_Condition_B_REP1",
            "LFQ_Astral_DIA_15min_50ng_Condition_B_REP2 Intensity": "LFQ_Astral_DIA_15min_50ng_Condition_B_REP2",
            "LFQ_Astral_DIA_15min_50ng_Condition_B_REP3 Intensity": "LFQ_Astral_DIA_15min_50ng_Condition_B_REP3",
        },
    }
    return (MAPPERS,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Download the data
    """)
    return


@app.cell
def _(get_merged_json, get_raw_data):
    # Astral
    Astral_df = get_merged_json(
        repo_url="https://github.com/Proteobench/Results_quant_ion_DIA_Astral/archive/refs/heads/main.zip",
        outfile_name="astral_df.json",
        write_to_file=True,
    )
    hash_dict_astral = get_raw_data(df=Astral_df)
    # diaPASEF
    diaPASEF_df = get_merged_json(
        repo_url="https://github.com/Proteobench/Results_quant_ion_DIA_diaPASEF/archive/refs/heads/main.zip",
        outfile_name="diapasef_df.json",
        write_to_file=True,
    )
    hash_dict_diapasef = get_raw_data(df=diaPASEF_df)
    return Astral_df, diaPASEF_df


@app.cell
def _(Astral_df):
    Astral_df.to_csv(
        "/mnt/d/Proteobench_manuscript_data/supp_tables_manuscript/Astral_df.tsv",
        index=False,
        sep="\t",
    )
    Astral_df
    return


@app.cell
def _(diaPASEF_df):
    diaPASEF_df.to_csv(
        "/mnt/d/Proteobench_manuscript_data/supp_tables_manuscript/diaPASEF_df.tsv",
        index=False,
        sep="\t",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Functions
    """)
    return


@app.cell
def _(DIAQuantIonModuleAstral, pathlib, pd):
    def extract_all_from_hashes(hashes, data_dir="extracted_files", module=DIAQuantIonModuleAstral(token="")):
        """Extract all results from hashes."""
        all_datapoints = pd.DataFrame()
        results_dict = {}
        comments = []

        for point_hash, tool in hashes.items():
            print(f"Processing {point_hash} - {tool}")
            if not tool in results_dict:
                results_dict[tool] = {}

            raw_data_path = f"{data_dir}/{point_hash}/input_file"  # Extension can vary
            param_path = f"{data_dir}/{point_hash}/param_0."  # Extension can vary
            if tool == "AlphaDIA":
                secondary_raw_data_path = f"{data_dir}/{point_hash}/input_file_secondary"  # Extension can vary

            # Identify the correct raw data file extension. There can be only one raw data file per point_hash.
            raw_data_files = list(pathlib.Path(raw_data_path).parent.glob(f"{pathlib.Path(raw_data_path).name}.*"))
            print(f"Raw data files found: {raw_data_files}")
            # Identify the correct parameter file extension. There can be only one parameter file per point_hash.
            param_files = list(pathlib.Path(param_path).parent.glob(f"{pathlib.Path(param_path).name}.*"))
            print(f"Parameter files found: {param_files}")

            if tool == "AlphaDIA":
                secondary_raw_data = list(
                    pathlib.Path(secondary_raw_data_path).parent.glob(f"{pathlib.Path(secondary_raw_data_path).name}.*")
                )
                print(f"Secondary raw data files found: {secondary_raw_data}")
                if not secondary_raw_data:
                    print(
                        f"Skipping {point_hash} - {tool}: Reverting to primary raw data only - No secondary raw data file found."
                    )
                    secondary_raw_data_path = None
                else:
                    secondary_raw_data_path = secondary_raw_data[0]

            if not raw_data_files or not param_files:
                print(f"Skipping {point_hash} - {tool}: No raw data or parameter files found.")
                continue
            raw_data_path = raw_data_files[0]
            param_path = param_files[0]

            if "FragPipe" in tool or "AlphaPept" in tool:
                param_path = open(param_path, "rb")

            extract_params_func = globals()[f"extract_{tool.replace('-', '').lower().replace(' (diann quant)', '')}_params"]
            param_data = extract_params_func(param_path).__dict__
            results_performance, all_datapoints, _ = module.benchmarking(
                raw_data_path,
                tool,
                user_input=param_data,
                all_datapoints=all_datapoints,
                input_file_secondary=secondary_raw_data_path if tool == "AlphaDIA" else None,
            )

            if "MaxQuant" in tool:
                print("adding carbamidos to maxquant")
                results_performance["precursor ion"] = results_performance["precursor ion"].apply(
                    lambda x: x.replace("C", "C[Carbamidomethyl]")
                )

            results_dict[tool][point_hash] = results_performance
        # Set all datapoints to old
        all_datapoints["old_new"] = "old"
        return results_dict, all_datapoints

    return (extract_all_from_hashes,)


@app.cell
def _(
    MAPPERS,
    PlotDataPoint,
    filter_df_numquant_epsilon,
    filter_df_numquant_nr_prec,
    make_subplots,
):
    def prepare_datapoints(all_datapoints, min_quant=3):
        """Filter and calculate metrics for data points."""
        all_datapoints['median_abs_epsilon'] = [filter_df_numquant_epsilon(v, min_quant=min_quant) for v in all_datapoints['results']]
        all_datapoints['nr_prec'] = [filter_df_numquant_nr_prec(v, min_quant=min_quant) for v in all_datapoints['results']]
        return all_datapoints

    def plot_performance_metrics(all_datapoints, min_quant=3, metric='Median', subset=None, x_range=None, y_range=None, subset_col='id'):
        """Plot performance metrics for data points."""
        if subset:
            all_datapoints = all_datapoints[all_datapoints[subset_col].isin(subset)]
        all_datapoints = prepare_datapoints(all_datapoints, min_quant=min_quant)
        _plot = PlotDataPoint.plot_metric(all_datapoints, metric=metric, hide_annot=True)
        _plot.update_layout(xaxis=dict(range=x_range) if x_range else {}, yaxis=dict(range=y_range) if y_range else {})
        return _plot

    def plot_performance_metrics_all_filters(all_datapoints, x_range, y_range, metric='Median', subset=None, subset_col='id'):
        if subset:
            all_datapoints = all_datapoints[all_datapoints[subset_col].isin(subset)]
        plots = []
        for min_quant in range(1, 7):
            datapoints = prepare_datapoints(all_datapoints, min_quant=min_quant)
            _plot = PlotDataPoint.plot_metric(datapoints, metric=metric, hide_annot=True)
            _plot.update_layout(xaxis=dict(range=x_range), yaxis=dict(range=y_range))
            plots.append(_plot)
        combined_fig = make_subplots(rows=2, cols=3, subplot_titles=[f'k={i}' for i in range(1, 7)], vertical_spacing=0.08)
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
        for fig, (r, c) in zip(plots, positions):
            for trace in fig.data:
                combined_fig.add_trace(trace, row=r, col=c)
                combined_fig.update_xaxes(range=x_range, row=r, col=c, tickfont=dict(size=12), title_font=dict(size=12))
                combined_fig.update_yaxes(range=y_range, row=r, col=c, tickfont=dict(size=12), title_font=dict(size=12))
        combined_fig.add_annotation(text=f'{metric.capitalize()}QuantError(k)', x=0.5, y=-0.07, showarrow=False, xref='paper', yref='paper', xanchor='center', yanchor='top', font=dict(size=16))
        combined_fig.add_annotation(text='Depth(k)', x=-0.05, y=0.5, showarrow=False, textangle=-90, xref='paper', yref='paper', xanchor='center', yanchor='bottom', font=dict(size=16))
        combined_fig.update_layout(height=800, width=1200, font=dict(size=12))
        names = set()
        combined_fig.for_each_trace(lambda trace: trace.update(showlegend=False) if trace.name in names else names.add(trace.name))
        return combined_fig

    def prepare_performance_dict(results, mappers=MAPPERS, mapper=None, subset=None):
        """Prepare a dictionary of performance results."""
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}
        print(results)
        performance_dict = {}
        for tool, subdict in results.items():
            print(f'Processing {tool}')
            print(f'Tool has the following runs: {subdict.keys()}')
            for run_name, df in subdict.items():
                print(f'Processing {run_name}')
                if mapper != None:
                    df = df.rename(columns=mappers[mapper])
                elif tool in mappers:
                    tool_mapper = mappers[tool]
                    df = df.rename(columns=tool_mapper)
                df.columns = [x.replace('.mzML', '') for x in df.columns]
                performance_dict[tool] = df
        return performance_dict  # Reduced vertical spacing (default is 0.1)  # Set tick font size  # Set axis title font size  # Add central x and y axis labels as annotations  # General layout configuration  # Sets font size for legend, titles, and annotations  # Remove duplicate legend items

    return (
        plot_performance_metrics,
        plot_performance_metrics_all_filters,
        prepare_performance_dict,
    )


@app.cell
def _(matplotlib, pd, plt, re, sns, upsetplot):
    def filter_upset_data(data, tools):
        # Filter the data so that only subsets are plotted that contain sequences from all tools, from all-but-one tool, or from only one tool
        data_index_reset = data.reset_index()
        ids = data_index_reset["id"]
        occurrences = data_index_reset.drop(columns="id")
        occurrences = occurrences.astype(int)
        row_sums = occurrences.sum(axis=1)
        # Turn row_sums into a dataframe
        row_sums = pd.DataFrame(row_sums)
        row_sums = row_sums.rename(columns={0: "Number of tools"})
        row_sums["id"] = ids
        print("number of precursor ions before filtering:")
        print(len(data_index_reset))
        filtered_data = data_index_reset[
            (row_sums["Number of tools"] == len(tools))
            | (row_sums["Number of tools"] == len(tools) - 1)
            | (row_sums["Number of tools"] == 1)
        ]
        filtered_data = filtered_data.set_index(tools)
        return filtered_data


    def add_epsilons(data, df_dict):
        # Store the original index
        data_index = data.index
        # Reset the index so that the id column is available for merging
        data = data.reset_index()

        for tool, df in df_dict.items():
            # Merge the id column from df with the epsilon column from tool_df
            print(tool)
            data = data.merge(
                df[["precursor ion", "epsilon"]],
                left_on="id",
                right_on="precursor ion",
                how="left",
            )
            # data.to_csv(f"analysis_debug/{tool}_epsilon.csv")

            data = data.rename(columns={"epsilon": f"{tool}_epsilon"})
            data = data.drop(columns=["precursor ion"])

        # Set the index back to the original index
        data = data.set_index(data_index.names)
        return data


    def upsetplot_from_df_dict(df_dict):
        sequence_dict = {}
        for tool, df in df_dict.items():
            # Each df should have a "sequence" column
            unique_sequences = df["precursor ion"].unique()
            # Store the sequences in a list and add it to the dictionary
            sequence_dict[tool] = set(unique_sequences)

        # Create the upset plot
        sequences = upsetplot.from_contents(sequence_dict)
        tools = list(df_dict.keys())
        filtered_sequences = filter_upset_data(sequences, tools)
        data_with_epsilons = add_epsilons(filtered_sequences, df_dict)

        return data_with_epsilons


    def plot_boxplot(boxplot_data, ax, i=1):
        boxplot_data["absolute epsilon"] = boxplot_data["epsilon"].abs()

        # Draw the stripplot with a custom palette
        sns.boxplot(
            data=boxplot_data,
            x="workflow",
            y="absolute epsilon",
            hue="quantified by",
            ax=ax,
            showfliers=False,
            linewidth=1,
        )
        # sns.violinplot(data=boxplot_data, x="tool", y="epsilon", hue = "unique or all", ax=ax, inner=None, linewidth=1)

        # Add the number of observations to each boxplot

        # Improve aesthetics of labels and title
        ax.set_ylabel("AbsQuantError({})".format(i), fontsize=7, fontweight="bold")
        # rotate
        # ax.set_xticklabels(ax.get_xticklabels(), rotation=20, horizontalalignment="right")

        # Add subtle grid lines to enhance readability
        ax.yaxis.grid(True, linestyle="--", color="gray", alpha=0.7)
        ax.xaxis.grid(False)  # Only y-axis grid for cleaner look

        # make y label bigger
        ax.yaxis.label.set_size(12)

        # Hide the legend
        ax.legend_.remove()
        # Add a tighter layout for better spacing
        plt.tight_layout()


    def strip_peptidoform(peptidoform):
        no_mods = re.sub(r"\[.*?\]", "", peptidoform)
        no_mods = no_mods.replace("-", "")
        return no_mods


    def filter_df(df):
        df["precursor ion"] = df["precursor ion"].apply(strip_peptidoform)
        df.drop_duplicates(subset="precursor ion", inplace=True, keep="first")
        return df


    def plot_upset_and_boxplot(df_dict, mapper, stripped=False):

        if stripped:
            df_dict_copy = df_dict.copy()
            df_dict_copy = {key: filter_df(val) for key, val in df_dict_copy.items()}

        else:
            df_dict_copy = df_dict.copy()

        boxplotdata = upsetplot_from_df_dict(df_dict_copy)
        fig, ax_upset = plt.subplots(1, 1, figsize=(7, 3))

        # plot upset plot
        matplotlib.rcParams.update({"font.size": 10})
        upset = upsetplot.UpSet(
            boxplotdata,
            subset_size="count",
            include_empty_subsets=False,
            sort_categories_by="input",
        )
        upset.style_subsets(min_degree=1, facecolor="#3274A1")
        upset.style_subsets(min_degree=2, facecolor="black")
        upset.style_subsets(min_degree=6, facecolor="#E1812C")
        upset.plot(fig=fig)
        ax_upset.grid(False)

        # Hide x-axis label and ticks
        ax_upset.set_xlabel("")
        ax_upset.set_xticks([])
        ax_upset.set_ylabel("")
        ax_upset.set_yticks([])

        # Hide the box
        ax_upset.spines["top"].set_visible(False)
        ax_upset.spines["right"].set_visible(False)
        ax_upset.spines["left"].set_visible(False)
        ax_upset.spines["bottom"].set_visible(False)

        for text in fig.findobj(match=plt.Text):
            text.set_fontsize(8)

        # color the same as boxplot

        # plot boxplot, sorted the same way as the upset plot
        boxplotdata = boxplotdata.reset_index()

        # this needs to be adapted to the number of tools... currently hardcoded :( sorry
        boxplotdata["index_list"] = boxplotdata[boxplotdata.columns[:6]].values.tolist()

        boxplotdata["eval"] = boxplotdata["index_list"].apply(str).map(mapper)

        # drop all ions that are neither all or unique
        boxplotdata = boxplotdata.dropna(subset=["eval"])
        boxplotdata.to_csv("boxplotdata.csv")
        epsilon_cols = [col for col in boxplotdata.columns if "_epsilon" in col]
        important_cols = epsilon_cols + ["eval"]
        boxplotdata = boxplotdata[important_cols]

        boxplotdata["eval"] = pd.Categorical(boxplotdata["eval"], categories=mapper.values(), ordered=True)
        boxplotdata = boxplotdata.sort_values("eval")

        # turn to long format for plotting
        boxplotdata_final = pd.DataFrame()
        for col in epsilon_cols:
            temp = boxplotdata[["eval", col]]
            tool = col.split("_epsilon")[0]
            ions = temp[(temp["eval"] == tool) | (temp["eval"] == "all")]
            ions["quantified by"] = ions["eval"].apply(lambda x: "all" if x == "all" else "unique")
            ions["workflow"] = tool
            ions = ions.rename(columns={col: "epsilon"})
            ions = ions.drop(columns=["eval"]).reset_index(drop=True)
            boxplotdata_final = pd.concat([boxplotdata_final, ions])

        boxplotdata_final.reset_index(drop=True, inplace=True)

        # Set the style
        fig, box_ax = plt.subplots(figsize=(10, 6))
        fig_box = plot_boxplot(boxplotdata_final, ax=box_ax)
        plt.show()
        return fig, fig_box


    def plot_upset_and_boxplot_all_filters(df_dict, mapper, save_path="figures_manuscript/"):

        for i in range(1, 7):

            # filter the df dict
            df_dict_filtered = {key: value[value["nr_observed"] >= i] for key, value in df_dict.items()}

            boxplotdata = upsetplot_from_df_dict(df_dict_filtered)
            # boxplotdata.to_csv("analysis/boxplotdata_min_quant_" + str(i) + ".csv")
            fig, ax_upset = plt.subplots(1, 1, figsize=(7, 3))

            # plot upset plot
            matplotlib.rcParams.update({"font.size": 10})
            upset = upsetplot.UpSet(
                boxplotdata,
                subset_size="count",
                include_empty_subsets=False,
                sort_categories_by="input",
                show_counts=False,
            )
            upset.style_subsets(min_degree=1, facecolor="#3274A1")
            upset.style_subsets(min_degree=2, facecolor="black")
            upset.style_subsets(min_degree=5, facecolor="#E1812C")
            upset.plot(fig=fig)
            # Save the upset plot

            ax_upset.grid(False)
            # Hide x-axis label and ticks
            ax_upset.set_xlabel("")
            ax_upset.set_xticks([])
            ax_upset.set_ylabel("")
            ax_upset.set_yticks([])
            # Hide the box
            ax_upset.spines["top"].set_visible(False)
            ax_upset.spines["right"].set_visible(False)
            ax_upset.spines["left"].set_visible(False)
            ax_upset.spines["bottom"].set_visible(False)

            for text in fig.findobj(match=plt.Text):
                text.set_fontsize(8)

            fig.savefig(
                save_path + f"upset_plot_min_quant_{i}.svg",
            )

            n_tools = int((len(mapper.keys()) - 1) / 2)
            # plot boxplot, sorted the same way as the upset plot
            boxplotdata = boxplotdata.reset_index()

            boxplotdata["index_list"] = boxplotdata[boxplotdata.columns[:n_tools]].values.tolist()
            boxplotdata["eval"] = boxplotdata["index_list"].apply(str).map(mapper)

            # # drop all ions that are neither all or unique
            # boxplotdata = boxplotdata.dropna(subset=["eval"])
            epsilon_cols = [col for col in boxplotdata.columns if "_epsilon" in col]
            important_cols = epsilon_cols + ["eval"]
            boxplotdata = boxplotdata[important_cols]

            boxplotdata["eval"] = pd.Categorical(boxplotdata["eval"], categories=mapper.values(), ordered=True)
            boxplotdata = boxplotdata.sort_values("eval")

            # turn to long format for plotting
            boxplotdata_final = pd.DataFrame()
            for col in epsilon_cols:
                temp = boxplotdata[["eval", col]]
                tool = col.split("_epsilon")[0]
                ions = temp[(temp["eval"] == tool) | (temp["eval"] == "all")]
                ions["quantified by"] = ions["eval"].apply(lambda x: "all" if x == "all" else "unique")
                ions["workflow"] = tool
                ions = ions.rename(columns={col: "epsilon"})
                ions = ions.drop(columns=["eval"]).reset_index(drop=True)
                boxplotdata_final = pd.concat([boxplotdata_final, ions])

            boxplotdata_final.reset_index(drop=True, inplace=True)
            # Save the boxplot data
            # boxplotdata_final.to_csv("analysis/boxplotdata_final_min_quant_" + str(i) + ".csv")

            # Set the style
            fig, box_ax = plt.subplots(figsize=(10, 6))
            fig_box = plot_boxplot(boxplotdata_final, ax=box_ax, i=i)
            plt.title("Min. quantified ions: " + str(i))
            plt.savefig(save_path + f"boxplot_min_quant_{i}.svg")
            plt.show()
        return fig, fig_box

    return (plot_upset_and_boxplot_all_filters,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Module overviews
    """)
    return


@app.cell
def _(Astral_df):
    relevant_points_Astral = (
        Astral_df[~Astral_df["software_name"].isin(["MaxQuant"])][["software_name", "intermediate_hash"]]
        .set_index("intermediate_hash")
        .to_dict()["software_name"]
    )
    return (relevant_points_Astral,)


@app.cell
def _(
    DIAQuantIonModuleAstral,
    extract_all_from_hashes,
    relevant_points_Astral,
):
    results_dict, all_datapoints = extract_all_from_hashes(
        relevant_points_Astral,
        data_dir="extracted_files",
        module=DIAQuantIonModuleAstral(token=""),
    )
    return all_datapoints, results_dict


@app.cell
def _(all_datapoints):
    all_datapoints
    return


@app.cell
def _():
    bounds_x = [0.156 - (0.156 * 0.05), 0.338 + (0.338 * 0.05)]
    bounds_y = [68000 - (68000 * 0.05), 132000 + (132000 * 0.05)]
    return bounds_x, bounds_y


@app.cell
def _(all_datapoints, bounds_x, bounds_y, plot_performance_metrics):
    _plot = plot_performance_metrics(all_datapoints, metric='Median', x_range=bounds_x, y_range=bounds_y, min_quant=3)
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_median_performance.svg')
    _plot
    return


@app.cell
def _():
    bounds_x_1 = [0.232 - 0.236 * 0.05, 0.53 + 0.53 * 0.05]
    bounds_y_1 = [68000 - 68000 * 0.05, 132000 + 132000 * 0.05]
    return bounds_x_1, bounds_y_1


@app.cell
def _(all_datapoints, bounds_x_1, bounds_y_1, plot_performance_metrics):
    _plot = plot_performance_metrics(all_datapoints, metric='Mean', x_range=bounds_x_1, y_range=bounds_y_1, min_quant=3)
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_mean_performance.svg')
    _plot
    return


@app.cell
def _():
    bounds_x_2 = [0.127 - 0.127 * 0.05, 0.342 + 0.342 * 0.05]
    bounds_y_2 = [38000 - 38000 * 0.08, 176500 + 176500 * 0.05]
    return bounds_x_2, bounds_y_2


@app.cell
def _(
    all_datapoints,
    bounds_x_2,
    bounds_y_2,
    plot_performance_metrics_all_filters,
):
    _plot = plot_performance_metrics_all_filters(all_datapoints, x_range=bounds_x_2, y_range=bounds_y_2, metric='Median')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_median_performance_all_filters.svg')
    _plot
    return


@app.cell
def _():
    bounds_x_3 = [0.22 - 0.22 * 0.05, 0.529 + 0.529 * 0.05]
    bounds_y_3 = [40000 - 40000 * 0.08, 176500 + 176500 * 0.05]
    return bounds_x_3, bounds_y_3


@app.cell
def _(
    all_datapoints,
    bounds_x_3,
    bounds_y_3,
    plot_performance_metrics_all_filters,
):
    _plot = plot_performance_metrics_all_filters(all_datapoints, x_range=bounds_x_3, y_range=bounds_y_3, metric='Mean')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_mean_performance_all_filters.svg')
    _plot
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Default settings, compare search engines
    """)
    return


@app.cell
def _(all_datapoints):
    all_datapoints
    return


@app.cell
def _():
    subset_hashes = [
        "b59c34881a1422f106478ac6d76238abb94a8c98",  # Spectronaut
        "d1812ee72c26966b4e3dabe820f7c1e563ebac7d",  # PEAKS
        "1cd54fe0ba5d6c98ef47688414c4f4c409a6eecf",  # FragPipe
        "6af1bb146c324c62d52a14daa19c2749d22ab519",  # DIA-NN
        "a1126afaaab3ecca77f373e730992f3239a5899d",  # AlphaDIA
    ]
    return (subset_hashes,)


@app.cell
def _(all_datapoints, plot_performance_metrics, subset_hashes):
    _plot = plot_performance_metrics(all_datapoints, subset=subset_hashes, min_quant=3, subset_col='intermediate_hash')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_median_performance_subset.svg')
    _plot
    return


@app.cell
def _(all_datapoints, plot_performance_metrics, subset_hashes):
    _plot = plot_performance_metrics(all_datapoints, metric='Mean', subset=subset_hashes, min_quant=3, subset_col='intermediate_hash')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_mean_performance_subset.svg')
    _plot
    return


@app.cell
def _(all_datapoints, plot_performance_metrics_all_filters, subset_hashes):
    _plot = plot_performance_metrics_all_filters(all_datapoints, x_range=[0.15, 0.35], y_range=[0, 160000], metric='Median', subset=subset_hashes, subset_col='intermediate_hash')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_median_performance_all_filters_subset.svg')
    _plot
    return


@app.cell
def _(all_datapoints, plot_performance_metrics_all_filters, subset_hashes):
    _plot = plot_performance_metrics_all_filters(all_datapoints, x_range=[0, 0.8], y_range=[0, 160000], metric='Mean', subset=subset_hashes, subset_col='intermediate_hash')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/astral_mean_performance_all_filters_subset.svg')
    _plot
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Intersection between all the search engines: How do the unique quantifications perform?
    """)
    return


@app.cell
def _():
    # subset_hashes = [
    #     "b59c34881a1422f106478ac6d76238abb94a8c98",  # Spectronaut
    #     "d1812ee72c26966b4e3dabe820f7c1e563ebac7d",  # PEAKS
    #     "1cd54fe0ba5d6c98ef47688414c4f4c409a6eecf",  # FragPipe
    #     "c572ba8406c3a04d30b2f4e3c29ae6fb9328fede",  # DIA-NN
    #     "05de113fc6f5c645f059c3d68dda0d25920f4fd9",  # AlphaDIA
    # ]
    subset_hashes_1 = ['c572ba8406c3a04d30b2f4e3c29ae6fb9328fede', '887471e3771f74d27eff4f7f89b34e9fde53214a', '649792bdaf1bb9e371d5c261dc7bfd7d42a84df6', '1cd54fe0ba5d6c98ef47688414c4f4c409a6eecf', 'a1126afaaab3ecca77f373e730992f3239a5899d']  # DIA-NN  # Spectronaut  # PEAKS  # FragPipe  # AlphaDIA
    return (subset_hashes_1,)


@app.cell
def _(Astral_df, subset_hashes_1):
    Astral_df_subset = Astral_df[Astral_df['intermediate_hash'].isin(subset_hashes_1)].copy()
    return


@app.cell
def _():
    all_tools_mapper = {
        "[True, False, False, False, False]": "AlphaDIA",
        "[False, True, False, False, False]": "FragPipe (DIA-NN quant)",
        "[False, False, True, False, False]": "DIA-NN",
        "[False, False, False, True, False]": "Spectronaut",
        "[False, False, False, False, True]": "PEAKS",
        "[False, True, True, True, True]": "all but AlphaDIA",
        "[True, False, True, True, True]": "all but FragPipe (DIA-NN quant)",
        "[True, True, False, True, True]": "all but DIA-NN",
        "[True, True, True,  False, True]": "all but Spectronaut",
        "[True, True, True, True, False]": "all but PEAKS",
        "[True, True, True, True, True]": "all",
    }
    return (all_tools_mapper,)


@app.cell
def _(prepare_performance_dict, results_dict, subset_hashes_1):
    performance_df_dict = prepare_performance_dict(results_dict, mapper=None, subset=subset_hashes_1)
    return (performance_df_dict,)


@app.cell
def _(performance_df_dict):
    performance_df_dict.keys()
    return


@app.cell
def _(
    all_tools_mapper,
    performance_df_dict,
    plot_upset_and_boxplot_all_filters,
):
    fig = plot_upset_and_boxplot_all_filters(
        performance_df_dict, all_tools_mapper, save_path="/mnt/d/Proteobench_manuscript_data/figures_manuscript/"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A look at precursor quantification for e.coli and yeast precursors
    """)
    return


@app.cell
def _(np, pd, plt, sns, to_rgba):
    def plot_pair_quantifications(
        results,
        subset,
    ):
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}

        lprec = {}
        for tool, subdict in results.items():
            for hashe, df in subdict.items():
                precursors = df["precursor ion"].unique()
                lprec[hashe] = precursors

        # prepare the data for the pair plot
        lplot = []
        for i, (tool, subdict) in enumerate(results.items()):
            for hashe, df in subdict.items():
                res = df[["precursor ion", "log2_A_vs_B", "species"]].copy()
                res["tool"] = tool
                lplot.append(res)

        gtab = pd.concat(lplot, ignore_index=True)
        gtab_wide = gtab.pivot_table(index=["species", "precursor ion"], columns="tool", values="log2_A_vs_B")

        # Get limits for the plots
        lims = np.max(np.abs(gtab[gtab["species"].isin(["ECOLI", "YEAST"])]["log2_A_vs_B"].dropna()))
        lims = (-lims, lims)

        # Create the pair plot for E. coli
        ecoli = gtab_wide[gtab_wide.index.get_level_values("species") == "ECOLI"].reset_index()
        g = sns.pairplot(ecoli.drop(columns=["species", "precursor ion"]), plot_kws={"alpha": 0.1})

        # Apply same axis limits to all subplots in E. coli pairplot
        for i, ax in enumerate(g.axes.flatten()):
            # Skip the diagonal subplots (i.e., where row == column)
            if not i % len(g.axes) == i // len(g.axes):  # Diagonal check
                ax.axhline(y=-2, linestyle="--", linewidth=0.5)
            ax.set_xlim(lims)
            ax.set_ylim(lims)
            ax.axvline(x=-2, linestyle="--", linewidth=0.5)

        plt.suptitle("E. coli Pairplot")
        plt.tight_layout()
        plt.show()

        # Plot for yeast
        yeast = gtab_wide[gtab_wide.index.get_level_values("species") == "YEAST"].reset_index()
        g = sns.pairplot(yeast.drop(columns=["species", "precursor ion"]), plot_kws={"alpha": 0.1})

        # Apply same axis limits to all subplots in Yeast pairplot
        for i, ax in enumerate(g.axes.flatten()):
            # Skip the diagonal subplots (i.e., where row == column)
            if not i % len(g.axes) == i // len(g.axes):  # Diagonal check
                ax.axhline(y=1, linestyle="--", linewidth=0.5)
            ax.set_xlim(lims)
            ax.set_ylim(lims)
            ax.axvline(x=1, linestyle="--", linewidth=0.5)

        plt.suptitle("Yeast Pairplot")
        plt.tight_layout()
        plt.show()


    def plot_pair_quantifications_combined(results, subset=None):
        """
        Create a combined pair plot comparing log2(A vs B) fold-changes across multiple tools
        using E. coli (lower triangle) and Yeast (upper triangle) precursor ions.

        Parameters:
            results (dict): Dictionary mapping tool name -> dict of {hash -> DataFrame} with
                            columns ['precursor ion', 'log2_A_vs_B', 'species'].
            subset (list, optional): List of tool names to include in the plot.
        """
        # Filter hashes
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}

        tools = list(results.keys())

        # Aggregate DataFrames per tool
        tool_data = {}
        for tool in tools:
            dfs = [df.copy() for df in results[tool].values()]
            tool_data[tool] = pd.concat(dfs, ignore_index=True)

        # Extract species-specific data for each tool, indexed by precursor ion
        e_coli_vals = {}
        yeast_vals = {}
        for tool, df in tool_data.items():
            ecoli_df = df[df["species"].str.upper() == "ECOLI"]
            yeast_df = df[df["species"].str.upper() == "YEAST"]
            e_coli_vals[tool] = ecoli_df.set_index("precursor ion")["log2_A_vs_B"]
            yeast_vals[tool] = yeast_df.set_index("precursor ion")["log2_A_vs_B"]

        # Determine global log2 limits
        all_vals = pd.concat([s.dropna() for d in [e_coli_vals, yeast_vals] for s in d.values()])
        lim = np.ceil(np.percentile(np.abs(all_vals), 99.5)) * 1.1 if not all_vals.empty else 1.0

        # Colors
        col_ecoli = "#1f77b4"
        col_yeast = "#ff7f0e"

        n = len(tools)
        fig, axes = plt.subplots(n, n, figsize=(3 * n, 3 * n))

        for i in range(n):
            for j in range(n):
                ax = axes[i, j]
                tool_i = tools[i]
                tool_j = tools[j]

                if i == j:
                    ec_vals = e_coli_vals[tool_i].dropna()
                    yt_vals = yeast_vals[tool_i].dropna()
                    if not ec_vals.empty:
                        sns.kdeplot(ec_vals, ax=ax, color=col_ecoli, fill=True, alpha=0.4)
                    if not yt_vals.empty:
                        sns.kdeplot(yt_vals, ax=ax, color=col_yeast, fill=True, alpha=0.4)
                    ax.axvline(-2, linestyle="--", color=col_ecoli, lw=1)
                    ax.axvline(1, linestyle="--", color=col_yeast, lw=1)
                    ax.set_xlim(-lim, lim)
                    if not i == 0:
                        ax.yaxis.set_visible(False)
                    if not j == n - 1:
                        ax.xaxis.set_visible(False)

                elif i > j:  # E. coli: lower triangle
                    ax.set_facecolor(to_rgba(col_ecoli, alpha=0.1))
                    x = e_coli_vals[tool_j]
                    y = e_coli_vals[tool_i]
                    common = x.index.intersection(y.index)
                    ax.scatter(x.loc[common], y.loc[common], color=col_ecoli, alpha=0.3, s=10)
                    ax.axhline(-2, linestyle="--", color="gray", lw=0.8)
                    ax.axvline(-2, linestyle="--", color="gray", lw=0.8)
                    ax.set_xlim(-lim, lim)
                    ax.set_ylim(-lim, lim)

                else:  # Yeast: upper triangle
                    ax.set_facecolor(to_rgba(col_yeast, alpha=0.1))
                    x = yeast_vals[tool_j]
                    y = yeast_vals[tool_i]
                    common = x.index.intersection(y.index)
                    ax.scatter(x.loc[common], y.loc[common], color=col_yeast, alpha=0.3, s=10)
                    ax.axhline(1, linestyle="--", color="gray", lw=0.8)
                    ax.axvline(1, linestyle="--", color="gray", lw=0.8)
                    ax.set_xlim(-lim, lim)
                    ax.set_ylim(-lim, lim)

                # Clean ticks
                if i < n - 1:
                    ax.set_xticks([])
                else:
                    ax.set_xlabel(tool_j)
                if j > 0:
                    ax.set_yticks([])
                else:
                    ax.set_ylabel(tool_i)

        # Final layout and legend
        fig.legend(
            handles=[
                plt.Line2D([0], [0], color=col_ecoli, lw=4, label="E. coli"),
                plt.Line2D([0], [0], color=col_yeast, lw=4, label="Yeast"),
            ],
            loc="upper right",
            bbox_to_anchor=(1.09, 0.99),
            title="Species",
        )
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(
            "/mnt/d/Proteobench_manuscript_data/figures_manuscript/pair_quantifications_combined.png",
            bbox_inches="tight",
            dpi=600,
        )
        plt.show()

    return (plot_pair_quantifications_combined,)


@app.cell
def _(plot_pair_quantifications_combined, results_dict, subset_hashes_1):
    plot_pair_quantifications_combined(results_dict, subset=subset_hashes_1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Comparison with diaPASEF
    """)
    return


@app.cell
def _():
    from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import (
        DIAQuantIonModulediaPASEF,
    )

    diapasef_module = DIAQuantIonModulediaPASEF("token")
    return (diapasef_module,)


@app.cell
def _(diaPASEF_df):
    relevant_points_diapasef = (
        diaPASEF_df[~diaPASEF_df["software_name"].isin(["MaxQuant"])][["software_name", "intermediate_hash"]]
        .set_index("intermediate_hash")
        .to_dict()["software_name"]
    )
    return (relevant_points_diapasef,)


@app.cell
def _(diapasef_module, extract_all_from_hashes, relevant_points_diapasef):
    results_dict_diaPASEF, all_datapoints_diaPASEF = extract_all_from_hashes(
        relevant_points_diapasef,
        data_dir="extracted_files",
        module=diapasef_module,
    )
    return (all_datapoints_diaPASEF,)


@app.cell
def _(all_datapoints_diaPASEF):
    all_datapoints_diaPASEF
    return


@app.cell
def _():
    subset_hashes_diapasef = [
        "85a7f4eea2244c7ea4db1407d56e62fdb1385964",  # DIA-NN, corresponds to e24e82b93910c326f524d49f844c36024e016076 in all_datapoints_diaPASEF
        "829432aa5955a64d185144843588afc2c3610de6",  # Spectronaut
        "b0a37efafe69c5c846f772305c06bad61410898b",  # PEAKS
        "8f9c72a7c277c7d0ab08b7ffc1f4e9213702220d",  # AlphaDIA
        "fdad2a4d2e6fe409bbbb0ed2d6644ee100e288ba",
    ]
    return


@app.cell
def _():
    x_bounds = [0.120 - (0.120 * 0.05), 0.25 + (0.25 * 0.05)]
    y_bounds = [70000 - (70000 * 0.05), 126486 + (126486 * 0.05)]
    return x_bounds, y_bounds


@app.cell
def _(diaPASEF_df):
    diaPASEF_df
    return


@app.cell
def _(all_datapoints_diaPASEF):
    all_datapoints_diaPASEF
    return


@app.cell
def _(all_datapoints_diaPASEF, plot_performance_metrics, x_bounds, y_bounds):
    _plot = plot_performance_metrics(all_datapoints_diaPASEF, x_range=x_bounds, y_range=y_bounds, metric='Median', min_quant=3)
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/diapasef_median_performance.svg')
    _plot
    return


@app.cell
def _():
    x_bounds_1 = [0.203 - 0.203 * 0.05, 0.344 + 0.344 * 0.05]
    y_bounds_1 = [80697 - 80697 * 0.05, 126486 + 126486 * 0.05]
    return x_bounds_1, y_bounds_1


@app.cell
def _(
    all_datapoints_diaPASEF,
    plot_performance_metrics,
    x_bounds_1,
    y_bounds_1,
):
    _plot = plot_performance_metrics(all_datapoints_diaPASEF, x_range=x_bounds_1, y_range=y_bounds_1, metric='Mean', min_quant=3)
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/diaPASEF_mean_performance.svg')
    _plot
    return


@app.cell
def _():
    x_bounds_2 = [0.1 - 0.1 * 0.05, 0.223 + 0.223 * 0.05]
    y_bounds_2 = [50000 - 50000 * 0.05, 146000 + 146000 * 0.05]
    return x_bounds_2, y_bounds_2


@app.cell
def _(
    all_datapoints_diaPASEF,
    plot_performance_metrics_all_filters,
    x_bounds_2,
    y_bounds_2,
):
    _plot = plot_performance_metrics_all_filters(all_datapoints_diaPASEF, x_range=x_bounds_2, y_range=y_bounds_2, metric='Median')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/diapasef_median_performance_all_filters.svg')
    _plot
    return


@app.cell
def _():
    x_bounds_3 = [0.15 - 0.15 * 0.05, 0.5 + 0.5 * 0.05]
    y_bounds_3 = [50000 - 50000 * 0.05, 148000 + 148000 * 0.05]
    return x_bounds_3, y_bounds_3


@app.cell
def _(
    all_datapoints_diaPASEF,
    plot_performance_metrics_all_filters,
    x_bounds_3,
    y_bounds_3,
):
    _plot = plot_performance_metrics_all_filters(all_datapoints_diaPASEF, x_range=x_bounds_3, y_range=y_bounds_3, metric='Mean')
    _plot.write_image('/mnt/d/Proteobench_manuscript_data/figures_manuscript/diapasef_mean_performance_all_filters.svg')
    _plot
    return


if __name__ == "__main__":
    app.run()
