from typing import Callable

import pandas as pd
import streamlit as st


# TOCHECK: not used?
def filter_data_using_slider(
    slider_id_uuid: str,
    all_datapoints: pd.DataFrame,
    filter_data_point: Callable,
) -> pd.DataFrame:
    """
    Filter the data points based on the slider value.

    Returns
    -------
    pandas.DataFrame
        The filtered data points.
    """
    if slider_id_uuid in st.session_state.keys():
        return filter_data_point(
            st.session_state[all_datapoints],
            st.session_state[st.session_state[slider_id_uuid]],
        )


def clean_dataframe_for_export(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataframe for CSV export by replacing newlines in text fields.

    Parameters
    ----------
    data : pd.DataFrame
        The data to clean.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with newlines and commas replaced.
    """
    data_copy = data.copy()
    for col in data_copy.select_dtypes(include=["object"]).columns:
        data_copy[col] = data_copy[col].apply(
            lambda x: str(x).replace("\n", " ").replace("\r", " ").replace(",", ";") if isinstance(x, str) else x
        )
    return data_copy
