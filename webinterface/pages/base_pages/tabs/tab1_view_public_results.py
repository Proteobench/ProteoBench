"""
Generic Tab 1: Results Display (All Data)

This module provides a unified interface for displaying benchmark results
across all ProteoBench module types (Quant, De Novo, etc.).
"""

import os
import uuid
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import streamlit as st
import streamlit_utils

from ..utils.general import clean_dataframe_for_export
from ..utils.metricplot import render_metric_plot
from ..utils.resulttable import configure_aggrid, prepare_display_dataframe, render_aggrid


from ..utils.parameter_filters import (  # noqa: F401
    apply_parameter_filters,
    generate_parameter_filters,
)
from ..utils.resulttable import add_open_source_column


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


def initialize_main_data_points(variables, ionmodule) -> None:
    """
    Initialize the all_datapoints variable in the session state.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    ionmodule : object
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


def generate_main_slider(
    slider_id_uuid: str, description_slider_md: str, default_val_slider: float, max_nr_observed: int = 6
) -> None:
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
    return st.radio(
        "Select metric",
        ["Median", "Mean"],
        help=help_text,
        horizontal=True,
    )


def display_metric_calc_approach_selector(variables) -> str:
    """Display metric calculation approach selector and return selected mode."""
    help_text = getattr(variables.texts.Help, "radio_mode", None) if hasattr(variables, "texts") else None
    return st.radio(
        "Select metric calculation approach",
        ["Species-weighted", "Global"],
        help=help_text,
        horizontal=True,
    )


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
    key = (
        variables.colorblind_mode_selector_submitted_uuid if use_submitted else variables.colorblind_mode_selector_uuid
    )
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
        return st.session_state[variables.all_datapoints]

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

    with st.container(key="tour_metric_plot"):
        try:
            fig = plot_generator.plot_main_metric(
                result_df=data, hide_annot=plot_params.get("hide_annot", False), annotation=annotation, **plot_params
            )
            st.plotly_chart(fig, use_container_width=True, key=plot_uuid)
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
            import traceback

            with st.expander("Error details"):
                st.code(traceback.format_exc())


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

    downloads_df = st.session_state[variables.all_datapoints][["id", "intermediate_hash"]].copy()
    downloads_df = downloads_df.sort_values(sort_by, ascending=False)
    downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

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

    st.subheader("Download all data from a submitted workflow")

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
        st.info(
            "Storage directory is not configured. Set `storage.dir` in secrets.toml to enable downloads.", icon="ℹ️"
        )


def display_existing_results(
    variables,
    ionmodule,
    plot_params: Dict[str, Any],
    use_slider: bool = True,
    table_style: str = "aggrid",
    column_config: Optional[Dict] = None,
) -> None:
    """
    Main orchestration function for Tab 1: plot + interactive table with bidirectional
    highlight synchronisation.

    Clicking a point in the scatter plot highlights the matching row in the table.
    Clicking a row in the table highlights the matching point in the scatter plot.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        The module instance (Quant, De Novo, etc.).
    plot_params : Dict[str, Any]
        Module-specific plotting parameters passed straight through to render_metric_plot
        (and on to plot_main_metric). alpha_warning and beta_warning are consumed here.
    use_slider : bool, optional
        Whether to use slider-based filtering (default True for Quant).
    table_style : str, optional
        Reserved; AgGrid is always used.
    column_config : Optional[Dict], optional
        Reserved for future st.dataframe column configuration.
    """
    initialize_main_data_points(variables, ionmodule)
    filtered_data = filter_data_if_applicable(variables, ionmodule, use_slider)
    filtered_data = add_open_source_column(filtered_data)

    # Apply parameter-based filters (key_prefix must be unique per module page)
    filtered_data = generate_parameter_filters(filtered_data, key_prefix=f"param_filter_{variables.all_datapoints}")

    # Get plot generator from module
    plot_generator = ionmodule.get_plot_generator()

    # --- Session state keys for bidirectional selection ---
    # highlight_key : ProteoBench ID currently highlighted in both widgets
    # plot_key_id   : key -> UUID used for the Plotly chart; regenerating clears Plotly selection
    # agrid_key_id  : key -> UUID used for the AgGrid;       regenerating clears row selection
    highlight_key = f"{variables.fig_metric}_tab1_highlight_id"
    plot_key_id = variables.fig_metric
    agrid_key_id = f"{variables.fig_metric}_tab1_aggrid_key"

    if plot_key_id not in st.session_state:
        st.session_state[plot_key_id] = uuid.uuid4()
    if agrid_key_id not in st.session_state:
        st.session_state[agrid_key_id] = uuid.uuid4()

    highlight_id = st.session_state.get(highlight_key, None)

    # Stamp the Highlight column so plot_main_metric renders the highlighted point
    # with a distinct colour and larger marker (both HYE and de novo generators respect this).
    data_for_plot = filtered_data.copy()
    if "Highlight" not in data_for_plot.columns:
        data_for_plot["Highlight"] = False
    data_for_plot["Highlight"] = data_for_plot["id"] == highlight_id

    # Build annotation and strip meta-keys before forwarding to render_metric_plot.
    annotation = ""
    if plot_params.get("beta_warning"):
        annotation = "-Beta-"
    elif plot_params.get("alpha_warning"):
        annotation = "-Alpha-"

    consumed_keys = {"alpha_warning", "beta_warning", "metric", "mode", "label", "colorblind_mode"}
    extra_plot_kwargs = {k: v for k, v in plot_params.items() if k not in consumed_keys}

    # --- Render plot via the shared utility; get the clicked point ID ---
    plot_clicked_id = render_metric_plot(
        data=data_for_plot,
        key=st.session_state[plot_key_id],
        plot_generator=plot_generator,
        metric=plot_params.get("metric"),
        mode=plot_params.get("mode"),
        label=plot_params.get("label", "None"),
        colorblind_mode=plot_params.get("colorblind_mode", False),
        annotation=annotation,
        **extra_plot_kwargs,
    )

    if plot_clicked_id is not None and plot_clicked_id != highlight_id:
        st.session_state[highlight_key] = plot_clicked_id
        st.session_state[agrid_key_id] = uuid.uuid4()
        st.rerun(scope="fragment")

    # --- Render table via shared utilities ---
    with st.container(key="tour_results_table"):
        st.subheader("Benchmark Results")
        df_display = prepare_display_dataframe(filtered_data, highlight_id)
        grid_options = configure_aggrid(df_display, enable_selection=True)
        grid_response = render_aggrid(
            df_display,
            grid_options,
            key=st.session_state[agrid_key_id],
            enable_selection=True,
        )

        st.download_button(
            label="Download table",
            data=streamlit_utils.save_dataframe(clean_dataframe_for_export(df_display)),
            file_name="benchmark_results.csv",
            mime="text/csv",
            key=f"tab1_download_table_{variables.fig_metric}",
            icon=":material/download:",
        )

    if grid_response is not None:
        selected_rows = grid_response.selected_rows
        selected_id = None
        if selected_rows is not None:
            if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
                selected_id = selected_rows.iloc[0].get("id")
            elif isinstance(selected_rows, list) and len(selected_rows) > 0:
                selected_id = selected_rows[0].get("id")

    # Display download section
    with st.container(key="tour_download_section"):
        display_download_section(variables)
