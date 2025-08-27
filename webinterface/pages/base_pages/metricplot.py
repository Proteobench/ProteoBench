import streamlit as st
import pandas as pd
from proteobench.plotting.plot_quant import PlotDataPoint
import re

# functions to plot the metric plot


def render_metric_plot(data: pd.DataFrame, metric: str, label: str, key) -> str | None:
    """
    Displays the metric plot and returns the ProteoBench ID of the selected point (if any).

    Parameters
    ----------
    data : pd.DataFrame
        The filtered dataset to plot.


    metric : str
        Metric to plot ("Median" or "Mean").

    label : str
        The label for the data points.

    key : str
        Unique key for the plot in the Streamlit session state.

    Returns
    -------
    str or None
        ProteoBench ID of the selected data point, if any.
    """

    if len(data) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return None

    highlight_point_id = None
    try:
        fig_metric = PlotDataPoint.plot_metric(
            data,
            label=label,
            metric=metric,
        )
        event_dict = st.plotly_chart(
            fig_metric,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key=key,
        )
        selected_point = (
            event_dict["selection"]["points"][0]
            if "selection" in event_dict and "points" in event_dict["selection"] and event_dict["selection"]["points"]
            else None
        )
        if selected_point:
            hover = selected_point.get("hovertext", "")
            match = re.search(r"ProteoBench ID: ([^\s<]+)", hover)
            if match:
                highlight_point_id = match.group(1)

    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

    return highlight_point_id
