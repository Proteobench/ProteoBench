import json
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


def prepare_df_for_display(data: pd.DataFrame) -> pd.DataFrame:
    """
    Reformat a DataFrame so it is Arrow-serialisable for ``st.dataframe``.

    Two fixes are applied:

    - Columns whose values are dicts or lists are JSON-serialised to strings.
    - Object columns that mix types (e.g. booleans and empty strings) are cast
      to ``str`` so Arrow does not try to infer a uniform type.

    Parameters
    ----------
    data : pd.DataFrame
        The data to sanitise.

    Returns
    -------
    pd.DataFrame
        Copy of ``data`` safe to pass to ``st.dataframe``.
    """
    df = data.copy()
    for col in df.columns:
        sample = df[col].dropna()
        if sample.empty:
            continue
        first = sample.iloc[0]
        if isinstance(first, (dict, list)):
            df[col] = df[col].apply(lambda v: json.dumps(v) if isinstance(v, (dict, list)) else v)
        elif df[col].dtype == object:
            unique_types = {type(v) for v in sample}
            if len(unique_types) > 1:
                df[col] = df[col].astype(str)
    return df


def clean_dataframe_for_export(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataframe for CSV export by replacing newlines in text fields and
    serialising dict/list columns to JSON strings.

    Parameters
    ----------
    data : pd.DataFrame
        The data to clean.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe safe for CSV export and Streamlit caching.
    """
    data_copy = data.copy()
    for col in data_copy.columns:
        sample = data_copy[col].dropna()
        if sample.empty:
            continue
        first = sample.iloc[0]
        if isinstance(first, (dict, list)):
            data_copy[col] = data_copy[col].apply(lambda v: json.dumps(v) if isinstance(v, (dict, list)) else v)
        elif data_copy[col].dtype == object:
            data_copy[col] = data_copy[col].apply(
                lambda x: str(x).replace("\n", " ").replace("\r", " ").replace(",", ";") if isinstance(x, str) else x
            )
    return data_copy
