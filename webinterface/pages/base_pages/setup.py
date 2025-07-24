"""Build DataFrames for all data points and previously submitted data points."""

from typing import Callable

import streamlit as st


def initialize_main_data_points(all_datapoints: str, obtain_all_data_points: Callable) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if all_datapoints not in st.session_state.keys():
        st.session_state[all_datapoints] = None
        st.session_state[all_datapoints] = obtain_all_data_points(all_datapoints=st.session_state[all_datapoints])
