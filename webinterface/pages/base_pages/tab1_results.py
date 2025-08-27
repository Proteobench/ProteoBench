import os
import uuid
from typing import Callable

import streamlit as st
import pandas as pd

from .resulttable import configure_aggrid, render_aggrid, prepare_display_dataframe
from .metricplot import render_metric_plot


from .filter import filter_data_using_slider


def initialize_main_slider(slider_id_uuid: str, default_val_slider: float) -> None:
    """
    Initialize the slider for the main data.

    We use a slider uuid and associate a defalut value with it.
    - self.variables_quant.slider_id_uuid
    - self.variables_quant.default_val_slider
    """
    key = slider_id_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]
    if _id_of_key not in st.session_state.keys():
        st.session_state[_id_of_key] = default_val_slider


def generate_main_slider(slider_id_uuid: str, description_slider_md: str, default_val_slider: float) -> None:
    """
    Create a slider input.
    """
    # key for slider_uuid in session state
    if slider_id_uuid not in st.session_state:
        st.session_state[slider_id_uuid] = uuid.uuid4()
    slider_key = st.session_state[slider_id_uuid]

    fpath = description_slider_md
    st.markdown(open(fpath, "r").read())

    default_value = st.session_state.get(slider_key, default_val_slider)
    st.select_slider(
        label="Minimal precursor quantifications (# samples)",
        options=[1, 2, 3, 4, 5, 6],
        value=default_value,
        key=slider_key,
    )


def generate_main_selectbox(variables_quant, selectbox_id_uuid) -> None:
    """
    Create the selectbox for the Streamlit UI.
    """
    if selectbox_id_uuid not in st.session_state.keys():
        st.session_state[selectbox_id_uuid] = uuid.uuid4()

    try:
        # TODO: Other labels based on different modules, e.g. mass tolerances are less relevant for DIA
        st.selectbox(
            "Select label to plot",
            variables_quant.metric_plot_labels,
            key=st.session_state[selectbox_id_uuid],
        )
    except Exception as e:
        st.error(f"Unable to create the selectbox: {e}", icon="🚨")


def display_download_section(variables_quant, reset_uuid=False) -> None:
    """
    Render the selector and area for raw data download.

    Parameters
    ----------
    reset_uuid : bool, optional
        Whether to reset the UUID, by default False.
    """
    if len(st.session_state[variables_quant.all_datapoints]) == 0:
        st.error("No data available for download.", icon="🚨")
        return

    downloads_df = st.session_state[variables_quant.all_datapoints][["id", "intermediate_hash"]]
    downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

    if variables_quant.placeholder_downloads_container not in st.session_state.keys() or reset_uuid:
        st.session_state[variables_quant.placeholder_downloads_container] = st.empty()
        st.session_state[variables_quant.download_selector_id_uuid] = uuid.uuid4()

    # with st.session_state[variables_quant.placeholder_downloads_container].container(border=True):
    st.subheader("Download raw datasets")

    # Sort the intermediate_hash values and get the corresponding ids
    sorted_indices = sorted(range(len(downloads_df["id"])), key=lambda i: downloads_df["id"].iloc[i])
    sorted_intermediate_hash = [downloads_df["intermediate_hash"].iloc[i] for i in sorted_indices]
    sorted_ids = [downloads_df["id"].iloc[i] for i in sorted_indices]

    st.selectbox(
        "Select dataset",
        sorted_intermediate_hash,
        index=None,
        key=st.session_state[variables_quant.download_selector_id_uuid],
        format_func=lambda x: sorted_ids[sorted_intermediate_hash.index(x)],
    )

    if (
        st.session_state[st.session_state[variables_quant.download_selector_id_uuid]] is not None
        and st.secrets["storage"]["dir"] is not None
    ):
        dataset_path = (
            st.secrets["storage"]["dir"]
            + "/"
            + st.session_state[st.session_state[variables_quant.download_selector_id_uuid]]
        )
        if os.path.isdir(dataset_path):
            files = os.listdir(dataset_path)
            for file_name in files:
                path_to_file = dataset_path + "/" + file_name
                with open(path_to_file, "rb") as file:
                    st.download_button(file_name, file, file_name=file_name)
        else:
            st.write(
                "Directory for this dataset does not exist, this should not happen"
                " on the server, but is expected in the local development environment."
            )


def display_existing_results(variables_quant, ionmodule) -> None:
    """
    Orchestrates the full display of quantification results in Streamlit,
    including plotting and interactive tabular output with styling.

    Parameters
    ----------
    variables_quant : object
        Object containing quantification variables including data points,
        slider/selectbox UUIDs, and configuration flags.

    ionmodule : object
        Module responsible for filtering and transforming ion data.
    """
    initialize_and_filter_data(variables_quant, ionmodule)
    data_points_filtered = variables_quant.filtered_data

    metric = display_metric_selector(variables_quant)

    # prepare plot key explicitly for tab 1
    key = variables_quant.result_plot_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    highlight_point_id = render_metric_plot(
        data_points_filtered,
        metric,
        label=st.session_state[st.session_state[variables_quant.selectbox_id_uuid]],
        key=_id_of_key,
    )

    df_display = prepare_display_dataframe(data_points_filtered, highlight_point_id)
    grid_options = configure_aggrid(df_display)

    # prepare df key explicitly for tab 1
    key = variables_quant.table_id_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    render_aggrid(df_display, grid_options, key=_id_of_key)
    offer_download(df_display)
    display_download_section(variables_quant=variables_quant)


# === Modular Functions ===


def initialize_and_filter_data(variables_quant, ionmodule):
    initialize_main_data_points(
        all_datapoints=variables_quant.all_datapoints,
        obtain_all_data_points=ionmodule.obtain_all_data_points,
    )
    variables_quant.filtered_data = filter_data_using_slider(
        slider_id_uuid=variables_quant.slider_id_uuid,
        all_datapoints=variables_quant.all_datapoints,
        filter_data_point=ionmodule.filter_data_point,
    )


def display_metric_selector(variables_quant) -> str:
    key = variables_quant.metric_selector_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    return st.radio(
        "Select metric to plot",
        options=["Median", "Mean"],
        help="Toggle between median and mean absolute difference metrics.",
        key=_id_of_key,
    )


def offer_download(df: pd.DataFrame, filename: str = "quantification_results.csv") -> None:
    """
    Adds a download button to export the displayed DataFrame as a CSV file.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to be downloaded.

    filename : str, optional
        The name of the file to download, by default "quantification_results.csv".
    """
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Download table as CSV", data=csv_data, file_name=filename, mime="text/csv")


def initialize_main_data_points(all_datapoints: str, obtain_all_data_points: Callable) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if all_datapoints not in st.session_state.keys():
        st.session_state[all_datapoints] = None
        st.session_state[all_datapoints] = obtain_all_data_points(all_datapoints=st.session_state[all_datapoints])
