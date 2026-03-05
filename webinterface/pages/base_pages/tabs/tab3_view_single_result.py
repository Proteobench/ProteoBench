"""
Generic Tab 3: In-Depth Plots

This module provides a unified interface for displaying in-depth analysis plots
across all ProteoBench module types (Quant, De Novo, etc.).
"""

import glob
import os
import uuid
import zipfile
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
import streamlit_utils
from plotly import graph_objects as go


def generate_indepth_plots(
    module,
    variables,
    parsesettingsbuilder,
    user_input,
    public_id: Optional[str],
    public_hash: Optional[str],
    metric: str = "Median",
    mode: str = "Global",
    colorblind_mode: bool = False,
) -> Optional[go.Figure]:
    """
    Generate and display in-depth plots for the selected dataset.

    Works generically across all module types by using the plot_generator interface.

    Parameters
    ----------
    module : object
        The module instance (Quant, De Novo, etc.).
    variables : object
        Variables object containing session state keys.
    parsesettingsbuilder : ParseSettingsBuilder
        Parse settings builder for the module.
    user_input : dict
        User input parameters.
    public_id : Optional[str]
        The dataset identifier ("Uploaded dataset" or public run name).
    public_hash : Optional[str]
        The hash of the selected public dataset.
    metric : str, optional
        The metric to use for plotting (e.g., "Median", "Mean"). Defaults to "Median".
    mode : str, optional
        The mode for metric calculation (e.g., "Global", "Species-specific"). Defaults to "Global".
    colorblind_mode : bool, optional
        Whether to use colorblind-friendly colors. Defaults to False.

    Returns
    -------
    Optional[go.Figure]
        The first generated plot or None if generation fails.
    """
    plot_generator = module.get_plot_generator()

    # Validate that we have data to plot
    if variables.result_perf not in st.session_state:
        if public_hash is None:
            st.error(":x: Please submit a result file or select a public run for display", icon="🚨")
            return None
        elif public_id == "Uploaded dataset":
            st.error(":x: Please submit a result file in the Submit New Data Tab", icon="🚨")
            return None

    # Load performance data
    if public_id == "Uploaded dataset":
        performance_data = st.session_state[variables.result_perf]
    else:
        performance_data = load_public_performance_data(public_hash)
        if performance_data is None:
            return None

    # Generate parse settings
    parse_settings = parsesettingsbuilder.build_parser(user_input["input_format"])

    # Generate plots using module's plot generator
    try:
        plots = plot_generator.generate_in_depth_plots(
            performance_data,
            parse_settings,
            metric=metric,
            mode=mode,
            colorblind_mode=colorblind_mode,
        )
    except Exception as e:
        st.error(f"Error generating in-depth plots: {e}", icon="🚨")
        import traceback

        with st.expander("Error details"):
            st.code(traceback.format_exc())
        return None

    # Store plots in session state
    for plot_name, fig in plots.items():
        st.session_state[f"{variables.fig_prefix}_{plot_name}"] = fig

    # Display plots using module's layout configuration
    display_plots_with_layout(plots, plot_generator, variables, public_id)

    # Display performance data table
    display_performance_table(performance_data, variables, user_input, public_id)

    return plots.get(next(iter(plots))) if plots else None


def load_public_performance_data(public_hash: str) -> Optional[pd.DataFrame]:
    """
    Load performance data for a public dataset from storage.

    Parameters
    ----------
    public_hash : str
        The hash identifier of the public dataset.

    Returns
    -------
    Optional[pd.DataFrame]
        The loaded performance data or None if loading fails.
    """
    if "storage" not in st.secrets or st.secrets["storage"]["dir"] is None:
        st.error(":x: Storage directory not configured", icon="🚨")
        return None

    dataset_path = os.path.join(st.secrets["storage"]["dir"], public_hash)
    pattern = os.path.join(dataset_path, "*_data.zip")
    zip_files = glob.glob(pattern)

    if not zip_files:
        st.error(":x: Could not find the files on the server", icon="🚨")
        return None

    zip_path = zip_files[0]

    try:
        with zipfile.ZipFile(zip_path) as z:
            with z.open("result_performance.csv") as f:
                return pd.read_csv(f)
    except Exception as e:
        st.error(f":x: Error loading performance data: {e}", icon="🚨")
        return None


def display_plots_with_layout(plots: dict, plot_generator, variables, public_id: str) -> None:
    """
    Display plots using the module's layout configuration.

    Parameters
    ----------
    plots : dict
        Dictionary of plot names to plotly figures.
    plot_generator : PlotGeneratorBase
        The plot generator instance.
    variables : object
        Variables object.
    public_id : str
        The dataset identifier for display in titles.
    """
    layout_config = plot_generator.get_in_depth_plot_layout()
    descriptions = plot_generator.get_in_depth_plot_descriptions()

    for section in layout_config:
        # Handle section title if provided
        if "title" in section and section["title"]:
            st.markdown(f"## {section['title']}")

        # Create columns based on section configuration
        cols = st.columns(section["columns"])

        # Display plots in columns
        for i, plot_name in enumerate(section["plots"]):
            if plot_name not in plots:
                continue

            col = cols[i % section["columns"]]

            with col:
                # Add plot title if available in titles dict
                if "titles" in section and plot_name in section["titles"]:
                    st.subheader(section["titles"][plot_name])
                elif plot_name in descriptions:
                    # Use first line of description as title
                    title = descriptions[plot_name].split(".")[0]
                    st.subheader(title)

                # Add description
                if plot_name in descriptions:
                    desc = descriptions[plot_name]
                    st.markdown(f"{desc}")
                    if public_id:
                        st.caption(f"Data source: {public_id}")

                # Display plot
                st.plotly_chart(plots[plot_name], use_container_width=True)

        # Add separator after each section (except last)
        if section != layout_config[-1] and len(section["plots"]) > 0:
            st.markdown("---")


def display_performance_table(performance_data: pd.DataFrame, variables, user_input: dict, public_id: str) -> None:
    """
    Display the performance data table with download option.

    Parameters
    ----------
    performance_data : pd.DataFrame
        The performance data to display.
    variables : object
        Variables object.
    user_input : dict
        User input parameters.
    public_id : str
        The dataset identifier.
    """
    st.subheader(f"Sample of the processed file for {public_id}")

    # Display description if available
    if hasattr(variables, "description_table_md") and os.path.exists(variables.description_table_md):
        st.markdown(open(variables.description_table_md, "r", encoding="utf-8").read())

    # Display table
    st.dataframe(performance_data.head(100))

    # Generate sample name
    if public_id == "Uploaded dataset":
        sample_name = generate_sample_name(user_input.get("input_format", "unknown"))
    else:
        sample_name = public_id

    # Download button
    random_uuid = uuid.uuid4()
    st.download_button(
        label="Download table",
        data=streamlit_utils.save_dataframe(performance_data),
        file_name=f"{sample_name}.csv",
        mime="text/csv",
        key=f"{random_uuid}",
        icon=":material/download:",
    )


def generate_sample_name(input_format: str) -> str:
    """
    Generate a unique sample name based on input format and timestamp.

    Parameters
    ----------
    input_format : str
        The input format/software name.

    Returns
    -------
    str
        The generated sample name.
    """
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{input_format}_{time_stamp}"


def display_in_depth_plots_generic(variables, ionmodule, performance_data: pd.DataFrame, **kwargs) -> None:
    """
    Generic function to display in-depth plots for any module type.

    This is a simpler alternative to generate_indepth_plots when you already
    have the performance data loaded.

    Parameters
    ----------
    variables : object
        Variables object.
    ionmodule : object
        The module instance.
    performance_data : pd.DataFrame
        The performance data to visualize.
    **kwargs : dict
        Additional module-specific parameters to pass to generate_in_depth_plots.
    """
    if performance_data is None or len(performance_data) == 0:
        st.warning("No data available for in-depth analysis.", icon="⚠️")
        return

    # Get plot generator from module
    plot_generator = ionmodule.get_plot_generator()

    # Generate plots
    try:
        plots = plot_generator.generate_in_depth_plots(performance_data=performance_data, **kwargs)
    except Exception as e:
        st.error(f"Error generating in-depth plots: {e}", icon="🚨")
        import traceback

        with st.expander("Error details"):
            st.code(traceback.format_exc())
        return

    # Display plots with layout
    display_plots_with_layout(plots, plot_generator, variables, "Current Dataset")
