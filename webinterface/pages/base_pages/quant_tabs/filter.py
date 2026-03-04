from typing import Callable

import pandas as pd
import streamlit as st


def filter_data_using_slider(
    slider_id_uuid: str,
    all_datapoints: str,  # Session state key for the datapoints, not the DataFrame itself
    filter_data_point: Callable,
) -> pd.DataFrame:
    """
    Filter the data points based on the slider value.

    Returns
    -------
    pandas.DataFrame
        The filtered data points.
    """

    if slider_id_uuid not in st.session_state:
        print(f"Debug: slider_id_uuid '{slider_id_uuid}' not found in session state")
        print(f"Debug: Available keys in session state: {list(st.session_state.keys())}")
        return pd.DataFrame()

    if all_datapoints not in st.session_state:
        print(f"Debug: all_datapoints key '{all_datapoints}' not found in session state")
        return pd.DataFrame()

    # Get the slider key (UUID) from session state
    slider_key = st.session_state[slider_id_uuid]

    if slider_key not in st.session_state:
        print(f"Debug: slider_key '{slider_key}' not found in session state")
        return pd.DataFrame()

    # Get the datapoints and slider value
    datapoints = st.session_state[all_datapoints]
    slider_value = st.session_state[slider_key]

    if datapoints is None or (isinstance(datapoints, pd.DataFrame) and datapoints.empty):
        print("Debug: No datapoints available for filtering")
        print(f"Debug: datapoints type: {type(datapoints)}, value: {datapoints}")
        return pd.DataFrame()

    # Apply the filter
    filtered_result = filter_data_point(datapoints, slider_value)

    return filtered_result
