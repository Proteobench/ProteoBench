"""Display similar to Tab1 in the quant benchmarking modules, all of the data
next to the sumbitted data."""

import uuid
from typing import Callable

import pandas as pd
import streamlit as st

from proteobench.plotting.plot_quant import PlotDataPoint

from .filter import filter_data_using_slider


def initialize_submitted_slider(slider_id_submitted_uuid, default_val_slider) -> None:
    """
    Initialize the slider for the submitted data.
    """
    id_key_in_state = slider_id_submitted_uuid
    if id_key_in_state not in st.session_state.keys():
        st.session_state[id_key_in_state] = uuid.uuid4()
    if st.session_state[id_key_in_state] not in st.session_state.keys():
        value_key_in_state = st.session_state[id_key_in_state]  # the uuid4 as key
        st.session_state[value_key_in_state] = default_val_slider


def generate_submitted_slider(variables_quant) -> None:
    """
    Create a slider input.
    """
    if variables_quant.slider_id_submitted_uuid not in st.session_state:
        st.session_state[variables_quant.slider_id_submitted_uuid] = uuid.uuid4()
    slider_key = st.session_state[variables_quant.slider_id_submitted_uuid]

    st.markdown(open(variables_quant.description_slider_md, "r", encoding="utf-8").read())

    st.select_slider(
        label="Minimal precursor quantifications (# samples)",
        options=[1, 2, 3, 4, 5, 6],
        value=st.session_state.get(slider_key, variables_quant.default_val_slider),
        key=slider_key,
    )


def generate_submitted_selectbox(variables_quant) -> None:
    """
    Create the selectbox for the Streamlit UI.
    """
    if variables_quant.selectbox_id_submitted_uuid not in st.session_state.keys():
        st.session_state[variables_quant.selectbox_id_submitted_uuid] = uuid.uuid4()

    try:
        st.selectbox(
            "Select label to plot",
            ["None", "precursor_mass_tolerance", "fragment_mass_tolerance"],
            key=st.session_state[variables_quant.selectbox_id_submitted_uuid],
        )
    except Exception as e:
        st.error(f"Unable to create the selectbox: {e}", icon="🚨")


def display_submitted_results(variables_quant, ionmodule) -> None:
    """
    Display the results section of the page for submitted data.
    """
    # handled_submission = self.process_submission_form()
    # if handled_submission == False:
    #    return
    key_all_datapoints_submitted = variables_quant.all_datapoints_submitted
    initialize_submitted_data_points(key_all_datapoints_submitted, ionmodule.obtain_all_data_points)
    data_points_filtered = filter_data_using_slider(
        slider_id_uuid=variables_quant.slider_id_submitted_uuid,
        all_datapoints=key_all_datapoints_submitted,
        filter_data_point=ionmodule.filter_data_point,
    )

    metric = st.radio(
        "Select metric to plot",
        options=["Median", "Mean"],
        help="Toggle between median and mean absolute difference metrics.",
        key="placeholder2",  # TODO: add to variables
    )

    if len(data_points_filtered) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return

    try:
        fig_metric = PlotDataPoint.plot_metric(
            data_points_filtered,
            metric=metric,
            label=st.session_state[st.session_state[variables_quant.selectbox_id_submitted_uuid]],
        )

        try:
            st.plotly_chart(fig_metric, use_container_width=True)
        except Exception:
            st.error("No (new) datapoints available for plotting", icon="🚨")
            return
    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

    st.session_state[variables_quant.table_id_uuid] = uuid.uuid4()
    st.data_editor(
        st.session_state[variables_quant.all_datapoints_submitted],
        key=st.session_state[variables_quant.table_id_uuid],
        on_change=handle_submitted_table_edits,
        args=(variables_quant,),
    )

    st.title("Public submission")
    st.markdown(
        "If you want to make this point — and the associated data —"
        "publicly available, please go to “Public Submission"
    )


def initialize_submitted_data_points(
    all_datapoints_submitted: str,
    obtain_all_data_points: Callable,
) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    key_in_state = all_datapoints_submitted
    if key_in_state not in st.session_state.keys():
        st.session_state[key_in_state] = None
        # ? So all_datapoints argument is always None?
        st.session_state[key_in_state] = obtain_all_data_points(
            all_datapoints=st.session_state[key_in_state],
        )


def filter_data_submitted_slider(self) -> pd.DataFrame:
    """
    Filter the data points based on the slider value.

    Returns
    -------
    pd.DataFrame
        The filtered data points.
    """
    if (
        self.variables_quant.slider_id_submitted_uuid in st.session_state.keys()
        and self.variables_quant.all_datapoints_submitted in st.session_state.keys()
    ):
        return self.ionmodule.filter_data_point(
            st.session_state[self.variables_quant.all_datapoints_submitted],
            st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]],
        )


def handle_submitted_table_edits(variables_quant) -> None:
    """Callback function for handling edits made to the data table in the UI."""
    edits = st.session_state[st.session_state[variables_quant.table_id_uuid]]["edited_rows"].items()
    for k, v in edits:
        try:
            # ToDo: check if this can be done more clearly
            # ? gets row k from the all_datapoints_submitted DataFrame
            # ? and ... modifies the first column specified in the keys of dictionary v
            # df = st.session_state[variables_quant.all_datapoints_submitted]
            # df[list(v.keys())[0]].iloc[k] = list(v.values())[0]
            st.session_state[variables_quant.all_datapoints_submitted][list(v.keys())[0]].iloc[k] = list(v.values())[0]
        except TypeError:
            return
    st.session_state[variables_quant.highlight_list_submitted] = list(
        st.session_state[variables_quant.all_datapoints_submitted]["Highlight"]
    )
    st.session_state[variables_quant.placeholder_table] = st.session_state[variables_quant.all_datapoints_submitted]

    if len(st.session_state[variables_quant.all_datapoints]) == 0:
        st.error("No datapoints available for plotting", icon="🚨")

    try:
        fig_metric = PlotDataPoint.plot_metric(
            st.session_state[variables_quant.all_datapoints],
            label=st.session_state[st.session_state[variables_quant.selectbox_id_uuid]],
        )
    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

    st.session_state[variables_quant.fig_metric] = fig_metric
