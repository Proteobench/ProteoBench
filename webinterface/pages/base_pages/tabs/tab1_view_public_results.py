"""
Generic Tab 1: Results Display (All Data)

This module provides a unified interface for displaying benchmark results
across all ProteoBench module types (Quant, De Novo, etc.).
"""

import os
import uuid
from typing import Any, Callable, Dict, Optional

import pandas as pd
import streamlit as st


def initialize_uuid_state(key: str, default_value: Any = None) -> None:
    """
    Initialize a UUID-based state key with an optional default value.

    Parameters
    ----------
    key : str
        The session state key to initialize.
    default_value : Any, optional
        The default value to associate with the generated UUID.
    """
    if key not in st.session_state:
        st.session_state[key] = uuid.uuid4()

    if default_value is not None:
        uuid_key = st.session_state[key]
        if uuid_key not in st.session_state:
            st.session_state[uuid_key] = default_value


def initialize_main_data_points(variables, ionmodule: Callable) -> None:
    """
    Initialize the all_datapoints variable in the session state.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    ionmodule : Callable
        The module instance with obtain_all_data_points method.
    """
    if variables.all_datapoints not in st.session_state:
        st.session_state[variables.all_datapoints] = None
        st.session_state[variables.all_datapoints] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables.all_datapoints]
        )


# UI Control Functions


def initialize_main_slider(slider_id_uuid: str, default_val_slider: int) -> None:
    """Initialize the slider state with UUID and default value."""
    initialize_uuid_state(slider_id_uuid, default_val_slider)


def generate_main_slider(slider_id_uuid: str, description_slider_md: str, default_val_slider: float, max_nr_observed: int = 6) -> None:
    """
    Create a slider input.
    
    Parameters
    ----------
    slider_id_uuid : str
        UUID for the slider state key
    description_slider_md : str
        Path to markdown file with slider description
    default_val_slider : float
        Default value for the slider
    max_nr_observed : int, optional
        Maximum value for the slider range (default 6)
    """
    # key for slider_uuid in session state
    if slider_id_uuid not in st.session_state:
        st.session_state[slider_id_uuid] = uuid.uuid4()
    slider_key = st.session_state[slider_id_uuid]

    default_value = st.session_state.get(slider_key, default_val_slider)
    
    # Generate slider options based on max_nr_observed
    slider_options = list(range(1, max_nr_observed + 1))
    
    st.select_slider(
        label="Minimal precursor quantifications (# samples)",
        options=slider_options,
        value=default_value,
        key=slider_key,
        help="Use the slider to set the minimum number of raw files in which a precursor must be quantified (e.g., 3 = ≥3 files).",
    )


def initialize_radio(radio_id_uuid: str, default_value: str) -> None:
    """Initialize radio button state with UUID and default value."""
    initialize_uuid_state(radio_id_uuid, default_value)


def generate_main_radio(radio_id_uuid: str, description: str, options: list, help: str = None) -> None:
    """Generate a radio button selector."""
    radio_uuid = st.session_state[radio_id_uuid]
    st.radio(description, options, key=radio_uuid, help=help)


def initialize_main_selectbox(selectbox_id_uuid: str, default_value: str = "None") -> None:
    """Initialize the selectbox state with UUID and default value."""
    initialize_uuid_state(selectbox_id_uuid, default_value)


def generate_main_selectbox(variables, selectbox_id_uuid: str) -> None:
    """Generate the main selectbox for label selection."""
    selectbox_uuid = st.session_state[selectbox_id_uuid]

    # Get help text if available
    help_text = getattr(variables.texts.Help, "selectbox", None) if hasattr(variables, "texts") else None

    st.selectbox(
        "Select label",
        variables.metric_plot_labels,
        key=selectbox_uuid,
        help=help_text,
    )


def display_metric_selector(variables) -> str:
    """Display metric selector and return selected metric."""
    help_text = getattr(variables.texts.Help, "radio_metric", None) if hasattr(variables, "texts") else None
    metric = st.radio(
        "Select metric",
        ["Median", "Mean"],
        help=help_text,
        horizontal=True,
    )
    return metric


def display_metric_calc_approach_selector(variables) -> str:
    """Display metric calculation approach selector and return selected mode."""
    help_text = getattr(variables.texts.Help, "radio_mode", None) if hasattr(variables, "texts") else None
    mode = st.radio(
        "Select metric calculation approach",
        ["Species-weighted", "Global"],
        help=help_text,
        horizontal=True,
    )
    return mode


def display_colorblindmode_selector(variables, use_submitted: bool = False) -> str:
    """Display colorblind mode selector toggle.
    
    Parameters
    ----------
    variables : VariablesClass
        Variables object containing selector UUIDs
    use_submitted : bool, optional
        If True, use the submitted selector UUID, by default False
    
    Returns
    -------
    bool
        Current state of the colorblind mode toggle
    """
    key = variables.colorblind_mode_selector_submitted_uuid if use_submitted else variables.colorblind_mode_selector_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    return st.toggle(
        "Colorblind Mode",
        help="Toggle colorblind mode on or off.",
        key=_id_of_key,
    )


def filter_data_if_applicable(variables, ionmodule, use_slider: bool = True) -> pd.DataFrame:
    """
    Filter data using module-specific filtering logic.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    ionmodule : object
        The module instance with filter_data_point method.
    use_slider : bool, optional
        Whether to use slider-based filtering (Quant) or return all data (De Novo).

    Returns
    -------
    pd.DataFrame
        Filtered or unfiltered data points.
    """
    if not use_slider or not hasattr(ionmodule, "filter_data_point"):
        # No filtering for this module type
        return st.session_state[variables.all_datapoints]

    # Slider-based filtering (Quant modules)
    if hasattr(variables, "slider_id_uuid"):
        slider_key = st.session_state.get(variables.slider_id_uuid)
        filter_value = st.session_state.get(slider_key, 3)
        return ionmodule.filter_data_point(st.session_state[variables.all_datapoints], filter_value)

    return st.session_state[variables.all_datapoints]


def render_main_plot(plot_generator, data: pd.DataFrame, variables, plot_params: Dict[str, Any]) -> None:
    """
    Render the main metric plot using the module's plot generator.

    Parameters
    ----------
    plot_generator : PlotGeneratorBase
        The plot generator instance from the module.
    data : pd.DataFrame
        The data to plot.
    variables : object
        Variables object containing session state keys.
    plot_params : Dict[str, Any]
        Module-specific parameters for plotting (label, metric, mode, etc.).
    """
    # Prepare plot key
    key = variables.fig_metric if hasattr(variables, "fig_metric") else "main_plot"
    if key not in st.session_state:
        st.session_state[key] = uuid.uuid4()
    plot_uuid = st.session_state[key]

    # Build annotation text based on alpha/beta warnings
    annotation = ""
    if plot_params.get("beta_warning", False):
        annotation = "-Beta-"
    elif plot_params.get("alpha_warning", False):
        annotation = "-Alpha-"

    try:
        fig = plot_generator.plot_main_metric(
            result_df=data, 
            hide_annot=plot_params.get("hide_annot", False),
            annotation=annotation,
            **plot_params
        )
        st.plotly_chart(fig, use_container_width=True, key=plot_uuid)
    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
        import traceback

        with st.expander("Error details"):
            st.code(traceback.format_exc())


def render_results_table(
    data: pd.DataFrame, table_style: str = "dataframe", column_config: Optional[Dict] = None
) -> None:
    """
    Render the results table with configurable styling.

    Parameters
    ----------
    data : pd.DataFrame
        The data to display.
    table_style : str, optional
        The table rendering style ("dataframe" or "aggrid").
    column_config : Optional[Dict], optional
        Streamlit column configuration for enhanced display.
    """
    if len(data) == 0:
        st.info("No datapoints available to display.", icon="ℹ️")
        return

    st.subheader("Benchmark Results")

    if table_style == "aggrid":
        # Import AgGrid only if needed
        try:
            from st_aggrid import AgGrid, GridOptionsBuilder

            gb = GridOptionsBuilder.from_dataframe(data)
            gb.configure_default_column(
                filterable=True,
                groupable=False,
                sorteable=True,
                editable=False,
            )
            grid_options = gb.build()
            AgGrid(data, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)
        except ImportError:
            st.warning("AgGrid not available, falling back to dataframe", icon="⚠️")
            st.dataframe(data, use_container_width=True, hide_index=True, column_config=column_config)
    else:
        # Standard dataframe display
        st.dataframe(data, use_container_width=True, hide_index=True, column_config=column_config)


def display_download_section(variables, sort_by: str = "id") -> None:
    """
    Render the download section for raw datasets.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    sort_by : str, optional
        Column to sort the download options by.
    """
    if len(st.session_state[variables.all_datapoints]) == 0:
        st.error("No data available for download.", icon="🚨")
        return

    # Prepare downloads dataframe
    downloads_df = st.session_state[variables.all_datapoints][["id", "intermediate_hash"]].copy()
    downloads_df = downloads_df.sort_values(sort_by, ascending=False)
    downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

    # Initialize UUID state
    if (
        not hasattr(variables, "placeholder_downloads_container")
        or variables.placeholder_downloads_container not in st.session_state
    ):
        if hasattr(variables, "placeholder_downloads_container"):
            st.session_state[variables.placeholder_downloads_container] = st.empty()

    if (
        not hasattr(variables, "download_selector_id_uuid")
        or variables.download_selector_id_uuid not in st.session_state
    ):
        if hasattr(variables, "download_selector_id_uuid"):
            st.session_state[variables.download_selector_id_uuid] = uuid.uuid4()

    st.subheader("Download raw datasets")

    # Create selectbox key
    selector_key = st.session_state.get(
        getattr(variables, "download_selector_id_uuid", "download_selector"), "download_selector"
    )

    selected_hash = st.selectbox(
        "Select dataset (sorted by most recent)",
        downloads_df["intermediate_hash"],
        index=None,
        key=selector_key,
        format_func=lambda x: downloads_df["id"][x] if x in downloads_df.index else x,
    )

    # Handle file downloads
    if selected_hash is not None and "storage" in st.secrets and st.secrets["storage"]["dir"] is not None:
        dataset_path = os.path.join(st.secrets["storage"]["dir"], selected_hash)
        if os.path.isdir(dataset_path):
            files = os.listdir(dataset_path)
            if files:
                st.write(f"Available files for dataset `{downloads_df['id'][selected_hash]}`:")
                for file_name in sorted(files):
                    path_to_file = os.path.join(dataset_path, file_name)
                    with open(path_to_file, "rb") as file:
                        st.download_button(
                            label=f"📥 {file_name}",
                            data=file,
                            file_name=file_name,
                            key=f"download_{selected_hash}_{file_name}",
                        )
            else:
                st.info("No files available in this dataset directory.", icon="ℹ️")
        else:
            st.warning(
                f"Directory for dataset `{downloads_df['id'][selected_hash]}` does not exist. "
                "This may indicate the data has not been uploaded or archived.",
                icon="⚠️",
            )
    elif selected_hash is not None:
        st.info("Storage directory is not configured. Set `storage.dir` in secrets.toml to enable downloads.", icon="ℹ️")


def display_existing_results(
    variables,
    ionmodule,
    plot_params: Dict[str, Any],
    use_slider: bool = True,
    table_style: str = "dataframe",
    column_config: Optional[Dict] = None,
) -> None:
    """
    Main orchestration function for displaying benchmark results.

    This is the primary entry point for Tab 1, working across all module types.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        The module instance (Quant, De Novo, etc.).
    plot_params : Dict[str, Any]
        Module-specific plotting parameters (label, metric, level, etc.).
    use_slider : bool, optional
        Whether to use slider-based filtering (default True for Quant).
    table_style : str, optional
        Table rendering style ("dataframe" or "aggrid").
    column_config : Optional[Dict], optional
        Streamlit column configuration for dataframe display.
    """
    # Initialize and filter data
    initialize_main_data_points(variables, ionmodule)
    filtered_data = filter_data_if_applicable(variables, ionmodule, use_slider)

    # Get plot generator from module
    plot_generator = ionmodule.get_plot_generator()

    # Render main plot
    render_main_plot(plot_generator, filtered_data, variables, plot_params)

    # Render results table
    render_results_table(filtered_data, table_style, column_config)

    # Display download section
    display_download_section(variables)
