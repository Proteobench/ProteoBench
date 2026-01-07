"""Tab 3 (2.5): In-depth plots for current data in the Quant module."""

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


# TODO: make more generic. This is currently specific to LFQ DIA ion quant (original) only.
def generate_indepth_plots(
    module,
    variables,
    parsesettingsbuilder,
    user_input,
    public_id: Optional[str],
    public_hash: Optional[str],
) -> go.Figure:
    """
    Generate and return plots based on the current benchmark data in Tab 2.5.

    Parameters
    ----------
    public_id : Optional[str], optional
        The dataset to plot, either "Uploaded dataset" or name of public run.
    public_hash : Optional[str], optional
        The hash of the selected public dataset. If None, the uploaded dataset is displayed.

    Returns
    -------
    go.Figure
        The generated plots for the selected dataset.
    """

    plot_generator = module.get_plot_generator()

    # no uploaded dataset and no public dataset selected? nothing to plot!
    if variables.result_perf not in st.session_state.keys():
        if public_hash is None:
            st.error(":x: Please submit a result file or select a public run for display", icon="🚨")
            return False
        elif public_id == "Uploaded dataset":
            st.error(":x: Please submit a result file in the Submit New Data Tab", icon="🚨")
            return False

    if public_id == "Uploaded dataset":
        performance_data = st.session_state[variables.result_perf]
    else:
        # Downloading the public performance data
        performance_data = None
        if st.secrets["storage"]["dir"] is not None:
            dataset_path = os.path.join(st.secrets["storage"]["dir"], public_hash)
            # Define the path and the pattern
            pattern = os.path.join(dataset_path, "*_data.zip")

            # Use glob to find files matching the pattern
            zip_files = glob.glob(pattern)

            # Check that at least one match was found
            if not zip_files:
                st.error(":x: Could not find the files on the server", icon="🚨")
                return

            # (Optional) handle multiple matches if necessary
            zip_path = zip_files[0]  # Assumes first match is the desired one

            # Open the ZIP file and extract the desired CSV
            with zipfile.ZipFile(zip_path) as z:
                with z.open("result_performance.csv") as f:
                    performance_data = pd.read_csv(f)

    parse_settings = parsesettingsbuilder.build_parser(user_input["input_format"])
    plots = plot_generator.generate_in_depth_plots(
        performance_data,
        parse_settings,
    )

    for plot_name, fig in plots.items():
        st.session_state[f"{variables.fig_prefix}_{plot_name}"] = fig

    if variables.first_new_plot:
        layout_config = plot_generator.get_in_depth_plot_layout()
        descriptions = plot_generator.get_in_depth_plot_descriptions()

        for section in layout_config:
            cols = st.columns(section["columns"])

            for i, plot_name in enumerate(section["plots"]):
                col = cols[i % section["columns"]]

                with col:
                    st.subheader(section["titles"][plot_name])
                    st.markdown(f"{descriptions[plot_name]} calculated from {public_id}")
                    st.plotly_chart(plots[plot_name], use_container_width=True)

            if len(section["plots"]) > 0:
                st.markdown("---")
    else:
        pass

    st.subheader("Sample of the processed file for {}".format(public_id))
    st.markdown(open(variables.description_table_md, "r", encoding="utf-8").read())
    st.session_state[variables.df_head] = st.dataframe(performance_data.head(100))

    st.subheader("Download table")
    random_uuid = uuid.uuid4()
    if public_id == "Uploaded dataset":
        # user uploaded data does not have sample name yet
        sample_name = generate_sample_name(user_input=user_input["input_format"])
    else:
        # use public run name as sample name
        sample_name = public_id
    st.download_button(
        label="Download",
        data=streamlit_utils.save_dataframe(performance_data),
        file_name=f"{sample_name}.csv",
        mime="text/csv",
        key=f"{random_uuid}",
    )

    return plots.get("logfc") or next(iter(plots.values()))


def generate_sample_name(user_input: str) -> str:
    """
    Generate a unique sample name based on the input format,
    software name used and the current timestamp.

    Returns
    -------
    str
        The generated sample name.
    """
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_name = "-".join(
        [
            user_input,
            time_stamp,
        ]
    )

    return sample_name
