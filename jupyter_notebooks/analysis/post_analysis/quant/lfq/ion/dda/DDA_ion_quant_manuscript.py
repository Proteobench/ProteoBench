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
    from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive
    from proteobench.io.params.fragger import extract_params as extract_fragpipe_params
    from proteobench.io.params.i2masschroq import extract_params as extract_i2masschroq_params
    from proteobench.io.params.maxquant import extract_params as extract_maxquant_params
    from proteobench.io.params.sage import extract_params as extract_sage_params
    from proteobench.io.params.alphapept import extract_params as extract_alphapept_params
    from proteobench.io.params.proline import extract_params as extract_proline_params
    from proteobench.io.params.wombat import extract_params as extract_wombat_params
    from proteobench.io.params.msangel import extract_params as extract_msangel_params
    from proteobench.io.params.quantms import extract_params as extract_quantms_params
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
        DDAQuantIonModuleQExactive,
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
        "FragPipe": {
            "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01 Intensity": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01",
            "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02 Intensity": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02",
            "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03 Intensity": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03",
            "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01 Intensity": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01",
            "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02 Intensity": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02",
            "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03 Intensity": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03",
        },
        "FragPipeMBR": {
            "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01 Intensity": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01",
            "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02 Intensity": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02",
            "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03 Intensity": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03",
            "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01 Intensity": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01",
            "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02 Intensity": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02",
            "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03 Intensity": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03",
        },
        "PEAKS": {
            "Sample 1 Normalized Area": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01",
            "Sample 2 Normalized Area": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02",
            "Sample 3 Normalized Area": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03",
            "Sample 4 Normalized Area": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01",
            "Sample 5 Normalized Area": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02",
            "Sample 6 Normalized Area": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03",
        },
        "MSAngel": {
            "abundance_LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01",
            "abundance_LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02",
            "abundance_LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03",
            "abundance_LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01",
            "abundance_LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02",
            "abundance_LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03",
        },
        "ProlineStudio": {
            "abundance_LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01.mgf": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01",
            "abundance_LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02.mgf": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02",
            "abundance_LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03.mgf": "LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03",
            "abundance_LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01.mgf": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01",
            "abundance_LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02.mgf": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02",
            "abundance_LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03.mgf": "LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03",
        }
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
    # QExactive
    QExactive_df = get_merged_json(
        repo_url="https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip",
        outfile_name="astral_df.json",
        write_to_file=True,
    )
    hash_dict_qexactive = get_raw_data(df=QExactive_df)
    return (QExactive_df,)


@app.cell
def _(QExactive_df):
    QExactive_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Functions
    """)
    return


@app.cell
def _(DDAQuantIonModuleQExactive, pathlib, pd):
    def extract_all_from_hashes(hashes, data_dir='extracted_files', module=DDAQuantIonModuleQExactive(token='')):
        """Extract all results from hashes."""
        all_datapoints = pd.DataFrame()
        results_dict = {}
        comments = []
        for point_hash, _tool in hashes.items():
            print(f'Processing {point_hash} - {_tool}')
            if not _tool in results_dict:
                results_dict[_tool] = {}
            raw_data_path = f'{data_dir}/{point_hash}/input_file'
            param_path = f'{data_dir}/{point_hash}/param_'
            raw_data_files = list(pathlib.Path(raw_data_path).parent.glob(f'{pathlib.Path(raw_data_path).name}.*'))
            print(f'Raw data files found: {raw_data_files}')
            param_files = list(pathlib.Path(param_path).parent.glob(f'{pathlib.Path(param_path).name}*.*'))  # Extension can vary
            print(f'Parameter files found: {param_files}')  # Extension and number can vary
            if not raw_data_files or not param_files:
                print(f'Skipping {point_hash} - {_tool}: No raw data or parameter files found.')  # Identify the correct raw data file extension. There can be only one raw data file per point_hash.
                continue
            raw_data_path = raw_data_files[0]
            extract_params_func = globals()[f'extract_{_tool.replace('-', '').lower().replace(' (diann quant)', '').replace('prolinestudio', 'proline')}_params']
            if 'quantms' in _tool:
                param_data = extract_params_func(file1=open(param_files[0], 'rb'), file2=open(param_files[1], 'rb')).__dict__
            elif 'FragPipe' in _tool or 'AlphaPept' in _tool:
                param_data = extract_params_func(open(param_files[0], 'rb')).__dict__  # Identify the correct parameter file extension. There can be one or two (quantms) parameter files per point_hash.
            else:
                param_data = extract_params_func(param_files[0]).__dict__
            results_performance, all_datapoints, _ = module.benchmarking(raw_data_path, _tool, user_input=param_data, all_datapoints=all_datapoints)
            if 'MaxQuant' in _tool:
                print('adding carbamidos to maxquant')
                results_performance['precursor ion'] = results_performance['precursor ion'].apply(lambda x: x.replace('C', 'C[Carbamidomethyl]'))
            if 'PEAKS' in _tool or 'i2MassChroQ' in _tool:
                print('rewriting N-Terminal acetylation')
                results_performance['precursor ion'] = results_performance['precursor ion'].apply(rewrite_nterm_acetylation)
            results_dict[_tool][point_hash] = results_performance
            all_datapoints.loc[all_datapoints['old_new'] == 'new', 'intermediate_hash'] = point_hash
            print(all_datapoints['intermediate_hash'])
        all_datapoints['old_new'] = 'old'
        return (results_dict, all_datapoints)

    def rewrite_nterm_acetylation(proforma):
        if proforma[1:9] == '[Acetyl]':
            return f'[Acetyl]-{proforma[0] + proforma[9:]}'
        return proforma  # overwrite new hash with actual hash  # Set all datapoints to old  # A[Acetyl]AAAAAAGDSDSWDADAFSVEDPVRK -> [Acetyl]-AAAAAAAGDSDSWDADAFSVEDPVRK

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

    def plot_performance_metrics(all_datapoints, min_quant=3, metric='Median', subset=None, x_range=None, y_range=None, autoscale=True, subset_col='id'):
        """Plot performance metrics for data points."""
        if subset:
            all_datapoints = all_datapoints[all_datapoints[subset_col].isin(subset)]
        all_datapoints = prepare_datapoints(all_datapoints, min_quant=min_quant)
        print(all_datapoints)
        print(metric)
        _plot = PlotDataPoint.plot_metric(all_datapoints, metric=metric, hide_annot=True)
        _plot.update_layout(xaxis=dict(range=x_range) if x_range else {}, yaxis=dict(range=y_range) if y_range else {})
        if autoscale:
            y_min = all_datapoints['nr_prec'].min()
            y_max = all_datapoints['nr_prec'].max()
            _plot.update_yaxes(range=[y_min - y_min * 0.08, y_max + y_max * 0.05])
            if metric == 'Median':
                x_min = all_datapoints['median_abs_epsilon'].min()
                x_max = all_datapoints['median_abs_epsilon'].max()
            else:
                x_min = all_datapoints['mean_abs_epsilon'].min()
                x_max = all_datapoints['mean_abs_epsilon'].max()
            _plot.update_xaxes(range=[x_min - x_min * 0.05, x_max + x_max * 0.05])
        _plot.update_xaxes(title_text='{}QuantError({})'.format(metric, min_quant))
        _plot.update_yaxes(title_text='Depth({})'.format(min_quant))
        return _plot

    def plot_performance_metrics_all_filters(all_datapoints, metric='Median', subset=None, subset_col='id'):
        if subset:
            all_datapoints = all_datapoints[all_datapoints[subset_col].isin(subset)]
        plots = []
        x_min = 0
        x_max = 0
        y_min = 0
        y_max = 0
        for min_quant in range(1, 7):
            datapoints = prepare_datapoints(all_datapoints, min_quant=min_quant)
            _plot = PlotDataPoint.plot_metric(datapoints, metric=metric, hide_annot=True)
            plots.append(_plot)  # Automatically adjust the y-axis range based on the data
            print(datapoints['median_abs_epsilon'].min())
            print(datapoints['median_abs_epsilon'].max())
            if datapoints['median_abs_epsilon'].min() < x_min or x_min == 0:
                x_min = datapoints['median_abs_epsilon'].min()
            if datapoints['median_abs_epsilon'].max() > x_max or x_max == 0:
                x_max = datapoints['median_abs_epsilon'].max()
            if datapoints['nr_prec'].min() < y_min or y_min == 0:
                y_min = datapoints['nr_prec'].min()
            if datapoints['nr_prec'].max() > y_max or y_max == 0:
                y_max = datapoints['nr_prec'].max()
        combined_fig = make_subplots(rows=2, cols=3, subplot_titles=[f'k={i}' for i in range(1, 7)])
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
        y_min_scaled = y_min - y_min * 0.3  # update x axis and y axis label
        y_max_scaled = y_max + y_max * 0.05
        x_min_scaled = x_min - x_min * 0.05
        x_max_scaled = x_max + x_max * 0.3
        print(f'x_min: {x_min}, x_max: {x_max}y_min: {y_min}, y_max: {y_max}')
        for _fig, (r, c) in zip(plots, positions):
            for trace in _fig.data:
                combined_fig.add_trace(trace, row=r, col=c)
        combined_fig.update_layout(height=800, width=1200)
        layout_update = {}
        for i in range(1, 7 + 1):
            layout_update[f'xaxis{(i if i > 1 else '')}'] = dict(range=[0.1, 0.6])
            layout_update[f'yaxis{(i if i > 1 else '')}'] = dict(range=[y_min_scaled, y_max_scaled])
        combined_fig.update_layout(**layout_update)
        names = set()
        combined_fig.for_each_trace(lambda trace: trace.update(showlegend=False) if trace.name in names else names.add(trace.name))
        return combined_fig

    def prepare_performance_dict(results, mappers=MAPPERS, mapper=None, subset=None):
        """Prepare a dictionary of performance results."""
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}
        performance_dict = {}
        for _tool, subdict in results.items():
            print(f'Processing {_tool}')
            print(f'Tool has the following runs: {subdict.keys()}')
            for run_name, df in subdict.items():
                print(f'Processing {run_name}')
                if mapper != None:
                    df = df.rename(columns=mappers[mapper])
                elif _tool in mappers:
                    tool_mapper = mappers[_tool]
                    df = df.rename(columns=tool_mapper)
                df.columns = [x.replace('.mzML', '') for x in df.columns]
                if _tool not in performance_dict:
                    performance_dict[_tool] = []
                performance_dict[_tool].append(df)
        return performance_dict  # N = number of subplots  # remove duplicate legend items  #print(results)

    return (
        plot_performance_metrics,
        plot_performance_metrics_all_filters,
        prepare_performance_dict,
    )


@app.cell
def _(matplotlib, pd, plt, re, sns, upsetplot):
    def filter_upset_data(data, tools):
        data_index_reset = data.reset_index()  # Filter the data so that only subsets are plotted that contain sequences from all tools, from all-but-one tool, or from only one tool
        ids = data_index_reset['id']
        occurrences = data_index_reset.drop(columns='id')
        occurrences = occurrences.astype(int)
        row_sums = occurrences.sum(axis=1)
        row_sums = pd.DataFrame(row_sums)
        row_sums = row_sums.rename(columns={0: 'Number of tools'})  # Turn row_sums into a dataframe
        row_sums['id'] = ids
        print('number of precursor ions before filtering:')
        print(len(data_index_reset))
        filtered_data = data_index_reset[(row_sums['Number of tools'] == len(tools)) | (row_sums['Number of tools'] == len(tools) - 1) | (row_sums['Number of tools'] == 1)]
        filtered_data = filtered_data.set_index(tools)
        return filtered_data

    def add_epsilons(data, df_dict):
        data_index = data.index
        data = data.reset_index()
        for _tool, df in df_dict.items():
            print(_tool)
            data = data.merge(df[['precursor ion', 'epsilon']], left_on='id', right_on='precursor ion', how='left')
            data.to_csv(f'analysis_debug/{_tool}_epsilon.csv')
            data = data.rename(columns={'epsilon': f'{_tool}_epsilon'})
            data = data.drop(columns=['precursor ion'])
        data = data.set_index(data_index.names)
        return data  # Store the original index

    def upsetplot_from_df_dict(df_dict):  # Reset the index so that the id column is available for merging
        sequence_dict = {}
        for _tool, df in df_dict.items():
            unique_sequences = df['precursor ion'].unique()
            sequence_dict[_tool] = set(unique_sequences)  # Merge the id column from df with the epsilon column from tool_df
        sequences = upsetplot.from_contents(sequence_dict)
        tools = list(df_dict.keys())
        filtered_sequences = filter_upset_data(sequences, tools)
        data_with_epsilons = add_epsilons(filtered_sequences, df_dict)
        return data_with_epsilons

    def plot_boxplot(boxplot_data, ax):
        boxplot_data['absolute epsilon'] = boxplot_data['epsilon'].abs()
        sns.boxplot(data=boxplot_data, x='workflow', y='absolute epsilon', hue='quantified by', ax=ax, showfliers=False, linewidth=1)
        ax.set_ylabel('Error between measured and expected logFC', fontsize=7, fontweight='bold')
        ax.yaxis.grid(True, linestyle='--', color='gray', alpha=0.7)
        ax.xaxis.grid(False)
        ax.yaxis.label.set_size(12)  # Set the index back to the original index
        ax.get_legend().remove()
        plt.tight_layout()

    def strip_peptidoform(peptidoform):
        no_mods = re.sub('\\[.*?\\]', '', peptidoform)
        no_mods = no_mods.replace('-', '')
        return no_mods
      # Each df should have a "sequence" column
    def filter_df(df):
        df['precursor ion'] = df['precursor ion'].apply(strip_peptidoform)  # Store the sequences in a list and add it to the dictionary
        df.drop_duplicates(subset='precursor ion', inplace=True, keep='first')
        return df
      # Create the upset plot
    def plot_upset_and_boxplot(df_dict, mapper, stripped=False):
        if stripped:
            df_dict_copy = df_dict.copy()
            df_dict_copy = {key: filter_df(val) for key, val in df_dict_copy.items()}
        else:
            df_dict_copy = df_dict.copy()
        boxplotdata = upsetplot_from_df_dict(df_dict_copy)
        _fig, ax_upset = plt.subplots(1, 1, figsize=(6, 3))
        matplotlib.rcParams.update({'font.size': 10})
        upset = upsetplot.UpSet(boxplotdata, subset_size='count', include_empty_subsets=False, sort_categories_by='input')
        upset.style_subsets(min_degree=1, facecolor='#3274A1')
        upset.style_subsets(min_degree=2, facecolor='black')  # Draw the stripplot with a custom palette
        upset.style_subsets(min_degree=6, facecolor='#E1812C')
        upset.plot(fig=_fig)
        ax_upset.grid(False)
        ax_upset.set_xlabel('')
        ax_upset.set_xticks([])
        ax_upset.set_ylabel('')
        ax_upset.set_yticks([])
        ax_upset.spines['top'].set_visible(False)
        ax_upset.spines['right'].set_visible(False)  #palette="Set2"
        ax_upset.spines['left'].set_visible(False)
        ax_upset.spines['bottom'].set_visible(False)  # sns.violinplot(data=boxplot_data, x="tool", y="epsilon", hue = "unique or all", ax=ax, inner=None, linewidth=1)
        for text in _fig.findobj(match=plt.Text):
            text.set_fontsize(8)  # Add the number of observations to each boxplot
        boxplotdata = boxplotdata.reset_index()
        boxplotdata['index_list'] = boxplotdata[boxplotdata.columns[:6]].values.tolist()  # Improve aesthetics of labels and title
        boxplotdata['eval'] = boxplotdata['index_list'].apply(str).map(mapper)
        boxplotdata = boxplotdata.dropna(subset=['eval'])
        boxplotdata.to_csv('boxplotdata.csv')
        epsilon_cols = [col for col in boxplotdata.columns if '_epsilon' in col]  # rotate
        important_cols = epsilon_cols + ['eval']  # ax.set_xticklabels(ax.get_xticklabels(), rotation=20, horizontalalignment="right")
        boxplotdata = boxplotdata[important_cols]
        boxplotdata['eval'] = pd.Categorical(boxplotdata['eval'], categories=mapper.values(), ordered=True)  # Add subtle grid lines to enhance readability
        boxplotdata = boxplotdata.sort_values('eval')
        boxplotdata_final = pd.DataFrame()  # Only y-axis grid for cleaner look
        for col in epsilon_cols:
            temp = boxplotdata[['eval', col]]  # make y label bigger
            _tool = col.split('_epsilon')[0]
            ions = temp[(temp['eval'] == _tool) | (temp['eval'] == 'all')]
            ions['quantified by'] = ions['eval'].apply(lambda x: 'all' if x == 'all' else 'unique')  # remove legend
            ions['workflow'] = _tool
            ions = ions.rename(columns={col: 'epsilon'})
            ions = ions.drop(columns=['eval']).reset_index(drop=True)  # Add a tighter layout for better spacing
            boxplotdata_final = pd.concat([boxplotdata_final, ions])
        boxplotdata_final.reset_index(drop=True, inplace=True)
        _fig, box_ax = plt.subplots(figsize=(10, 6))
        fig_box = plot_boxplot(boxplotdata_final, ax=box_ax)
        plt.show()
        return (_fig, fig_box)

    def plot_upset_and_boxplot_all_filters(df_dict, mapper, save_path='figures_manuscript/'):
        for i in range(1, 7):
            df_dict_filtered = {key: value[0][value[0]['nr_observed'] >= i] for key, value in df_dict.items()}
            boxplotdata = upsetplot_from_df_dict(df_dict_filtered)
            _fig, ax_upset = plt.subplots(1, 1, figsize=(6, 3))
            matplotlib.rcParams.update({'font.size': 10})
            upset = upsetplot.UpSet(boxplotdata, subset_size='count', include_empty_subsets=False, sort_categories_by='input', show_counts=False)
            upset.style_subsets(min_degree=1, facecolor='#3274A1')
            upset.style_subsets(min_degree=2, facecolor='black')
            upset.style_subsets(min_degree=6, facecolor='#E1812C')
            upset.plot(fig=_fig)
            ax_upset.grid(False)
            ax_upset.set_xlabel('')
            ax_upset.set_xticks([])
            ax_upset.set_ylabel('')
            ax_upset.set_yticks([])
            ax_upset.spines['top'].set_visible(False)
            ax_upset.spines['right'].set_visible(False)
            ax_upset.spines['left'].set_visible(False)
            ax_upset.spines['bottom'].set_visible(False)
            for text in _fig.findobj(match=plt.Text):  # plot upset plot
                text.set_fontsize(8)
            _fig.savefig(save_path + f'upset_plot_min_quant_{i}.svg')
            n_tools = 6
            boxplotdata = boxplotdata.reset_index()
            boxplotdata['index_list'] = boxplotdata[boxplotdata.columns[:n_tools]].values.tolist()
            boxplotdata['eval'] = boxplotdata['index_list'].apply(str).map(mapper)
            epsilon_cols = [col for col in boxplotdata.columns if '_epsilon' in col]
            important_cols = epsilon_cols + ['eval']
            boxplotdata = boxplotdata[important_cols]
            boxplotdata['eval'] = pd.Categorical(boxplotdata['eval'], categories=mapper.values(), ordered=True)
            boxplotdata = boxplotdata.sort_values('eval')
            boxplotdata_final = pd.DataFrame()
            for col in epsilon_cols:
                temp = boxplotdata[['eval', col]]  # Hide x-axis label and ticks
                _tool = col.split('_epsilon')[0]
                ions = temp[(temp['eval'] == _tool) | (temp['eval'] == 'all')]
                ions['quantified by'] = ions['eval'].apply(lambda x: 'all' if x == 'all' else 'unique')
                ions['workflow'] = _tool
                ions = ions.rename(columns={col: 'epsilon'})
                ions = ions.drop(columns=['eval']).reset_index(drop=True)  # Hide the box
                boxplotdata_final = pd.concat([boxplotdata_final, ions])
            boxplotdata_final.reset_index(drop=True, inplace=True)
            _fig, box_ax = plt.subplots(figsize=(10, 6))
            fig_box = plot_boxplot(boxplotdata_final, ax=box_ax)
            plt.ylabel('AbsQuantError({})'.format(i))
            plt.savefig(save_path + f'boxplot_min_quant_{i}.svg')
            plt.show()
        return (_fig, fig_box)  # color the same as boxplot  # plot boxplot, sorted the same way as the upset plot  # this needs to be adapted to the number of tools... currently hardcoded :( sorry  # drop all ions that are neither all or unique  # turn to long format for plotting  # Set the style  # filter the df dict  # plot upset plot  # Save the upset plot  # Hide x-axis label and ticks  # Hide the box  # plot boxplot, sorted the same way as the upset plot  # # drop all ions that are neither all or unique  # boxplotdata = boxplotdata.dropna(subset=["eval"])  # turn to long format for plotting  # Set the style  #plt.title("Min. quantified ions: " + str(i))

    return (
        plot_boxplot,
        plot_upset_and_boxplot_all_filters,
        strip_peptidoform,
        upsetplot_from_df_dict,
    )


@app.cell
def _(pd, plt, sns):
    def plot_filtered_intensity_boxplots(tool_dict, save_path="figures_manuscript/"):
        # Get the MaxQuant DataFrame
        first_df = tool_dict["MaxQuant"][0]

        # Ensure 'Intensity_mean_A' and 'nr_observed' columns exist
        if 'log_Intensity_mean_A' not in first_df.columns or 'nr_observed' not in first_df.columns:
            print("Error: Required columns ('log_Intensity_mean_A', 'nr_observed') not found in the first tool DataFrame.")
            return

        # Create a list to store the data for the boxplot
        intensity_data = pd.DataFrame()
        abserror_data = pd.DataFrame()
        labels = []

        # Loop through filter values for 'nr_observed' from 1 to 6
        for i in range(1, 7):
            # Filter the DataFrame for rows where 'nr_observed' >= i
            filtered_df = first_df[first_df['nr_observed'] >= i]

            # Check if there are any data points for the current filter
            if len(filtered_df) > 0:
                intensity_data[i] = filtered_df['log_Intensity_mean_A']
                abserror_data[i] = filtered_df['epsilon'].abs()
                labels.append(f"k = {i}")
            else:
                labels.append(f"k = {i} (No data)")

        # Create the boxplot
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=intensity_data, color='royalblue', showfliers=False)

        # Set the x-ticks and labels
        plt.xticks(range(len(labels)), labels)

        # Adding labels and title
        plt.xlabel('Minimum number of runs the ion was observed in')
        plt.ylabel('mean log2(Intensity) in condition A')
        #plt.title(f'Boxplot of Intensity_mean_A for {first_tool} with varying nr_observed filters')

        # Show the plot
        plt.tight_layout()
        plt.savefig(save_path + f"meanlogIntensity_over_k.svg")
        plt.show()

        # plot boxplots over k, showing absquanterror
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=abserror_data, color='royalblue', showfliers=False)
        plt.xlabel('Minimum number of runs the ion was observed in')
        plt.ylabel('AbsQuantError(k)')
        plt.xticks(range(len(labels)), labels)
        #plt.title(f'Boxplot of AbsQuantError(k) for {first_tool}')
        #plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(save_path + f"absquanterror_over_k.svg")

        plt.show()

    return (plot_filtered_intensity_boxplots,)


@app.cell
def _(
    MAPPERS,
    matplotlib,
    pd,
    plot_boxplot,
    plt,
    upsetplot,
    upsetplot_from_df_dict,
):
    # MBR Analysis versions of the above functions
    def prepare_performance_dict_MBR_analysis(results, mappers=MAPPERS, mapper=None, subset=None):
        """Prepare a dictionary of performance results."""
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}
        performance_dict = {}
        for _tool, subdict in results.items():
            print(f'Processing {_tool}')
            print(f'Tool has the following runs: {subdict.keys()}')
            for run_name, df in subdict.items():
                print(f'Processing {run_name}')
                if mapper != None:
                    df = df.rename(columns=mappers[mapper])
                elif _tool in mappers:
                    tool_mapper = mappers[_tool]
                    df = df.rename(columns=tool_mapper)
                df.columns = [x.replace('.mzML', '') for x in df.columns]
                if run_name == '8cbc0bce20eee581ad10326e02a09dbc316c30e1':
                    performance_dict['MaxQuant (MBR)'] = df
                elif run_name == '36b7b01b380f641722b3b34633bb53d72348eb80':
                    performance_dict['MaxQuant (no MBR)'] = df
        return performance_dict

    def plot_upset_and_boxplot_and_scatterplot_all_filters_MBR_analysis(df_dict, mapper, save_path='figures_manuscript/'):
        for i in range(1, 7):
            df_dict_filtered = {key: value[value['nr_observed'] >= i] for key, value in df_dict.items()}
            boxplotdata = upsetplot_from_df_dict(df_dict_filtered)
            _fig, ax_upset = plt.subplots(1, 1, figsize=(6, 3))
            matplotlib.rcParams.update({'font.size': 10})
            upset = upsetplot.UpSet(boxplotdata, subset_size='count', include_empty_subsets=False, sort_categories_by='input', show_counts=True)
            upset.style_subsets(min_degree=1, facecolor='#3274A1')
            upset.style_subsets(min_degree=2, facecolor='black')
            upset.style_subsets(min_degree=6, facecolor='#E1812C')
            upset.plot(fig=_fig)
            ax_upset.grid(False)
            ax_upset.set_xlabel('')
            ax_upset.set_xticks([])
            ax_upset.set_ylabel('')
            ax_upset.set_yticks([])  # filter the df dict
            ax_upset.spines['top'].set_visible(False)
            ax_upset.spines['right'].set_visible(False)
            ax_upset.spines['left'].set_visible(False)
            ax_upset.spines['bottom'].set_visible(False)
            for text in _fig.findobj(match=plt.Text):
                text.set_fontsize(8)
            _fig.savefig(save_path + f'upset_plot_min_quant_{i}.svg')
            n_tools = 2  # plot upset plot
            boxplotdata = boxplotdata.reset_index()
            boxplotdata['index_list'] = boxplotdata[boxplotdata.columns[:n_tools]].values.tolist()
            boxplotdata['eval'] = boxplotdata['index_list'].apply(str).map(mapper)
            epsilon_cols = [col for col in boxplotdata.columns if '_epsilon' in col]
            important_cols = epsilon_cols + ['eval']
            boxplotdata = boxplotdata[important_cols]
            boxplotdata['eval'] = pd.Categorical(boxplotdata['eval'], categories=mapper.values(), ordered=True)
            boxplotdata = boxplotdata.sort_values('eval')
            boxplotdata_final = pd.DataFrame()
            for col in epsilon_cols:
                temp = boxplotdata[['eval', col]]
                _tool = col.split('_epsilon')[0]
                ions = temp[(temp['eval'] == _tool) | (temp['eval'] == 'all')]  # Save the upset plot
                ions['quantified by'] = ions['eval'].apply(lambda x: 'all' if x == 'all' else 'unique')
                ions['workflow'] = _tool
                ions = ions.rename(columns={col: 'epsilon'})  # Hide x-axis label and ticks
                ions = ions.drop(columns=['eval']).reset_index(drop=True)
                boxplotdata_final = pd.concat([boxplotdata_final, ions])
            boxplotdata_final.reset_index(drop=True, inplace=True)
            _fig, box_ax = plt.subplots(figsize=(10, 6))
            fig_box = plot_boxplot(boxplotdata_final, ax=box_ax)  # Hide the box
            plt.ylabel('AbsQuantError({})'.format(i))
            plt.savefig(save_path + f'boxplot_MBR_min_quant_{i}.svg')
            plt.show()
            plt.scatter(x=abs(boxplotdata['MaxQuant (MBR)_epsilon']), y=abs(boxplotdata['MaxQuant (no MBR)_epsilon']), alpha=0.5)
            plt.xlabel('AbsQuantError({}), MBR'.format(i))
            plt.ylabel('AbsQuantError({}), no MBR'.format(i))
        return (_fig, fig_box)  # plot boxplot, sorted the same way as the upset plot  # # drop all ions that are neither all or unique  # boxplotdata = boxplotdata.dropna(subset=["eval"])  # turn to long format for plotting  # Set the style  #plt.title("Min. quantified ions: " + str(i))  # Plot the scatter plot of MBR vs no MBR

    return (
        plot_upset_and_boxplot_and_scatterplot_all_filters_MBR_analysis,
        prepare_performance_dict_MBR_analysis,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Module overviews
    """)
    return


@app.cell
def _(QExactive_df):
    relevant_points_QExactive = (
        QExactive_df[
            ["software_name", "intermediate_hash"]
        ]
        .set_index("intermediate_hash")
        .to_dict()["software_name"]
    )
    return (relevant_points_QExactive,)


@app.cell
def _(relevant_points_QExactive):
    relevant_points_QExactive
    return


@app.cell
def _(
    DDAQuantIonModuleQExactive,
    extract_all_from_hashes,
    relevant_points_QExactive,
):
    results_dict, all_datapoints = extract_all_from_hashes(
        relevant_points_QExactive,
        data_dir="extracted_files",
        module=DDAQuantIonModuleQExactive(token=""),
    )
    return all_datapoints, results_dict


@app.cell
def _(all_datapoints, plot_performance_metrics):
    _plot = plot_performance_metrics(all_datapoints, metric='Median', min_quant=3, autoscale=True)
    _plot.write_image('figures_manuscript/median_abs_overview_qexactive.svg')
    _plot
    return


@app.cell
def _(all_datapoints, plot_performance_metrics):
    _plot = plot_performance_metrics(all_datapoints, metric='Mean', x_range=[0.1, 0.6], y_range=[20000, 150000], min_quant=3, autoscale=True)
    _plot.write_image('figures_manuscript/mean_abs_overview_qexactive.svg')
    # Save the plot
    _plot
    return


@app.cell
def _(all_datapoints, plot_performance_metrics_all_filters):
    _plot = plot_performance_metrics_all_filters(all_datapoints, metric='Median')
    _plot.write_image('figures_manuscript/median_abs_kseries_qexactive.svg')
    _plot
    return


@app.cell
def _(all_datapoints, plot_performance_metrics_all_filters):
    _plot = plot_performance_metrics_all_filters(all_datapoints, metric='Mean')
    _plot.write_image('figures_manuscript/mean_abs_kseries_qexactive.svg')
    _plot
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Impact of MBR on and off
    """)
    return


@app.cell
def _():
    subset_hashes_MBR = [
        "982740480e3e36433d6691e3588bc4c2acea4430", # i2mass no MBR
        "e0ab1339a5354cb27d895ff252383ee4a3365b2e", # i2mass MBR
        "36b7b01b380f641722b3b34633bb53d72348eb80", # MaxQuant no MBR
        "8cbc0bce20eee581ad10326e02a09dbc316c30e1", # MaxQuant MBR
    ]
    return (subset_hashes_MBR,)


@app.cell
def _(all_datapoints):
    all_datapoints
    return


@app.cell
def _(all_datapoints):
    all_datapoints[all_datapoints['intermediate_hash'] == '982740480e3e36433d6691e3588bc4c2acea4430']
    return


@app.cell
def _(all_datapoints, plot_performance_metrics, subset_hashes_MBR):
    _plot = plot_performance_metrics(all_datapoints, subset=subset_hashes_MBR, min_quant=3, subset_col='intermediate_hash', autoscale=True)
    _plot
    return


@app.cell
def _(
    plot_upset_and_boxplot_and_scatterplot_all_filters_MBR_analysis,
    prepare_performance_dict_MBR_analysis,
    results_dict,
):
    # suppl. fig 7
    subset_hashes_MBR_MaxQuant = ['36b7b01b380f641722b3b34633bb53d72348eb80', '8cbc0bce20eee581ad10326e02a09dbc316c30e1']
    all_tools_mapper = {'[True, False]': 'MaxQuant (MBR)', '[False, True]': 'MaxQuant (no MBR)', '[True, True]': 'all'}
    performance_df_dict = prepare_performance_dict_MBR_analysis(results_dict, mapper=None, subset=subset_hashes_MBR_MaxQuant)  # MaxQuant no MBR
    _fig = plot_upset_and_boxplot_and_scatterplot_all_filters_MBR_analysis(performance_df_dict, all_tools_mapper, save_path='figures_manuscript/')  # MaxQuant MBR
    return


@app.cell
def _():
    subset_hashes_MaxQuantVersions = [
        "8f4fa9a7dd1f44ac4ae7a7e7fb9b9606660f4578", # 1.5.2.8
        "f4f23a743baef55ba419a1cf0e8dd67a4cb5b7ac", # 1.5.3.30
        "5dc44925b46df18a2799648b5f975a41ba8bf89f", # 1.5.8.2
        "7912158e0522a315917e20fe434966ca9a17192e", #1.6.3.3
        "a1140a31b414d7b3110ee9b9c0456cc4f1709782", # 2.1.3.0
        "36b7b01b380f641722b3b34633bb53d72348eb80", #2.1.4.0
        "00e2f863939301a2a71178652972dad895b27520" #2.5.1.0
    ]
    return (subset_hashes_MaxQuantVersions,)


@app.cell
def _(
    all_datapoints,
    plot_performance_metrics,
    subset_hashes_MaxQuantVersions,
):
    _plot = plot_performance_metrics(all_datapoints, subset=subset_hashes_MaxQuantVersions, min_quant=3, subset_col='intermediate_hash', autoscale=True)
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
    subset_hashes_1pertool = [
        "2a5ef6191b8098757d490acf76bb9c2af5b89a39", # MSAngel
    "9d1361331b165d6cc779ccf614419eb77057f573", # PEAKS
    #"d01e87b997b84c985868204b1ed26749902fd7f9", # quantms
    "6ed9da37e9d4600a9a28968c9a01db2b967d33cb", # Proline Studio
    # "bbd079eda4dd3d6a51b37924d83db50022530bb6", # Sage
    #"4decb9e0d2d9ed9f9be6a9ad5aa066b1dcd1e616", # WOMBAT
    "a3d801fcb75c46b2e76fa7078ae0a004360ebe44", # MaxQuant
    "28b0c3b9853a5b60c9e47428b8a51b4898083523", # FragPipe
    "90d852742aa152dc7ed813acebf7916b0c1d5b76", # i2masschroq
    ]
    return (subset_hashes_1pertool,)


@app.cell
def _():
    all_tools_mapper_1 = {'[True, False, False, False, False, False]': 'FragPipe', '[False, True, False, False, False, False]': 'i2MassChroQ', '[False, False, True, False, False, False]': 'MaxQuant', '[False, False, False, True, False, False]': 'MSAngel', '[False, False, False, False, True, False]': 'ProlineStudio', '[False, False, False, False, False, True]': 'PEAKS', '[True, True, True, True, True, False]': 'all but PEAKS', '[True, True, True, True, False, True]': 'all but ProlineStudio', '[True, True, True, False, True, True]': 'all but MSAngel', '[True, True, False, True, True, True]': 'all but MaxQuant', '[True, False, True, True, True, True]': 'all but i2MassChroQ', '[False, True, True, True, True, True]': 'all but FragPipe', '[True, True, True, True, True, True]': 'all'}  # FragPipe i2MassChroQ MaxQuant MSAngel ProlineStudio PEAKS
    return (all_tools_mapper_1,)


@app.cell
def _(prepare_performance_dict, results_dict, subset_hashes_1pertool):
    performance_df_dict_1 = prepare_performance_dict(results_dict, mapper=None, subset=subset_hashes_1pertool)
    return (performance_df_dict_1,)


@app.cell
def _(
    all_tools_mapper_1,
    performance_df_dict_1,
    plot_upset_and_boxplot_all_filters,
):
    _fig = plot_upset_and_boxplot_all_filters(performance_df_dict_1, all_tools_mapper_1, save_path='figures_manuscript/')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A look at precursor quantification for e.coli and yeast precursors
    """)
    return


@app.cell
def _(np, pd, plt, sns, to_rgba):
    def plot_pair_quantifications(results, subset):
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}
        lprec = {}
        for _tool, subdict in results.items():
            for hashe, df in subdict.items():
                precursors = df['precursor ion'].unique()
                lprec[hashe] = precursors
        lplot = []
        for i, (_tool, subdict) in enumerate(results.items()):
            for hashe, df in subdict.items():
                res = df[['precursor ion', 'log2_A_vs_B', 'species']].copy()
                res['tool'] = _tool
                lplot.append(res)
        gtab = pd.concat(lplot, ignore_index=True)
        gtab_wide = gtab.pivot_table(index=['species', 'precursor ion'], columns='tool', values='log2_A_vs_B')
        lims = np.max(np.abs(gtab[gtab['species'].isin(['ECOLI', 'YEAST'])]['log2_A_vs_B'].dropna()))  # prepare the data for the pair plot
        lims = (-lims, lims)
        ecoli = gtab_wide[gtab_wide.index.get_level_values('species') == 'ECOLI'].reset_index()
        g = sns.pairplot(ecoli.drop(columns=['species', 'precursor ion']), plot_kws={'alpha': 0.1})
        for i, ax in enumerate(g.axes.flatten()):
            if not i % len(g.axes) == i // len(g.axes):
                ax.axhline(y=-2, linestyle='--', linewidth=0.5)
            ax.set_xlim(lims)
            ax.set_ylim(lims)
            ax.axvline(x=-2, linestyle='--', linewidth=0.5)
        plt.suptitle('E. coli Pairplot')
        plt.tight_layout()
        plt.show()
        yeast = gtab_wide[gtab_wide.index.get_level_values('species') == 'YEAST'].reset_index()  # Get limits for the plots
        g = sns.pairplot(yeast.drop(columns=['species', 'precursor ion']), plot_kws={'alpha': 0.1})
        for i, ax in enumerate(g.axes.flatten()):
            if not i % len(g.axes) == i // len(g.axes):
                ax.axhline(y=1, linestyle='--', linewidth=0.5)
            ax.set_xlim(lims)
            ax.set_ylim(lims)  # Create the pair plot for E. coli
            ax.axvline(x=1, linestyle='--', linewidth=0.5)
        plt.suptitle('Yeast Pairplot')
        plt.tight_layout()
        plt.savefig('figures_manuscript/pair_quantifications.svg')
        plt.show()

    def plot_pair_quantifications_combined(results, subset=None):
        """  # Apply same axis limits to all subplots in E. coli pairplot
        Create a combined pair plot comparing log2(A vs B) fold-changes across multiple tools
        using E. coli (lower triangle) and Yeast (upper triangle) precursor ions.  # Skip the diagonal subplots (i.e., where row == column)
      # Diagonal check
        Parameters:
            results (dict): Dictionary mapping tool name -> dict of {hash -> DataFrame} with
                            columns ['precursor ion', 'log2_A_vs_B', 'species'].
            subset (list, optional): List of tool names to include in the plot.
        """
        if subset:
            results = {k: {sk: v for sk, v in inner_dict.items() if sk in subset} for k, inner_dict in results.items()}
        tools = ['FragPipe', 'i2MassChroQ', 'MaxQuant', 'MSAngel', 'ProlineStudio', 'PEAKS']
        print(results.keys)
        tool_data = {}  # Plot for yeast
        for _tool in tools:
            dfs = [df.copy() for df in results[_tool].values()]
            if len(dfs) > 0:
                tool_data[_tool] = pd.concat(dfs, ignore_index=True)
        e_coli_vals = {}
        yeast_vals = {}
        for _tool, df in tool_data.items():
            ecoli_df = df[df['species'].str.upper() == 'ECOLI']  # Apply same axis limits to all subplots in Yeast pairplot
            yeast_df = df[df['species'].str.upper() == 'YEAST']
            e_coli_vals[_tool] = ecoli_df.set_index('precursor ion')['log2_A_vs_B']  # Skip the diagonal subplots (i.e., where row == column)
            yeast_vals[_tool] = yeast_df.set_index('precursor ion')['log2_A_vs_B']  # Diagonal check
        all_vals = pd.concat([s.dropna() for d in [e_coli_vals, yeast_vals] for s in d.values()])
        lim = np.ceil(np.percentile(np.abs(all_vals), 99.5)) * 1.1 if not all_vals.empty else 1.0
        col_ecoli = '#1f77b4'
        col_yeast = '#ff7f0e'
        n = len(tools)
        _fig, axes = plt.subplots(n, n, figsize=(3 * n, 3 * n))
        for i in range(n):
            for j in range(n):  # save svg
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
                    ax.axvline(-2, linestyle='--', color=col_ecoli, lw=1)
                    ax.axvline(1, linestyle='--', color=col_yeast, lw=1)
                    ax.set_xlim(-lim, lim)
                    if not i == 0:
                        ax.yaxis.set_visible(False)  #print(results)
                    if not j == n - 1:  # Filter hashes
                        ax.xaxis.set_visible(False)
                elif i > j:
                    ax.set_facecolor(to_rgba(col_ecoli, alpha=0.1))
                    x = e_coli_vals[tool_j]
                    y = e_coli_vals[tool_i]
                    common = x.index.intersection(y.index)
                    ax.scatter(x.loc[common], y.loc[common], color=col_ecoli, alpha=0.3, s=10, rasterized=True)
                    ax.axhline(-2, linestyle='--', color='gray', lw=0.8)
                    ax.axvline(-2, linestyle='--', color='gray', lw=0.8)
                    ax.set_xlim(-lim, lim)
                    ax.set_ylim(-lim, lim)  # Aggregate DataFrames per tool
                else:
                    ax.set_facecolor(to_rgba(col_yeast, alpha=0.1))
                    x = yeast_vals[tool_j]
                    y = yeast_vals[tool_i]
                    common = x.index.intersection(y.index)
                    ax.scatter(x.loc[common], y.loc[common], color=col_yeast, alpha=0.3, s=10, rasterized=True)
                    ax.axhline(1, linestyle='--', color='gray', lw=0.8)  # Extract species-specific data for each tool, indexed by precursor ion
                    ax.axvline(1, linestyle='--', color='gray', lw=0.8)
                    ax.set_xlim(-lim, lim)
                    ax.set_ylim(-lim, lim)
                if i < n - 1:
                    ax.set_xticks([])
                else:
                    ax.set_xlabel(tool_j)
                if j > 0:
                    ax.set_yticks([])  # Determine global log2 limits
                else:
                    ax.set_ylabel(tool_i)
        _fig.legend(handles=[plt.Line2D([0], [0], color=col_ecoli, lw=4, label='E. coli'), plt.Line2D([0], [0], color=col_yeast, lw=4, label='Yeast')], loc='upper right', bbox_to_anchor=(1.09, 0.99), title='Species')
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig('figures_manuscript/pair_quantifications_combined.svg')
        plt.show()  # Colors  # E. coli: lower triangle  # Yeast: upper triangle  # Clean ticks  # Final layout and legend  # save as svg

    return plot_pair_quantifications, plot_pair_quantifications_combined


@app.cell
def _(plot_pair_quantifications, results_dict, subset_hashes_1pertool):
    results = plot_pair_quantifications(results_dict, subset=subset_hashes_1pertool)
    return


@app.cell
def _(
    plot_pair_quantifications_combined,
    results_dict,
    subset_hashes_1pertool,
):
    plot_pair_quantifications_combined(results_dict, subset=subset_hashes_1pertool)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Quantified in more runs -> higher intensity?
    """)
    return


@app.cell
def _(
    plot_filtered_intensity_boxplots,
    prepare_performance_dict,
    results_dict,
):
    subset_hashes_example = ['a3d801fcb75c46b2e76fa7078ae0a004360ebe44']
    performance_df_dict_2 = prepare_performance_dict(results_dict, mapper=None, subset=subset_hashes_example)
    _fig = plot_filtered_intensity_boxplots(performance_df_dict_2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Check which search engines perform methionine excision
    """)
    return


@app.cell
def _():
    fasta =  "ProteoBenchFASTA_MixedSpecies_HYE.fasta"
    # get all tryptic peptides from the fasta file that are at the beginning of the sequence

    from typing import List, Tuple, Iterable
    from pyteomics import fasta as pyfasta
    from pyteomics.parser import cleave, expasy_rules

    def nterm_tryptic_peptides_with_mc(
        fasta_path: str,
        min_length: int = 7,
        missed_cleavages: int = 2,
    ) -> List[Tuple[str, str]]:
        """
        Return all N-terminal tryptic peptides from proteins that start with M,
        allowing up to `missed_cleavages` and keeping only peptides with length >= `min_length`.
        """
        results: List[Tuple[str, str]] = []
        rule = expasy_rules['trypsin']

        # IMPORTANT: iterate over the GENERATOR returned by pyteomics.fasta.read(...)
        for header, seq in pyfasta.read(fasta_path):
            s = (seq or "").replace('*', '').replace('\n', '').replace('\r', '').upper()
            if not s.startswith('M'):
                continue

            # Generate tryptic peptides (fully tryptic, with missed cleavages & min length)
            peps: Iterable[str] = cleave(
                s,
                rule,
                missed_cleavages=missed_cleavages,
                min_length=min_length
            )

            prot_id = header.split()[0]
            for p in peps:
                if s.startswith(p):
                    results.append(p)

        return list(set(results))

    return fasta, nterm_tryptic_peptides_with_mc


@app.cell
def _(fasta, nterm_tryptic_peptides_with_mc):
    n_term_peptides = nterm_tryptic_peptides_with_mc(fasta)
    n_term_peptides
    return (n_term_peptides,)


@app.cell
def _(n_term_peptides):
    n_term_peptides_excision = [p[1:] for p in n_term_peptides]
    n_term_peptides_excision
    return (n_term_peptides_excision,)


@app.cell
def _(prepare_performance_dict, results_dict):
    performance_df_dict_3 = prepare_performance_dict(results_dict, mapper=None)
    return (performance_df_dict_3,)


@app.cell
def _(
    n_term_peptides,
    n_term_peptides_excision,
    performance_df_dict_3,
    strip_peptidoform,
):
    peptides_dict = {}
    n_term_peptides_excision_counts = {}
    for _tool, df_list in performance_df_dict_3.items():
        for df in df_list:
            peptides_dict[_tool] = df['precursor ion'].unique().tolist()
            peptides_dict[_tool] = [strip_peptidoform(pept) for pept in peptides_dict[_tool]]
            peptides_dict[_tool] = [pept.split('|Z=')[0] for pept in peptides_dict[_tool]]
            peptides_dict[_tool] = list(set(peptides_dict[_tool]))
            n_term_peptides_count = len(set(peptides_dict[_tool]) & set(n_term_peptides))
            print(f'{_tool}: {n_term_peptides_count} N-terminal peptides found in {len(peptides_dict[_tool])} total peptides.')
            n_term_peptides_excision_count = len(set(peptides_dict[_tool]) & set(n_term_peptides_excision))
            print(f'{_tool}: {n_term_peptides_excision_count} N-terminal peptides with excision found in {len(peptides_dict[_tool])} total peptides.')
            if _tool not in n_term_peptides_excision_counts:
                n_term_peptides_excision_counts[_tool] = []
            n_term_peptides_excision_counts[_tool].append(n_term_peptides_excision_count)
    n_term_peptides_excision_counts
    return


@app.cell
def _(plt):
    data = {'FragPipe': [792, 654, 886, 649, 792, 805], 'WOMBAT': [643, 602, 550, 506, 636], 'i2MassChroQ': [1, 1, 746, 766, 773, 791, 768, 1, 766, 1], 'MaxQuant': [646, 623, 644, 626, 646, 646, 645, 624, 554, 646, 646, 647, 644, 624, 644], 'Sage': [0, 0], 'AlphaPept': [0, 0, 0, 0], 'MSAngel': [741], 'ProlineStudio': [772], 'quantms': [0], 'PEAKS': [903]}
    counts = []
    colors = []
    tool_labels = []
    color_map = plt.cm.tab20
    tool_names = list(data.keys())
    for i, _tool in enumerate(tool_names):
        vals = data[_tool]
        counts.extend(vals)
        colors.extend([color_map(i % 20)] * len(vals))
        tool_labels.extend([_tool] * len(vals))
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(counts)), counts, color=colors)
    # Flatten data for plotting
    plt.xticks(range(len(counts)), tool_labels, rotation=90)
    plt.ylabel('Count')
    plt.title('Identified N-terminal peptides with Methionine excision per Tool')
    plt.tight_layout()  # color palette
    # Create the bar plot
    # Label x-axis with tool names, repeated for each bar
    plt.show()
    return


if __name__ == "__main__":
    app.run()
