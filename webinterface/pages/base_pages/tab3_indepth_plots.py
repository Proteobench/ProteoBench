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

from proteobench.plotting.plot_quant import PlotDataPoint


def generate_indepth_plots(
    variables_quant,
    parsesettingsbuilder,
    user_input,
    recalculate: bool,
    public_id: Optional[str],
    public_hash: Optional[str],
) -> go.Figure:
    """
    Generate and return plots based on the current benchmark data in Tab 2.5.

    Parameters
    ----------
    recalculate : bool
        Whether to recalculate the plots.
    public_id : Optional[str], optional
        The dataset to plot, either "Uploaded dataset" or name of public run.
    public_hash : Optional[str], optional
        The hash of the selected public dataset. If None, the uploaded dataset is displayed.

    Returns
    -------
    go.Figure
        The generated plots for the selected dataset.
    """
    # no uploaded dataset and no public dataset selected? nothing to plot!
    if variables_quant.result_perf not in st.session_state.keys():
        if public_hash is None:
            st.error(":x: Please submit a result file or select a public run for display", icon="🚨")
            return False
        elif public_id == "Uploaded dataset":
            st.error(":x: Please submit a result file in the Submit New Data Tab", icon="🚨")
            return False

    if public_id == "Uploaded dataset":
        performance_data = st.session_state[variables_quant.result_perf]
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

    # Filter the data based on the slider condition (as before)
    performance_data = performance_data[
        performance_data["nr_observed"] >= st.session_state[st.session_state[variables_quant.slider_id_uuid]]
    ]

    if recalculate:
        parse_settings = parsesettingsbuilder.build_parser(user_input["input_format"])

        fig_logfc = PlotDataPoint.plot_fold_change_histogram(
            performance_data,
            parse_settings.species_expected_ratio(),
        )
        fig_CV = PlotDataPoint.plot_CV_violinplot(performance_data)
        fig_MA = PlotDataPoint.plot_ma_plot(
            performance_data,
            parse_settings.species_expected_ratio(),
        )
        st.session_state[variables_quant.fig_cv] = fig_CV
        st.session_state[variables_quant.fig_logfc] = fig_logfc
    else:
        fig_logfc = st.session_state[variables_quant.fig_logfc]
        fig_CV = st.session_state[variables_quant.fig_cv]
        fig_MA = st.session_state[variables_quant.fig_ma_plot]

    if variables_quant.first_new_plot:
        col1, col2 = st.columns(2)
        col1.subheader("Log2 Fold Change distributions by species.")
        col1.markdown(
            """
                log2 fold changes calculated from {}
            """.format(
                public_id
            )
        )
        col1.plotly_chart(fig_logfc, use_container_width=True)

        col2.subheader("Coefficient of variation distribution in Condition A and B.")
        col2.markdown(
            """
                CVs calculated from {}
            """.format(
                public_id
            )
        )
        col2.plotly_chart(fig_CV, use_container_width=True)

        col1.markdown("---")  # optional horizontal separator

        col1.subheader("MA plot")
        col1.markdown(
            """
                MA plot calculated from {}
            """.format(
                public_id
            )
        )
        # Example: plot another figure or add any other Streamlit element
        # st.plotly_chart(fig_additional, use_container_width=True)
        col1.plotly_chart(fig_MA, use_container_width=True)

    else:
        pass

    st.subheader("Sample of the processed file for {}".format(public_id))
    st.markdown(open(variables_quant.description_table_md, "r", encoding="utf-8").read())
    st.session_state[variables_quant.df_head] = st.dataframe(performance_data.head(100))

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

    return fig_logfc


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
