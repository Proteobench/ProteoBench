import re

import pandas as pd
import streamlit as st

# functions to plot the metric plot


def render_metric_plot(
    data: pd.DataFrame, metric: str, mode: str, label: str, colorblind_mode: bool, key, plot_generator
) -> str | None:
    """
    Displays the metric plot and returns the ProteoBench ID of the selected point (if any).

    Parameters
    ----------
    data : pd.DataFrame
        The filtered dataset to plot.

    metric : str
        Metric to plot ("Median" or "Mean").

    mode : str
        Mode to plot ("Species-weighted" or "Global").

    label : str
        The label for the data points.

    key : str
        Unique key for the plot in the Streamlit session state.

    plot_generator : PlotGeneratorBase
        The plot generator instance for the module.

    Returns
    -------
    str or None
        ProteoBench ID of the selected data point, if any.
    """

    highlight_point_id = None

    # Check if user selected "Species-weighted" mode but no datapoints have these metrics
    if mode == "Species-weighted":

        metric_lower, mode_suffix, _ = plot_generator._get_metric_column_name(metric, mode)
        metric_col_name = f"{metric_lower}_abs_epsilon_{mode_suffix}"

        # Check how many datapoints have the equal-weighted metric
        original_count = len(data)
        filtered_data = plot_generator._filter_datapoints_with_metric(data, metric_col_name)

        if len(filtered_data) == 0:
            st.warning(
                "No submitted datapoints have species-weighted metrics yet. "
                "This metric calculation approach is only available for newly submitted results. "
                "Please use the 'Global' mode to view existing results.",
                icon="⚠️",
            )
            st.info(
                "New datapoints submitted after the species-weighted feature was implemented "
                "will automatically have these metrics calculated and will appear here. We are currently working towards resubmitting existing datapoints with these metrics as well.",
            )
            return None

        # Update data to use filtered datapoints
        data = filtered_data

    if len(data) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return None

    try:
        fig_metric = plot_generator.plot_main_metric(
            data,
            metric=metric,
            mode=mode,
            label=label,
            colorblind_mode=colorblind_mode,
        )
        event_dict = st.plotly_chart(
            fig_metric,
            width="stretch",
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
            match = re.search(r"ProteoBench ID: ([^<]+)", hover)
            if match:
                highlight_point_id = match.group(1)

    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

    return highlight_point_id
