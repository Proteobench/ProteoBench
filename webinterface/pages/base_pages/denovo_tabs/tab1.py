import os
import uuid
from typing import Callable
from proteobench.plotting.plot_denovo import PlotDataPoint

import pandas as pd
import streamlit as st

    
def initialize_radio(radio_id_uuid: str, default_value: str):
    key = radio_id_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    
    _id_of_key = st.session_state[key]
    if _id_of_key not in st.session_state.keys():
        st.session_state[_id_of_key] = default_value


def generate_main_radio(
        radio_id_uuid: str,
        description: str,
        options: list,
        help: str,
    ):
    """Wraps radio generation"""

    st.radio(
        description,
        options=options,
        horizontal=True,
        key=st.session_state[radio_id_uuid],
        help=help
    )

# Same as in quant_tabs
def generate_main_selectbox(variables, selectbox_id_uuid) -> None:
    """
    Create the selectbox for the Streamlit UI.
    """
    if selectbox_id_uuid not in st.session_state.keys():
        st.session_state[selectbox_id_uuid] = uuid.uuid4()

    try:
        # TODO: Other labels based on different modules, e.g. mass tolerances are less relevant for DIA
        st.selectbox(
            "Select label to plot",
            variables.metric_plot_labels,
            key=st.session_state[selectbox_id_uuid],
        )
    except Exception as e:
        st.error(f"Unable to create the selectbox: {e}", icon="🚨")


def display_existing_results(
        variables,
        ionmodule,
        level_mapping,
        evaluation_type_mapping
    ):
    """
    Display the results section of the page for existing data.
    """
    _initialize_main_data_points(variables, ionmodule)

    try:
        fig_metric = PlotDataPoint.plot_metric(
            benchmark_metrics_df=st.session_state[variables.all_datapoints],
            label=st.session_state[st.session_state[variables.selectbox_id_uuid]],
            level=level_mapping[
                st.session_state[st.session_state[variables.radio_level_id_uuid]]
            ],
            evaluation_type=evaluation_type_mapping[
                st.session_state[st.session_state[variables.radio_evaluation_id_uuid]]
            ]
        )
        st.plotly_chart(
            fig_metric,
            use_container_width=True,
            key=variables.fig_metric
        )
    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
    
    st.dataframe(st.session_state[variables.all_datapoints])
    _display_download_section(variables, reset_uuid=False)


def _initialize_main_data_points(variables, ionmodule: Callable):
    """
    Initialize the all_datapoionts variable in the session state.
    """
    if variables.all_datapoints not in st.session_state.keys():
        st.session_state[variables.all_datapoints] = None
        st.session_state[variables.all_datapoints] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables.all_datapoints]
        )

def _display_download_section(variables, reset_uuid=False) -> None:
    """
    Render the selector and area for raw data download.

    Parameters
    ----------
    reset_uuid : bool, optional
        Whether to reset the UUID, by default False.
    """
    # TODO: What to put in secrets.toml to make this work?
    if len(st.session_state[variables.all_datapoints]) == 0:
        st.error("No data available for download.", icon="🚨")
        return

    downloads_df = st.session_state[variables.all_datapoints][["id", "intermediate_hash"]]
    downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

    if variables.placeholder_downloads_container not in st.session_state.keys() or reset_uuid:
        st.session_state[variables.placeholder_downloads_container] = st.empty()
        st.session_state[variables.download_selector_id_uuid] = uuid.uuid4()

    with st.session_state[variables.placeholder_downloads_container].container(border=True):
        st.subheader("Download raw datasets")

        st.selectbox(
            "Select dataset",
            downloads_df["intermediate_hash"],
            index=None,
            key=st.session_state[variables.download_selector_id_uuid],
            format_func=lambda x: downloads_df["id"][x],
        )

        if (
            st.session_state[st.session_state[variables.download_selector_id_uuid]] != None
            and st.secrets["storage"]["dir"] != None
        ):
            dataset_path = (
                st.secrets["storage"]["dir"]
                + "/"
                + st.session_state[st.session_state[variables.download_selector_id_uuid]]
            )
            if os.path.isdir(dataset_path):
                files = os.listdir(dataset_path)
                for file_name in files:
                    path_to_file = dataset_path + "/" + file_name
                    with open(path_to_file, "rb") as file:
                        st.download_button(file_name, file, file_name=file_name)
            else:
                st.write("Directory for this dataset does not exist, this should not happen.")
