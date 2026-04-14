import marimo

__generated_with = "0.23.1"
app = marimo.App()


app._unparsable_cell(
    r"""
    ---
    jupyter: python3
    execute:
      enabled: true    # make sure cells are executed
      warning: false   # ⟵ don’t include any warnings in output
      message: false   # ⟵ also hides messages, if you want
    format:
      html: default
    ---
    """,
    name="_"
)


@app.cell
def _():
    import pandas as pd
    import ipywidgets as widgets
    from IPython.display import display
    import requests
    from bs4 import BeautifulSoup
    import os
    import zipfile
    from tqdm import tqdm
    from pathlib import Path

    import json

    from collections import defaultdict
    import toml

    from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive
    from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
    from proteobench.plotting import plot_quant
    from proteobench.io.parsing.parse_ion import load_input_file
    from proteobench.modules.constants import MODULE_SETTINGS_DIRS

    return (
        DDAQuantIonModuleQExactive,
        MODULE_SETTINGS_DIRS,
        ParseSettingsBuilder,
        defaultdict,
        display,
        load_input_file,
        os,
        pd,
        plot_quant,
        widgets,
    )


@app.cell
def _(os):
    from proteobench.utils.server_io import get_merged_json
    df = get_merged_json(repo_url="https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip")
    df.shape

    proteobench_directory = os.path.abspath("../../../../../../../")
    print(proteobench_directory)
    return df, proteobench_directory


@app.cell
def _(df, os):
    from proteobench.utils.server_io import get_raw_data


    def get_datasets_to_downlod(df, output_directory="temp_results"):
        """
        Check which datasets from the DataFrame need to be downloaded.
    
        Args:
            df: DataFrame containing intermediate_hash column
            output_directory: Directory where datasets are stored
        
        Returns:
            Tuple containing:
            - DataFrame containing only rows that need to be downloaded
            - Dictionary mapping intermediate_hash to directory paths
        """
        # Extract hash list from DataFrame 
        hash_list = df["intermediate_hash"].tolist()
    
        # Check which hashes already exist and build hash->dir mapping
        existing_hashes = []
        hash_vis_dir = {}
    
        if os.path.exists(output_directory):
            for hash_dir in os.listdir(output_directory):
                if hash_dir in hash_list:
                    existing_hashes.append(hash_dir)
                    hash_vis_dir[hash_dir] = os.path.join(output_directory, hash_dir)

        if existing_hashes:
            df_to_download = df[~df["intermediate_hash"].isin(existing_hashes)]
            return df_to_download, hash_vis_dir
        else:
            return df, hash_vis_dir

    # Get DataFrame of datasets that need downloading
    df_to_download, hash_vis_dirs = get_datasets_to_downlod(df,output_directory="temp_results")

    df_to_download.shape
    return df_to_download, get_raw_data, hash_vis_dirs


@app.cell
def _(hash_vis_dirs):
    hash_vis_dirs
    return


@app.cell
def _(df, df_to_download, get_raw_data, hash_vis_dirs):
    if df_to_download.shape[0] > 0:
        hash_vis_dirs_2 = get_raw_data(df_to_download, base_url='https://proteobench.cubimed.rub.de/datasets/', output_directory='temp_results')
        hash_vis_dirs.update(hash_vis_dirs_2)  # append hash_vis_dir_2 to hash_vis_dir
    for idx, row in df.iterrows():
        if row['intermediate_hash'] not in hash_vis_dirs:
    #check that all df["intermediate_hash"] are in hash_vis_dirs
    # remove them if they are not in hash_vis_dirs
            print(f'intermediate_hash {row['intermediate_hash']} not in hash_vis_dirs')
    df_1 = df[df['intermediate_hash'].isin(hash_vis_dirs)]
    return (df_1,)


@app.cell
def _(df_1, display, widgets):
    #%%script false --no-raise-error
    if False:
        row_selector = widgets.SelectMultiple(options=[(f'{row['id']} (hash: {row['intermediate_hash']}, submission comments: {row['submission_comments']})', idx) for idx, row in df_1.iterrows()], description='Select Rows:', rows=10, layout=widgets.Layout(width='50%'))  # Create a SelectMultiple widget with names as options
        button = widgets.Button(description='Filter Rows')
        output = widgets.Output()

        def on_button_click(b):  # Number of visible rows in the widget
            with output:  # Adjust layout as needed
                output.clear_output()
                selected_indices = list(row_selector.value)
                global filtered_df  # Button to confirm selection
                filtered_df = df_1.iloc[selected_indices]
                print('Filtered DataFrame:')
                display(filtered_df)  # Output widget to display the filtered DataFrame
        button.on_click(on_button_click)
        display(row_selector, button, output)
    else:  # Callback for filtering rows
        filtered_df = df_1  # Store filtered DataFrame globally  # Attach callback  # Display the widgets
    return (filtered_df,)


@app.cell
def _(filtered_df, hash_vis_dirs):
    location = hash_vis_dirs[filtered_df["intermediate_hash"].iloc[0]]
    #filtered_df["intermediate_hash"].iloc[0]
    #hash_vis_dirs
    return (location,)


@app.cell
def _(
    DDAQuantIonModuleQExactive,
    ParseSettingsBuilder,
    defaultdict,
    filtered_df,
    location,
    os,
    plot_quant,
    proteobench_directory,
):
    software_name = filtered_df["software_name"].iloc[0]

    # List all files in the directory
    all_files = os.listdir(location)

    # Filter for files that start with 'input_file' and ignore their extensions
    matching_file = os.path.join(location,[f for f in all_files if f.startswith('input_file') and os.path.isfile(os.path.join(location, f))][0])
    matching_file_params = os.path.join(location,[f for f in all_files if f.startswith('param') and os.path.isfile(os.path.join(location, f))][0])

    user_config = defaultdict(lambda: "")

    module_obj = DDAQuantIonModuleQExactive(token="")
    #results_df = module_obj.obtain_all_data_points(all_datapoints=None)

    results_performance, all_datapoints, result_df = module_obj.benchmarking(
        matching_file, software_name, user_input=user_config, all_datapoints=[]
    )

    fig1 = plot_quant.PlotDataPoint.plot_CV_violinplot(results_performance)
    fig1.show()

    parse_settings = ParseSettingsBuilder(
                    parse_settings_dir=f"{proteobench_directory}/proteobench/io/parsing/io_parse_settings/Quant/lfq/DDA/ion/QExactive", module_id="quant_lfq_DDA_ion_QExactive"
                ).build_parser(software_name)

    fig2 = plot_quant.PlotDataPoint.plot_fold_change_histogram(results_performance,parse_settings.species_expected_ratio())
    fig2.show()
    return


@app.cell
def _(
    DDAQuantIonModuleQExactive,
    MODULE_SETTINGS_DIRS,
    ParseSettingsBuilder,
    defaultdict,
    df_1,
    hash_vis_dirs,
    load_input_file,
    os,
):
    import time
    performance_dict = {}
    timings = {}
    # select 5 random rows from df
    #filtered_df = df#.sample(5)
    # Filter for specific software names
    valid_software_names = ['ProlineStudio', 'FragPipe', 'MSAngel']
    filtered_df_1 = df_1[df_1['software_name'].isin(valid_software_names)]
    for idx_1, row_1 in filtered_df_1.iterrows():
        location_1 = hash_vis_dirs[row_1['intermediate_hash']]
        software_name_1 = row_1['software_name']
        all_files_1 = os.listdir(location_1)
        if len(all_files_1) == 0:
            print(f'Directory {location_1} is empty.')
            continue  # List all files in the directory
        matching_file_1 = os.path.join(location_1, [f for f in all_files_1 if f.startswith('input_file') and os.path.isfile(os.path.join(location_1, f))][0])
        matching_file_params_1 = os.path.join(location_1, [f for f in all_files_1 if f.startswith('param') and os.path.isfile(os.path.join(location_1, f))][0])
        user_config_1 = defaultdict(lambda: '')
        module_obj_1 = DDAQuantIonModuleQExactive(token='')
        start_time = time.time()
        input_df = load_input_file(matching_file_1, software_name_1)  # Filter for files that start with 'input_file' and ignore their extensions
        end_time = time.time()
        load_time = end_time - start_time
        print(f'Time to load {software_name_1} input file: {load_time:.2f} seconds')
        parse_settings_1 = ParseSettingsBuilder(parse_settings_dir=MODULE_SETTINGS_DIRS['quant_lfq_DDA_ion_QExactive'], module_id='quant_lfq_DDA_ion_QExactive').build_parser(software_name_1)
        start_time = time.time()
        standard_format, replicate_to_raw = parse_settings_1.convert_to_standard_format(input_df)
        end_time = time.time()
        conversion_time = end_time - start_time
        print(f'Time to convert {software_name_1} to standard format: {conversion_time:.2f} seconds')
        replicate_to_raw = parse_settings_1._create_replicate_mapping()
        runs = replicate_to_raw['A']  # time loading input file
        runs.extend(replicate_to_raw['B'])
        start_time = time.time()
        results_performance_1, all_datapoints_1, result_df_1 = module_obj_1.benchmarking(matching_file_1, software_name_1, user_input=user_config_1, all_datapoints=[])
        end_time = time.time()
        benchmarking_time = end_time - start_time
        print(f'Time to benchmark {software_name_1}: {benchmarking_time:.2f} seconds')
        results_performance_runs = results_performance_1.loc[:, runs]
        total_missing = results_performance_1.loc[:, runs].isna().sum().sum()
        total_peptide_ions = results_performance_runs.shape[0]
        total_runs = results_performance_runs.shape[1]
        total_max = total_peptide_ions * total_runs  # Benchmark convert_to_standard_format
    # collect all timing data into a dataframe
        performance_dict[row_1['id']] = {'software_name': software_name_1, 'total_missing': total_missing, 'total_max': total_max, 'total_peptide_ions': total_peptide_ions, 'total_runs': total_runs, 'total_missing_ratio': total_missing / total_max, 'total_missing_percentage': total_missing / total_max * 100, 'benchmarking_time': benchmarking_time, 'load_time': load_time, 'conversion_time': conversion_time, 'locations': location_1}  # time benchmarking  #timings[row["id"]] = timing
    return (performance_dict,)


@app.cell
def _(pd, performance_dict):
    performance_df = pd.DataFrame(performance_dict).T
    performance_df
    return (performance_df,)


@app.cell
def _(performance_df):
    # Calculate pure benchmarking time by subtracting load and conversion times
    performance_df['pure_benchmarking_time'] = performance_df['benchmarking_time'] - ((performance_df['load_time'] + performance_df['conversion_time']))
    # Save performance DataFrame to TSV file in same directory as notebook
    performance_df.to_csv('performance_metrics_new.tsv', sep='\t', index=True)

    # Confirm you have >1 category
    print(performance_df["software_name"].nunique(), performance_df["software_name"].unique())
    return


@app.cell
def _(performance_df):
    import plotly.express as px
    import plotly.io as pio
    pio.templates.default = "plotly"     # the default Plotly template


    def create_scatter_plot(performance_df, x_column="total_peptide_ions", y_column="pure_benchmarking_time",
                            title="Benchmarking Time vs Total Peptide Ions by Software"):
        # Create the scatter plot
        fig = px.scatter(
            performance_df,
            x=x_column,
            y=y_column,
            color='software_name',
            labels={
                'total_peptide_ions': 'Total Peptide Ions',
                'benchmarking_time': 'Benchmarking Time (s)',
                'software_name': 'Software'
            },
            title=title
        )

        fig.update_layout(hovermode='closest')
        fig.show()

    create_scatter_plot(performance_df, x_column="total_peptide_ions", y_column="pure_benchmarking_time")
    return create_scatter_plot, pio, px


@app.cell
def _(create_scatter_plot, performance_df, pio):
    pio.templates.default = 'plotly'
    create_scatter_plot(performance_df, x_column='total_peptide_ions', y_column='load_time', title='Load Time vs Total Peptide Ions by Software')  # the default Plotly template
    return


@app.cell
def _(create_scatter_plot, performance_df):
    create_scatter_plot(performance_df, x_column="total_peptide_ions",
                        y_column="conversion_time",
                        title="Load Time vs Total Peptide Ions by Software")
    return


@app.cell
def _(performance_df, px):
    performance_df['IDX'] = performance_df.index
    fig = px.scatter(performance_df, x='total_peptide_ions', y='total_missing_percentage', hover_name='IDX', labels={'total_missing': 'Total Missing', 'total_missing_percentage': 'Total Missing Percentage'}, title='Interactive Scatter Plot of Missing Data')
    # Creating an interactive scatter plot using Plotly
    fig.update_layout(hovermode='closest')
    fig.show()
    return


@app.cell
def _(performance_df, px):
    performance_df['IDX'] = performance_df.index
    fig_1 = px.scatter(performance_df, x='total_missing', y='total_missing_percentage', hover_name='IDX', labels={'total_missing': 'Total Missing', 'total_missing_percentage': 'Total Missing Percentage'}, title='Interactive Scatter Plot of Missing Data')
    fig_1.update_layout(hovermode='closest')
    # Creating an interactive scatter plot using Plotly
    fig_1.show()
    return


if __name__ == "__main__":
    app.run()
