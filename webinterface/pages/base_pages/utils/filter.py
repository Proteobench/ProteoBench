from typing import Callable

import pandas as pd
import streamlit as st


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
