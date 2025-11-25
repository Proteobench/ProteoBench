"""Display similar to Tab1 in the quant benchmarking modules, all of the data
next to the submitted data."""

import uuid
from typing import Callable

import streamlit as st

from .filter import filter_data_using_slider
from .metricplot import render_metric_plot
from .resulttable import configure_aggrid, prepare_display_dataframe, render_aggrid


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


def generate_submitted_slider(variables, max_nr_observed: int = None) -> None:
    """
    Create a slider input.
    
    Parameters
    ----------
    variables : object
        Variables object containing slider configuration.
    max_nr_observed : int, optional
        Maximum nr_observed value for the slider. If None, defaults to 6.
    """
    if variables.slider_id_submitted_uuid not in st.session_state:
        st.session_state[variables.slider_id_submitted_uuid] = uuid.uuid4()
    slider_key = st.session_state[variables.slider_id_submitted_uuid]

    st.markdown(open(variables.description_slider_md, "r", encoding="utf-8").read())

    # Use provided max_nr_observed or default to 6
    if max_nr_observed is None:
        max_nr_observed = 6
    
    # Generate slider options from 1 to max_nr_observed
    slider_options = list(range(1, int(max_nr_observed) + 1))

    st.select_slider(
        label="Minimal precursor quantifications (# samples)",
        options=slider_options,
        value=st.session_state.get(slider_key, variables.default_val_slider),
        key=slider_key,
    )


def generate_submitted_selectbox(variables) -> None:
    """
    Create the selectbox for the Streamlit UI.
    """
    if variables.selectbox_id_submitted_uuid not in st.session_state.keys():
        st.session_state[variables.selectbox_id_submitted_uuid] = uuid.uuid4()

    try:
        st.selectbox(
            "Select label to plot",
            variables.metric_plot_labels,
            key=st.session_state[variables.selectbox_id_submitted_uuid],
        )
    except Exception as e:
        st.error(f"Unable to create the selectbox: {e}", icon="🚨")


def display_submitted_results(variables, ionmodule) -> None:
    """
    Display the results section of the page for submitted data.
    """
    # handled_submission = self.process_submission_form()
    # if handled_submission == False:
    #    return
    key_all_datapoints_submitted = variables.all_datapoints_submitted
    initialize_submitted_data_points(key_all_datapoints_submitted, ionmodule.obtain_all_data_points)
    data_points_filtered = filter_data_using_slider(
        slider_id_uuid=variables.slider_id_submitted_uuid,
        all_datapoints=key_all_datapoints_submitted,
        filter_data_point=ionmodule.filter_data_point,
    )

    metric = display_metric_selector(variables)
    mode = display_metric_calc_approach_selector(variables)

    if len(data_points_filtered) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return

    # prepare plot key explicitly for tab 4
    key = variables.result_submitted_plot_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    plot_generator = ionmodule.get_plot_generator()
    highlight_point_id = render_metric_plot(
        data_points_filtered,
        metric,
        mode,
        label=st.session_state[st.session_state[variables.selectbox_id_submitted_uuid]],
        key=_id_of_key,
        plot_generator=plot_generator,
        slider_id_uuid=variables.slider_id_submitted_uuid,
    )

    df_display = prepare_display_dataframe(st.session_state[variables.all_datapoints_submitted], highlight_point_id)
    grid_options = configure_aggrid(df_display)

    # prepare df key explicitly for tab 4
    key = variables.table_new_results_uuid
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


def display_metric_selector(variables) -> str:
    key = variables.metric_selector_submitted_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    return st.radio(
        "Select metric to plot",
        options=["Median", "Mean"],
        help="Toggle between median and mean absolute difference metrics.",
        key=_id_of_key,
    )


def display_metric_calc_approach_selector(variables) -> str:
    key = variables.metric_calc_approach_selector_submitted_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    return st.radio(
        "Select metric calculation approach",
        options=["Equal weighted species", "Global"],
        help="Toggle between equal weighted species-specific and global absolute difference metrics.",
        key=_id_of_key,
    )
