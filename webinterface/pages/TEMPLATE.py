"""Streamlit-based web interface for ProteoBench."""

import json
import logging
from datetime import datetime

import streamlit as st
import streamlit_utils
from streamlit_extras.let_it_rain import rain

from proteobench.modules.template.module import Module
from proteobench.modules.template.parse_settings import INPUT_FORMATS, LOCAL_DEVELOPMENT, TEMPLATE_RESULTS_PATH
from proteobench.modules.template.plot import plot_bench1, plot_bench2

logger = logging.getLogger(__name__)

## Different parts of the web application
# Data for generating the figures
# This is usually
# a) The result of the given datapoint
RESULT_PERF = "result_perf"
# b) All datapoints read from a json file or downloaded from the web
ALL_DATAPOINTS = "all_datapoints"
SUBMIT = "submit"
# Add your figures here
FIG1 = "fig1"
FIG2 = "fig2"

if "submission_ready" not in st.session_state:
    st.session_state["submission_ready"] = False


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
        if SUBMIT not in st.session_state:
            st.session_state[SUBMIT] = False
        self._main_page()
        self._sidebar()

    # Here the user can select the input file format. This is defined in the
    # modules folder in the io_parse_settings folder
    def generate_input_field(self, input_format: str, content: dict):
        if content["type"] == "text_input":
            return st.text_input(content["label"], content["value"][input_format])
        if content["type"] == "number_input":
            return st.number_input(
                content["label"],
                value=content["value"][input_format],
                format=content["format"],
            )
        if content["type"] == "selectbox":
            return st.selectbox(
                content["label"],
                content["options"],
                content["options"].index(content["value"][input_format]),
            )
        if content["type"] == "checkbox":
            return st.checkbox(content["label"], content["value"][input_format])

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
                "Search engine", INPUT_FORMATS, help=self.texts.Help.input_format
            )

            # self.user_input["pull_req"] = st.text_input(
            #     "Open pull request to make results available to everyone (type \"YES\" to enable)",
            #     "NO"
            # )

            with st.expander("Additional parameters"):
                # Here the user enters metadata about the data analysis
                with open("../webinterface/configuration/template.json") as file:
                    config = json.load(file)

                for key, value in config.items():
                    self.user_input[key] = self.generate_input_field(self.user_input["input_format"], value)
            submit_button = st.form_submit_button("Parse and bench", help=self.texts.Help.additional_parameters)

        # if st.session_state[SUBMIT]:
        if FIG1 in st.session_state:
            self._populate_results()

        if submit_button:
            self._run_proteobench()

    def _populate_results(self):
        self.generate_results("", None, None, False)

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image(
            "https://upload.wikimedia.org/wikipedia/commons/8/85/Garden_bench_001.jpg",
            width=150,
        )
        # st.sidebar.markdown(self.texts.Sidebar.badges)
        st.sidebar.header("About")
        st.sidebar.markdown(self.texts.Sidebar.about, unsafe_allow_html=True)

    def _run_proteobench(self):
        # Run Proteobench
        st.header("Running Proteobench")
        status_placeholder = st.empty()
        status_placeholder.info(":hourglass_flowing_sand: Running Proteobench...")

        if ALL_DATAPOINTS not in st.session_state:
            st.session_state[ALL_DATAPOINTS] = None

        try:
            result_performance, all_datapoints = Module().benchmarking(
                self.user_input["input_csv"],
                self.user_input["input_format"],
                self.user_input,
                st.session_state["all_datapoints"],
            )
            st.session_state[ALL_DATAPOINTS] = all_datapoints
        except Exception as e:
            status_placeholder.error(":x: Proteobench ran into a problem")
            st.exception(e)
        else:
            self.generate_results(status_placeholder, result_performance, all_datapoints, True)

    def generate_results(self, status_placeholder, result_performance, all_datapoints, recalculate):
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if recalculate:
            status_placeholder.success(":heavy_check_mark: Finished!")

            # Show head of result DataFrame
        st.header("Results")
        st.subheader("Sample of the processed file")
        if not recalculate:
            result_performance = st.session_state[RESULT_PERF]
            all_datapoints = st.session_state[ALL_DATAPOINTS]
        st.dataframe(result_performance.head(100))

        # Plot results
        # set your title
        st.subheader("TITLE FOR FIGURE 1")
        if recalculate:
            # calling the plot functions in modules/template/plot.py
            fig = plot_bench1(result_performance)
        else:
            fig = st.session_state[FIG1]
        st.plotly_chart(fig, use_container_width=True)

        # set your title
        st.subheader("TITLE FOR FIGURE 2")
        # show metadata
        # st.text(all_datapoints.head(100))

        if recalculate:
            # calling the plot functions in modules/template/plot.py
            fig2 = plot_bench1(all_datapoints)
        else:
            fig2 = st.session_state[FIG2]
        st.plotly_chart(fig2, use_container_width=True)

        # Naming the sample with specifics about input and analysis
        sample_name = "%s-%s-%s-%s" % (
            self.user_input["input_format"],
            self.user_input["version"],
            self.user_input["mbr"],
            time_stamp,
        )

        # Download link
        st.subheader("Download calculated ratios")
        st.download_button(
            label="Download",
            data=streamlit_utils.save_dataframe(result_performance),
            file_name=f"{sample_name}.csv",
            mime="text/csv",
        )
        st.subheader("Add results to online repository")
        st.session_state[FIG1] = fig
        st.session_state[FIG2] = fig2
        st.session_state[RESULT_PERF] = result_performance
        st.session_state[ALL_DATAPOINTS] = all_datapoints

        checkbox = st.checkbox("I confirm that the metadata is correct")
        if checkbox:
            st.session_state["submission_ready"] = True
            submit_pr = st.button("I really want to upload it")
            # TODO: check if parameters are filled
            # submit_pr = False
            if submit_pr:
                st.session_state[SUBMIT] = True
                if not LOCAL_DEVELOPMENT:
                    Module().clone_pr(
                        st.session_state[ALL_DATAPOINTS],
                        st.secrets["gh"]["token"],
                        username="Proteobot",
                        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
                        branch_name="new_branch",
                    )
                else:
                    DDA_QUANT_RESULTS_PATH = Module().write_json_local_development(st.session_state[ALL_DATAPOINTS])
        if SUBMIT in st.session_state:
            if st.session_state[SUBMIT]:
                # status_placeholder.success(":heavy_check_mark: Successfully uploaded data!")
                st.subheader("SUCCESS")
                st.session_state[SUBMIT] = False
                rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)


## Inline documentation. This is the one for the DDA_Quant module
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

        input_format = """
            Please select the software you used to generate the search engine results.
            You can check the toml files at https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules/dda_quant/io_parse_settings
            for more details.
            Additionally, you can use the tab-delimited Custom format containing the following columns:
            Sequence: peptide sequence
            Proteins: Protein accessions according to fasta file
            Charge (optional): Charge state of measured peptide
            FQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01: Quantitative column sample 1
            LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02: Quantitative column sample 2
            LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03: Quantitative column sample 3
            LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01: Quantitative column sample 4
            LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02: Quantitative column sample 5
            LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03: Quantitative column sample 6
        """

        additional_parameters = """
            Please provide all details about the used parameter for the database search. They will facilitate the comparison.
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
