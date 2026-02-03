import streamlit as st
import _uuid
from proteobench.plotting.plot_denovo import PlotDataPoint
import uuid

def display_submitted_results(variables, ionmodule) -> None:
    """
    Display the results section of the page for submitted data.
    """
    _initialize_submitted_data_points(
        all_datapoints_submitted=variables.all_datapoints_submitted,
        obtain_all_data_points=ionmodule.obtain_all_data_points
    )

    try:
        fig_metric = PlotDataPoint.plot_metric(
            benchmark_metrics_df=st.session_state[variables.all_datapoints_submitted],
            label=st.session_state[st.session_state[variables.selectbox_id_submitted_uuid]],
        )
        st.plotly_chart(
            fig_metric,
            use_container_width=True,
            key=variables.fig_metric_submitted
        )
    except Exception as e:
        st.error(f"Umable to plot the datapoints: {e}", icon="🚨")

    

def _initialize_submitted_data_points(all_datapoints_submitted, obtain_all_data_points) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if all_datapoints_submitted not in st.session_state.keys():
        st.session_state[all_datapoints_submitted] = None
        st.session_state[all_datapoints_submitted] = obtain_all_data_points(
            all_datapoints=st.session_state[all_datapoints_submitted]
        )
