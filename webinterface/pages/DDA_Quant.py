"""Streamlit-based web interface for ProteoBench."""

import logging
from datetime import datetime

from proteobench.modules.dda_quant import module_dda_quant
from proteobench.modules.dda_quant.parse_settings_dda_quant import \
    INPUT_FORMATS

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

import streamlit as st
from streamlit_utils import hide_streamlit_menu, save_dataframe

from proteobench.github.gh import clone_pr
from proteobench.modules.dda_quant import plot_dda_id

logger = logging.getLogger(__name__)

ALL_DATAPOINTS = "all_datapoints"
SUBMIT = 'submit'
FIG1 = 'fig1'
FIG2 = 'fig2'
RESULT_PERF = 'result_perf'

if 'submission_ready' not in st.session_state:
    st.session_state['submission_ready'] = False

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
                INPUT_FORMATS
            )

            # self.user_input["pull_req"] = st.text_input(
            #     "Open pull request to make results available to everyone (type \"YES\" to enable)", 
            #     "NO"
            # )

            with st.expander("Additional parameters"):
                self.user_input["version"] = st.text_input(
                    "Search engine version", 
                    "1.5.8.3"
                )

                self.user_input["software_name"] = st.text_input(
                    "software name", 
                    "Search engine name"
                )

                self.user_input["fdr_psm"] = st.text_input(
                    "FDR psm", 
                    "0.01"
                )
                
                self.user_input["fdr_peptide"] = st.text_input(
                    "FDR peptide", 
                    "0.01"
                )

                self.user_input["fdr_protein"] = st.text_input(
                    "FDR protein", 
                    "0.01"
                )

                self.user_input["precursor_mass_tolerance"] = st.text_input(
                    "Precursor mass tolerance", 
                    "10.0"
                )

                self.user_input["precursor_mass_tolerance_unit"] = st.selectbox(
                    "Precursor tolerance unit",
                    ("PPM", "Da")
                )

                self.user_input["fragment_mass_tolerance"] = st.text_input(
                    "Fragment mass tolerance", 
                    "10.0"
                )

                self.user_input["fragment_mass_tolerance_unit"] = st.selectbox(
                    "",
                    ("PPM", "Da")
                )

                self.user_input["search_enzyme_name"] = st.selectbox(
                    "Enzyme",
                    ("Trypsin", "Chemotrypsin")
                )

                self.user_input["allowed_missed_cleavage"] = st.text_input(
                    "Allowed missed cleavage", 
                    "2"
                )

                self.user_input["fixed_mods"] = st.text_input(
                    "What fixed mods were set", 
                    "CAM"
                )

                self.user_input["variable_mods"] = st.text_input(
                    "What variable mods were set", 
                    "MOxid"
                )

                self.user_input["precursor_charge"] = st.text_input(
                    "Possible charge states", 
                    "[2,3,4,5,6]"
                )

                self.user_input["max_num_mods_on_peptide"] = st.text_input(
                    "Maximum number of modifications on peptides", 
                    "2"
                )

                self.user_input["min_peptide_length"] = st.text_input(
                    "Minimum peptide length", 
                    "6"
                )

                self.user_input["max_peptide_length"] = st.text_input(
                    "max_peptide_length", 
                    "25"
                )

                self.user_input["mbr"] = st.checkbox(
                    "Quantified with MBR"
                )

                self.user_input["workflow_description"] = st.text_area(
                    "Fill in details not specified above, such as:",
                    "This workflow was run with isotope errors considering M-1, M+1, and M+2 ...", 
                    height=275
                    )

            submit_button = st.form_submit_button("Parse and bench")

                
        #if st.session_state[SUBMIT]:
        if FIG1 in st.session_state:
            self._populate_results()
            
    

        if submit_button:
            self._run_proteobench()


    def _populate_results(self):
        self.generate_results("", 
                None,
                None,
                False)


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
        
        if ALL_DATAPOINTS not in st.session_state:
            st.session_state[ALL_DATAPOINTS] = None
        

        try:
            result_performance, all_datapoints = module_dda_quant.benchmarking(
                self.user_input["input_csv"],
                self.user_input["input_format"],
                self.user_input,
                st.session_state['all_datapoints']
            )
            st.session_state[ALL_DATAPOINTS] = all_datapoints
        except Exception as e:
            status_placeholder.error(":x: Proteobench ran into a problem")
            st.exception(e)
        else:
            self.generate_results(status_placeholder, 
                result_performance,
                all_datapoints,
                True)

    def generate_results(self, 
        status_placeholder, 
        result_performance, 
        all_datapoints,
        recalculate):
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
            fig = plot_dda_id.plot_bench(result_performance)
        else:
            fig = st.session_state[FIG1]
        st.plotly_chart(fig, use_container_width=True)
            
            
        st.subheader("Mean error between conditions")
        st.text(all_datapoints.head(100))
        if recalculate:
            fig2 = plot_dda_id.plot_metric(all_datapoints) 
        else:
            fig2 = st.session_state[FIG2]
        st.plotly_chart(fig2, use_container_width=True)

        sample_name = "%s-%s-%s-%s" % (self.user_input["input_format"],self.user_input["version"],self.user_input["mbr"],time_stamp)

            # Download link
        st.subheader("Download calculated ratios")
        st.download_button(
                label="Download",
                data=save_dataframe(result_performance),
                file_name=f"{sample_name}.csv",
                mime="text/csv"
            )

        
        st.subheader("Add results to online repository")
        st.session_state[FIG1] = fig
        st.session_state[FIG2] = fig2
        st.session_state[RESULT_PERF]=result_performance
        st.session_state[ALL_DATAPOINTS] = all_datapoints

        
        checkbox = st.checkbox('I confirm that the metadata is correct')
        if checkbox:
            st.session_state['submission_ready'] = True 
            submit_pr = st.button("I really want to upload it")
                    #TODO: check if parameters are filled
                    #submit_pr = False
            if submit_pr:
                st.session_state[SUBMIT]=True
                clone_pr(
                        st.session_state[ALL_DATAPOINTS],
                        st.secrets["gh"]["token"],
                        username="Proteobot",
                        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
                        branch_name="new_branch"
                )
        if SUBMIT in st.session_state:
            if st.session_state[SUBMIT]:
            #status_placeholder.success(":heavy_check_mark: Successfully uploaded data!")
                st.subheader("SUCCESS")
                st.session_state[SUBMIT]=False


            

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
