"""Tab 3 (2.5): In-depth plots for current data in the Quant module."""

import glob
import os
import uuid
import zipfile
import subprocess
import logging

from datetime import datetime
from typing import Optional
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st
import streamlit_utils
from plotly import graph_objects as go

logger: logging.Logger = logging.getLogger(__name__)


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
            zip_path = zip_files[0]

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

    random_uuid = uuid.uuid4()
    if public_id == "Uploaded dataset":
        # user uploaded data does not have sample name yet
        sample_name = generate_sample_name(user_input=user_input["input_format"])
    else:
        # use public run name as sample name
        sample_name = public_id
    st.download_button(
        label="Download table",
        data=streamlit_utils.save_dataframe(performance_data),
        file_name=f"{sample_name}.csv",
        mime="text/csv",
        key=f"{random_uuid}",
        icon=":material/download:",
    )

    display_pmultiqc_report(performance_data=performance_data, sample_name=sample_name)

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


def display_pmultiqc_report(performance_data: pd.DataFrame, sample_name: str) -> None:

    st.subheader("pMultiQC Report")
    st.markdown(
        "pMultiQC Reports contain additional QC plots for e.g. missing values, CV distributions, and intensity distributions. Report generation might take up to a minute."
    )

    html_content = st.session_state.get("tab31_pmultiqc_html_content_" + sample_name, "")
    if not html_content:
        html_content = create_pmultiqc_report_section(performance_data)
        st.session_state["tab31_pmultiqc_html_content_" + sample_name] = html_content
        logger.info(
            "pMultiQC report generated.",
        )
    else:
        logger.info(
            'using cached pMultiQC report from session_state["tab31_pmultiqc_html_content_{}"].'.format(sample_name)
        )
    download_disactivate = True
    if html_content:
        download_disactivate = False
    show_download_button(html_content, disabled=download_disactivate, sample_name=sample_name)


def show_download_button(html_content: str, disabled: bool, sample_name: str) -> None:
    """
    Display a download button for the pMultiQC report.
    """
    st.markdown("Download the pMultiQC report generated from the intermediate data.")
    # components.html(html_content, height=800, scrolling=True)
    st.download_button(
        label="Download pMultiQC Report",
        file_name="pMultiQC_report_{}.html".format(sample_name),
        data=html_content,
        disabled=disabled,
        mime="text/html",
    )


def create_pmultiqc_report_section(performance_data: pd.DataFrame) -> str:
    """
    Create a section in the Streamlit app to display the pMultiQC report.
    """
    html_content = ""
    if st.button("Generate pMultiQC Report"):
        df_intermediate_results = performance_data
        with TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            tmp_data = (tmp_dir / "data").resolve()
            tmp_data.mkdir(parents=True, exist_ok=True)
            df_intermediate_results.to_csv(tmp_data / "result_performance.csv", index=False)
            file_out = tmp_dir
            ret_code = subprocess.run(
                [
                    "multiqc",
                    "--parse_proteobench",
                    f"{tmp_data}",
                    "-o",
                    f"{file_out}",
                    "-f",
                    "--clean-up",
                ],
                check=False,
            )
            html_path = Path(file_out) / "multiqc_report.html"
            if html_path.exists() and ret_code.returncode == 0:
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                st.success("pMultiQC report generated successfully.")
            else:
                st.error("Error generating pMultiQC report. Please check the logs.")
    return html_content
