"""Streamlit-based web interface for ProteoBench."""

import json
import logging
from datetime import datetime

from proteobench.modules.dda_quant.module import Module
from proteobench.modules.dda_quant.parse_settings import (
    DDA_QUANT_RESULTS_PATH, INPUT_FORMATS, LOCAL_DEVELOPMENT)
from proteobench.modules.dda_quant.plot import PlotDataPoint

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

import streamlit as st
import streamlit_utils
from streamlit_extras.let_it_rain import rain
import uuid

#from proteobench.github.gh import clone_pr, write_json_local_development

logger = logging.getLogger(__name__)

ALL_DATAPOINTS = "all_datapoints"
SUBMIT = "submit"
FIG1 = "fig1"
FIG2 = "fig2"
RESULT_PERF = "result_perf"
META_DATA = "meta_data"

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
            layout="wide",
            initial_sidebar_state="expanded"
        )
        if SUBMIT not in st.session_state:
            st.session_state[SUBMIT] = False
        self._main_page()
        self._sidebar()

    def generate_input_field(self, input_format: str, content: dict):
        if content["type"] == "text_input":
            if "placeholder" in content:
                return st.text_input(content["label"], placeholder=content["placeholder"])
            elif "value" in content:
                return st.text_input(content["label"], content["value"][input_format])
        if content["type"] == "number_input":
            return st.number_input(
                content["label"],
                value=None,
                format=content["format"],
                min_value=content["min_value"],
                max_value=content["max_value"]
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
        st.title("Module 2: DDA quantification")
        st.header("Description of the module")
        st.markdown(
            """
                    This module compares the MS1-level quantification tools for
                    data-dependent acquisition (DDA). The raw files provided for
                    this module are presented in the comprehensive LFQ benchmark
                    dataset from [Van Puyvelde et al., 2022](https://www.nature.com/articles/s41597-022-01216-6).
                    The samples contain tryptic peptides from Homo sapiens,
                    Saccharomyces cerevisiae, and Escherichia coli, mixed in different
                    ratios (condition A and condition B), with three replicates of each
                    condition. With these samples, we calculate three metrics:  
                    - To estimate the sensitivity of the workflows, we report the
                    number of unique precursors (charged modified sequence) quantified
                    in all 6 runs.  
                    - To estimate the accuracy of the workflows, we report the weighted
                    sum of precursor deviation from expected ratios.  
                    - To estimate the precision of the workflows, we report the weighted
                     average of the interquartile range (IQR) of the precursors ratio.  
                    
                    ProteoBench plots these three metrics to visualize workflow outputs
                     from different tools, with different versions, and/or different
                    sets of parameters for the search and quantification.
                    The full description of the pre-processing steps and metrics
                    calculation is available here: LINK.
                    """
        )
        st.header("Downloading associated files")
        st.markdown(
            """
                    The raw files used for this module were acquired on an Orbitrap
                    Q-Exactive H-FX (ThermoScientific). They can be downloaded from the
                    proteomeXchange repository PXD028735. You can download them here:  
                    [LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD028735/LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01.raw)  
                    [LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD028735/LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02.raw)  
                    [LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD028735/LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03.raw)  
                    [LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD028735/LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01.raw)  
                    [LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD028735/LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02.raw)  
                    [LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03.raw](https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD028735/LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03.raw)  

                    **It is imperative not to rename the files once downloaded!**
                    """
        )
        st.markdown(
            """
                    Download the fasta file here: [TODO]  
                    The fasta file provided for this module contains the three species
                    present in the samples and contaminant proteins
                    ([Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145))
                    """
        )

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
                with open("../webinterface/configuration/dda_quant.json") as file:
                    config = json.load(file)

                for key, value in config.items():
                    self.user_input[key] = self.generate_input_field(
                        self.user_input["input_format"], value
                    )
            
            submit_button = st.form_submit_button(
                "Parse and bench", help=self.texts.Help.additional_parameters
            )

        # if st.session_state[SUBMIT]:
        if FIG1 in st.session_state:
            self._populate_results()

        if submit_button:
            if self.user_input["input_csv"]:
                self._run_proteobench()
            else:
                 error_message = st.error(":x: Please provide a result file")

    def _populate_results(self):
        self.generate_results("", None, None, False)

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image("https://github.com/Proteobench/ProteoBench/raw/Add-logos/webinterface/logos/logo_proteobench/proteobench-logo-horizontal.svg",
                width=300)
        st.sidebar.image("https://raw.githubusercontent.com/Proteobench/ProteoBench/b6d40e853df10e486e0000aed9fe7b5ddc3f9286/webinterface/logos/logo_funding/DDSA_PrimaryLogo_Screen_Black.svg",
                width=300)
        mainlogo_list = [
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_funding/eubic_logo_transparent.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_funding/eupa-logo-transparent.png?raw=true"
        ]
        for i in range(0,len(mainlogo_list),3):
            st.sidebar.image(
                mainlogo_list[i:i+3],
                width=140,
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
            self.generate_results(
                status_placeholder, result_performance, all_datapoints, True
            )

    def generate_results(
        self, status_placeholder, result_performance, all_datapoints, recalculate
    ):
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
        st.subheader("Ratio between conditions")
        if recalculate:
            fig = PlotDataPoint().plot_bench(result_performance)
        else:
            fig = st.session_state[FIG1]
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Mean error between conditions")
        # show metadata
        # st.text(all_datapoints.head(100))

        if recalculate:
            fig2 = PlotDataPoint().plot_metric(all_datapoints)
        else:
            fig2 = st.session_state[FIG2]
        st.plotly_chart(fig2, use_container_width=True)

        sample_name = "%s-%s-%s-%s" % (
            self.user_input["input_format"],
            self.user_input["version"],
            self.user_input["mbr"],
            time_stamp,
        )

        # Download link
        st.subheader("Download calculated ratios")
        random_uuid = uuid.uuid4()
        st.download_button(
            label="Download",
            data=streamlit_utils.save_dataframe(result_performance),
            file_name=f"{sample_name}.csv",
            mime="text/csv",
            key=f"{random_uuid}"
        )

        st.subheader("Add results to online repository")
        st.session_state[FIG1] = fig
        st.session_state[FIG2] = fig2
        st.session_state[RESULT_PERF] = result_performance
        st.session_state[ALL_DATAPOINTS] = all_datapoints

        self.user_input[META_DATA] = st.file_uploader(
                "Meta data for searches", help=self.texts.Help.meta_data_file
            )
        self.user_input["comments_for_submission"] = st.text_area("Comments for submission", 
            placeholder="Anything else you want to let us know? Please specifically add changes in your search parameters here, that are not obvious from the parameter file.",
            height=200)
        checkbox = st.checkbox("I confirm that the metadata is correct")
        
        if checkbox and self.user_input[META_DATA]:
            st.session_state["submission_ready"] = True
            submit_pr = st.button("I really want to upload it")
            # TODO: update parameters of point to submit with parsed metadata parameters
            # submit_pr = False
            if submit_pr:
                st.session_state[SUBMIT] = True
                user_comments = self.user_input["comments_for_submission"]
                if not LOCAL_DEVELOPMENT:
                    Module().clone_pr(
                        st.session_state[ALL_DATAPOINTS],
                        st.secrets["gh"]["token"],
                        username="Proteobot",
                        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
                        branch_name="new_branch",
                        submission_comments=user_comments
                    )
                else:
                    DDA_QUANT_RESULTS_PATH = Module().write_json_local_development(
                        st.session_state[ALL_DATAPOINTS]
                    )
        if SUBMIT in st.session_state:
            if st.session_state[SUBMIT]:
                # status_placeholder.success(":heavy_check_mark: Successfully uploaded data!")
                st.subheader("SUCCESS")
                st.session_state[SUBMIT] = False
                rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)


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

        meta_data_file = """
            Please add a file with meta data that contains all relevant information about your search parameters
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
