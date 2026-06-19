import re

import pandas as pd
import streamlit as st

# functions to plot the metric plot


def render_metric_plot(
    data: pd.DataFrame,
    key,
    plot_generator,
    metric: str | None = None,
    mode: str | None = None,
    label: str = "None",
    colorblind_mode: bool = False,
    annotation: str = "",
    **extra_plot_kwargs,
) -> str | None:
    """
    Displays the metric plot and returns the ProteoBench ID of the selected point (if any).

    Parameters
    ----------
    data : pd.DataFrame
        The filtered dataset to plot.
    key : str
        Unique key for the plot in the Streamlit session state.
    plot_generator : PlotGeneratorBase
        The plot generator instance for the module.
    metric : str or None, optional
        Metric to plot ("Median", "Mean", "ROC-AUC"). None for modules that do not use this param.
    mode : str or None, optional
        Mode to plot ("Species-weighted" or "Global"). None for modules that do not use this param.
    label : str, optional
        The label for the data points.
    colorblind_mode : bool, optional
        Whether to use colorblind-safe colors.
    annotation : str, optional
        Optional annotation to display on the plot.
    **extra_plot_kwargs
        Additional keyword arguments forwarded to plot_main_metric (e.g. level,
        evaluation_type for de novo modules).

    Returns
    -------
    str or None
        ProteoBench ID of the selected data point, if any.
    """
    # Species-weighted pre-filter with user-visible warning (quant modules only).
    # Only triggered when mode is explicitly "Species-weighted" and the plot generator
    # exposes _get_metric_column_name (quant generators do, de novo generator does not).
    if mode == "Species-weighted" and hasattr(plot_generator, "_get_metric_column_name"):
        metric_lower, mode_suffix, _ = plot_generator._get_metric_column_name(metric, mode)
        metric_col_name = f"{metric_lower}_abs_epsilon_{mode_suffix}"
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

        data = filtered_data

    if len(data) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return None

    highlight_point_id = None
    try:
        # Build kwargs for plot_main_metric.  Only include metric/mode when they are
        # set so modules that don't use them are not surprised by unexpected kwargs.
        plot_kwargs = {}
        if metric is not None:
            plot_kwargs["metric"] = metric
        if mode is not None:
            plot_kwargs["mode"] = mode
        plot_kwargs.update(
            label=label,
            colorblind_mode=colorblind_mode,
            annotation=annotation,
            **extra_plot_kwargs,
        )

        fig_metric = plot_generator.plot_main_metric(data, **plot_kwargs)
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
            hover = selected_point.get("hovertext", "") or selected_point.get("text", "")
            match = re.search(r"ProteoBench ID: ([^<]+)", hover)
            if match:
                highlight_point_id = match.group(1)

    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

    return highlight_point_id
