"""Display similar to Tab1 in the quant benchmarking modules, all of the data
next to the submitted data."""

import uuid
from typing import Callable

import streamlit as st

from proteobench.plotting.plot_quant import PlotDataPoint

from .filter import filter_data_using_slider
from .resulttable import configure_aggrid, render_aggrid, prepare_display_dataframe
from .metricplot import render_metric_plot


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
            variables_quant.metric_plot_labels,
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

    metric = display_metric_selector(variables_quant)

    if len(data_points_filtered) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return

    # prepare plot key explicitly for tab 4
    key = variables_quant.result_submitted_plot_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    highlight_point_id = render_metric_plot(
        data_points_filtered,
        metric,
        label=st.session_state[st.session_state[variables_quant.selectbox_id_submitted_uuid]],
        key=_id_of_key,
    )

    df_display = prepare_display_dataframe(
        st.session_state[variables_quant.all_datapoints_submitted], highlight_point_id
    )
    grid_options = configure_aggrid(df_display)

    # prepare df key explicitly for tab 4
    key = variables_quant.table_new_results_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    render_aggrid(df_display, grid_options, key=str(_id_of_key))

    st.title("Public submission")
    st.markdown(
        "If you want to make this point — and the associated data —"
        "publicly available, please go to the tab 'Public Submission'"
    )


########################################################################################
# helper functions


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


def display_metric_selector(variables_quant) -> str:
    key = variables_quant.metric_selector_submitted_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    return st.radio(
        "Select metric to plot",
        options=["Median", "Mean"],
        help="Toggle between median and mean absolute difference metrics.",
        key=_id_of_key,
    )
