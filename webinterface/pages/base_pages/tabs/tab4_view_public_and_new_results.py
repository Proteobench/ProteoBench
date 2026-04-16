"""
Generic Tab 4: Display Results (Submitted Data)

This module provides a unified interface for displaying submitted benchmark results
across all ProteoBench module types (Quant, De Novo, etc.).
"""

import uuid
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st
import streamlit_utils

from ..utils.general import clean_dataframe_for_export


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


def initialize_submitted_slider(slider_id_uuid: str, default_val_slider: int) -> None:
    """Initialize the submitted slider state with UUID and default value."""
    initialize_uuid_state(slider_id_uuid, default_val_slider)


def generate_submitted_slider(variables) -> None:
    """Generate the slider for filtering submitted data."""
    if not hasattr(variables, "slider_id_submitted_uuid"):
        return  # Module doesn't use sliders

    slider_uuid = st.session_state[variables.slider_id_submitted_uuid]
    help_text = getattr(variables.texts.Help, "slider", None) if hasattr(variables, "texts") else None
    st.slider(
        "Minimum number of precursors per protein group",
        1,
        10,
        key=slider_uuid,
        help=help_text,
    )


def generate_submitted_selectbox(variables) -> None:
    """Generate the selectbox for submitted data label selection."""
    # Initialize if not already done
    if variables.selectbox_id_submitted_uuid not in st.session_state:
        st.session_state[variables.selectbox_id_submitted_uuid] = uuid.uuid4()

    selectbox_uuid = st.session_state[variables.selectbox_id_submitted_uuid]

    # Initialize the selectbox value if not present
    if selectbox_uuid not in st.session_state:
        st.session_state[selectbox_uuid] = "None"

    help_text = getattr(variables.texts.Help, "selectbox", None) if hasattr(variables, "texts") else None
    st.selectbox(
        "Select label",
        variables.metric_plot_labels,
        key=selectbox_uuid,
        help=help_text,
    )


def initialize_submitted_data_points(variables, ionmodule) -> None:
    """
    Initialize the submitted datapoints in the session state.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    ionmodule : object
        The module instance with obtain_all_data_points method.
    """
    if variables.all_datapoints_submitted not in st.session_state:
        st.session_state[variables.all_datapoints_submitted] = None
        st.session_state[variables.all_datapoints_submitted] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables.all_datapoints_submitted]
        )


def filter_submitted_data_if_applicable(variables, ionmodule, use_slider: bool = True) -> pd.DataFrame:
    """
    Filter submitted data using module-specific filtering logic.

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
        return st.session_state[variables.all_datapoints_submitted]

    # Slider-based filtering (Quant modules)
    if hasattr(variables, "slider_id_submitted_uuid"):
        slider_key = st.session_state.get(variables.slider_id_submitted_uuid)
        filter_value = st.session_state.get(slider_key, 3)
        return ionmodule.filter_data_point(st.session_state[variables.all_datapoints_submitted], filter_value)

    return st.session_state[variables.all_datapoints_submitted]


def render_submitted_results_table(
    data: pd.DataFrame, table_style: str = "dataframe", column_config: Optional[Dict] = None
) -> None:
    """
    Render the submitted results table with configurable styling and download button.

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
        st.info("No submitted datapoints available to display.", icon="ℹ️")
        return

    st.subheader("Submitted Benchmark Results")

    if table_style == "aggrid":
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
            st.dataframe(data, width='stretch', hide_index=True, column_config=column_config)
    else:
        st.dataframe(data, width='stretch', hide_index=True, column_config=column_config)

    # Add download button for the results table
    random_uuid = uuid.uuid4()
    # Clean data for CSV export (replace newlines with spaces)
    cleaned_data = clean_dataframe_for_export(data)
    st.download_button(
        label="Download table",
        data=streamlit_utils.save_dataframe(cleaned_data),
        file_name="submitted_benchmark_results.csv",
        mime="text/csv",
        key=f"tab4_download_{random_uuid}",
        icon=":material/download:",
    )


def display_submitted_results(
    variables,
    ionmodule,
    plot_params: Dict[str, Any],
    table_style: str = "dataframe",
    column_config: Optional[Dict] = None,
) -> None:
    """
    Display submitted benchmark results with plot and table.

    This is the main entry point for Tab 4, working across all module types.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        The module instance (Quant, De Novo, etc.).
    plot_params : Dict[str, Any]
        Module-specific plotting parameters.
    table_style : str, optional
        Table rendering style ("dataframe" or "aggrid").
    column_config : Optional[Dict], optional
        Streamlit column configuration for dataframe display.
    """
    # Initialize submitted data
    initialize_submitted_data_points(variables, ionmodule)

    # Filter data using slider if applicable
    filtered_data = filter_submitted_data_if_applicable(variables, ionmodule, use_slider=True)

    # Get plot generator from module
    plot_generator = ionmodule.get_plot_generator()

    # Prepare plot key
    fig_key = variables.fig_metric_submitted if hasattr(variables, "fig_metric_submitted") else "submitted_plot"
    if fig_key not in st.session_state:
        st.session_state[fig_key] = uuid.uuid4()
    plot_uuid = st.session_state[fig_key]

    try:
        # Generate plot using plot_generator interface
        fig = plot_generator.plot_main_metric(
            result_df=filtered_data,
            hide_annot=plot_params.get("hide_annot", False),
            **plot_params,
        )
        st.plotly_chart(fig, width='stretch', key=plot_uuid)
    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
        import traceback

        with st.expander("Error details"):
            st.code(traceback.format_exc())

    # Render results table
    render_submitted_results_table(filtered_data, table_style, column_config)
