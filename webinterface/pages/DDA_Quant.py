"""Streamlit-based web interface for DeepLC."""

import logging
import os
import pathlib
from datetime import datetime
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

import streamlit as st
from streamlit_utils import hide_streamlit_menu, save_dataframe

import pandas as pd
import numpy as np
import itertools
from matplotlib import pyplot as plt
from datetime import datetime

from collections import Counter
import toml
from proteobench.modules.dda_quant import main
from proteobench.modules.dda_quant.plot.plot import plot_bench

logger = logging.getLogger(__name__)


class DeepLCStreamlitError(Exception):
    pass


class MissingPeptideCSV(DeepLCStreamlitError):
    pass

class StreamlitUI:
    """Proteobench Streamlit UI."""

    def __init__(self):
        """Proteobench Streamlit UI."""
        self.texts = WebpageTexts
        self.user_input = dict()

        st.set_page_config(
            page_title="Proteobench web server",
            page_icon=":rocket:",
            layout="centered",
            initial_sidebar_state="expanded",
        )

        self._main_page()
        self._sidebar()

    def _main_page(self):
        """Format main page."""
        st.title("Proteobench")
        st.header("Input and configuration")

        with st.form(key="main_form"):
            st.subheader("Input files")
            self.user_input["input_csv"] = st.file_uploader(
                "Search engine result file", help=self.texts.Help.input_file
            )

            self.user_input["input_format"] = st.selectbox(
                "Search engine",

                ("MaxQuant", "AlphaPept", "Proline", "WOMBAT", "MSFragger")
            )

            self.user_input["version"] = st.text_input(
                "Search engine version", 
                "1.5.8.3"
            )

            self.user_input["mbr"] = st.checkbox(
                "Quantified with MBR"
            )

            self.user_input["workflow_description"] = st.text_area("Fill in details not specified above, such as:","This workflow was run with isotope errors considering M-1, M+1, and M+2 ...", height=275)


            st.subheader("Add results to online repository")

            
            self.user_input["pull_req"] = st.text_input(
                "Open pull request to make results available to everyone (type \"YES\" to enable)", 
                "NO"
            )
            

            with st.expander("What does this \"pull reqest\" mean?"):
                st.markdown(self.texts.Help.pull_req)
            submit_button = st.form_submit_button("Parse and bench")

        if submit_button:
            try:
                self._run_proteobench()
            except MissingPeptideCSV:
                st.error(self.texts.Errors.missing_peptide_csv)

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image(
            "https://upload.wikimedia.org/wikipedia/commons/8/85/Garden_bench_001.jpg",
            width=150,
        )
        #st.sidebar.markdown(self.texts.Sidebar.badges)
        st.sidebar.header("About")
        st.sidebar.markdown(self.texts.Sidebar.about, unsafe_allow_html=True)

    def _run_proteobench(self):
        # Run Proteobench
        st.header("Running Proteobench")
        status_placeholder = st.empty()
        status_placeholder.info(":hourglass_flowing_sand: Running Proteobench...")

        try:
            result_performance = main(
                self.user_input["input_csv"],
                self.user_input["input_format"],
                self.user_input["mbr"]
            )
        except Exception as e:
            status_placeholder.error(":x: Proteobench ran into a problem")
            st.exception(e)
        else:
            time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            status_placeholder.success(":heavy_check_mark: Finished!")

            # Show head of result DataFrame
            st.header("Results")
            st.subheader("Sample of the processed file")
            st.dataframe(result_performance.head(100))

            # Plot results
            st.subheader("Ratio between conditions")
            fig = plot_bench(result_performance)
            st.plotly_chart(fig, use_container_width=True)

            sample_name = "%s-%s-%s-%s" % (self.user_input["input_format"],self.user_input["version"],self.user_input["mbr"],time_stamp)

            # Download link
            st.subheader("Download calculated ratios")
            st.download_button(
                label="Download",
                data=save_dataframe(result_performance),
                file_name=f"{sample_name}.csv",
                mime="text/csv"
            )

    def _parse_user_config(self, user_input):
        """Validate and parse user input."""
        return config

class WebpageTexts:
    class Sidebar:

        about = f"""
            """

    class Help:
        input_file = """
            Output file of the search engine
            """

        pull_req = """
            It is open to the public indefinitely.
            """

    class Errors:
        missing_peptide_csv = """
            Upload a peptide CSV file or select the _Use example data_ checkbox.
            """
        missing_calibration_peptide_csv = """
            Upload a calibration peptide CSV file or select another _Calibration
            peptides_ option.
            """
        missing_calibration_column = """
            Upload a peptide CSV file with a `tr` column or select another _Calibration
            peptides_ option.
            """
        invalid_peptide_csv = """
            Uploaded peptide CSV file could not be read. Click on _Info about peptide
            CSV formatting_ for more info on the correct input format.
            """
        invalid_calibration_peptide_csv = """
            Uploaded calibration peptide CSV file could not be read. Click on _Info
            about peptide CSV formatting_ for more info on the correct input format.
            """


if __name__ == "__main__":
    StreamlitUI()
