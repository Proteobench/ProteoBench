"""Streamlit-based web interface for ProteoBench."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit_utils
from proteobench.modules.dda_quant_peptidoform.parse_settings import ModuleSettings
from streamlit_extras.let_it_rain import rain

from proteobench.modules.dda_quant_base.datapoint import (
    filter_df_numquant_median_abs_epsilon,
    filter_df_numquant_nr_prec,
)
from proteobench.modules.dda_quant_base.parse_settings import ParseSettings

from proteobench.modules.dda_quant_base.plot import PlotDataPoint
from proteobench.modules.dda_quant_peptidoform.module import PeptidoformModule

logger = logging.getLogger(__name__)

ALL_DATAPOINTS = "all_datapoints"
SUBMIT = "submit"
FIG_LOGFC = "fig_logfc"
FIG_METRIC = "fig_metric"
FIG_CV = "fig_CV_violinplot"
RESULT_PERF = "result_perf"
META_DATA = "meta_data"
INPUT_DF = "input_df"
META_FILE_UPLOADER_UUID = "meta_file_uploader_uuid"
COMMENTS_SUBMISSION_UUID = "comments_submission_uuid"
CHECK_SUBMISSION_UUID = "check_submission_uuid"
META_DATA_TEXT = "comments_for_submission"
CHECK_SUBMISSION = "heck_submission"
BUTTON_SUBMISSION_UUID = "button_submission_uuid"
DF_HEAD = "df_head"
PLACEHOLDER_FIG_COMPARE = "placeholder_fig_compare"
PLACEHOLDER_TABLE = "placeholder_table"
PLACEHOLDER_SLIDER = "placeholder_slider"
HIGHLIGHT_LIST = "highlight_list"
FIRST_NEW_PLOT = True
DEFAULT_VAL_SLIDER = 3

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
            initial_sidebar_state="expanded",
        )
        if SUBMIT not in st.session_state:
            st.session_state[SUBMIT] = False
        self._main_page()
        self._sidebar()

    def generate_input_field(self, input_format: str, content: dict):
        if content["type"] == "text_area":
            if "placeholder" in content:
                return st.text_area(content["label"], placeholder=content["placeholder"], height=content["height"])
            elif "value" in content:
                return st.text_area(content["label"], content["value"][input_format], height=content["height"])
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
                max_value=content["max_value"],
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
        st.title("DDA quantification - peptidoforms")
        st.warning(
            "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
        )
        st.header("Description of the module")
        st.markdown(
            Path("pages/markdown_files/dda_quant_peptidoform/module_description.md").read_text()
        )
        st.header("Downloading associated files")
        st.markdown(
            Path("pages/markdown_files/dda_quant_base/raw_file_download.md").read_text(),
            unsafe_allow_html=True
        )

        st.header("Input and configuration")
        st.markdown(
            """
                   Scroll down if you want to see the public benchmark runs publicly available
                   today.
                    """
        )

        with st.form(key="main_form"):
            st.subheader("Input files")
            st.markdown(
                Path("pages/markdown_files/dda_quant_base/input_file_button.md").read_text()
            )
            self.user_input["input_csv"] = st.file_uploader(
                "Software tool result file", help=self.texts.Help.input_file
            )

            self.user_input["input_format"] = st.selectbox(
                "Software tool", ParseSettings.module_settings.INPUT_FORMATS, help=self.texts.Help.input_format
            )

            # self.user_input["pull_req"] = st.text_input(
            #     "Open pull request to make results available to everyone (type \"YES\" to enable)",
            #     "NO"
            # )
            st.markdown(
                Path("pages/markdown_files/dda_quant_base/input_customParam_button.md").read_text()
            )
            with st.expander("Additional parameters"):
                with open("../webinterface/configuration/dda_quant.json") as file:
                    config = json.load(file)

                for key, value in config.items():
                    self.user_input[key] = self.generate_input_field(self.user_input["input_format"], value)

            st.markdown(
                """
                    Now, press `Parse and Bench` to calculate the metrics from your input. 
                    """
            )

            submit_button = st.form_submit_button("Parse and bench", help=self.texts.Help.parse_button)

        if submit_button:
            if self.user_input["input_csv"]:
                if META_FILE_UPLOADER_UUID in st.session_state.keys():
                    del st.session_state[META_FILE_UPLOADER_UUID]
                if COMMENTS_SUBMISSION_UUID in st.session_state.keys():
                    del st.session_state[COMMENTS_SUBMISSION_UUID]
                if CHECK_SUBMISSION_UUID in st.session_state.keys():
                    del st.session_state[CHECK_SUBMISSION_UUID]
                if BUTTON_SUBMISSION_UUID in st.session_state.keys():
                    del st.session_state[BUTTON_SUBMISSION_UUID]

                self._run_proteobench()
            else:
                error_message = st.error(":x: Please provide a result file")

        if FIG_LOGFC in st.session_state:
            self._populate_results()

        if "slider_id" in st.session_state.keys():
            default_val_slider = st.session_state[st.session_state["slider_id"]]
        else:
            default_val_slider = DEFAULT_VAL_SLIDER

        if ALL_DATAPOINTS not in st.session_state or FIRST_NEW_PLOT == True:
            st.session_state[ALL_DATAPOINTS] = None
            all_datapoints = st.session_state[ALL_DATAPOINTS]
            all_datapoints = PeptidoformModule(ModuleSettings).obtain_all_data_point(all_datapoints)

            all_datapoints["median_abs_epsilon"] = all_datapoints["results"].apply(
                filter_df_numquant_median_abs_epsilon, min_quant=default_val_slider
            )
            all_datapoints["nr_prec"] = all_datapoints["results"].apply(
                filter_df_numquant_nr_prec, min_quant=default_val_slider
            )

            if HIGHLIGHT_LIST not in st.session_state.keys():
                all_datapoints.insert(0, "Highlight", [False] * len(all_datapoints.index))
            else:
                all_datapoints.insert(0, "Highlight", st.session_state[HIGHLIGHT_LIST])

            st.markdown(
                """
                    Choose with the slider below the minimum number of quantification value 
                    per raw file.  
                    Example: when 3 is selected, only the precursor ions quantified in 
                    3 or more raw files will be considered for the plot. 
                        """
            )

            st.session_state[PLACEHOLDER_SLIDER] = st.empty()
            st.session_state[PLACEHOLDER_FIG_COMPARE] = st.empty()
            st.session_state[PLACEHOLDER_TABLE] = st.empty()

            st.session_state["slider_id"] = uuid.uuid4()
            st.session_state["table_id"] = uuid.uuid4()

            st.session_state[PLACEHOLDER_SLIDER].select_slider(
                label="Minimal ion quantifications (# samples)",
                options=[1, 2, 3, 4, 5, 6],
                value=default_val_slider,
                on_change=self.slider_callback,
                key=st.session_state["slider_id"],
            )

            fig_metric = PlotDataPoint.plot_metric(all_datapoints)

            st.session_state[ALL_DATAPOINTS] = all_datapoints
            st.session_state[FIG_METRIC] = fig_metric

            st.session_state[PLACEHOLDER_FIG_COMPARE].plotly_chart(
                st.session_state[FIG_METRIC], use_container_width=True
            )

            st.session_state[PLACEHOLDER_TABLE].data_editor(
                st.session_state[ALL_DATAPOINTS], key=st.session_state["table_id"], on_change=self.table_callback
            )

    def _populate_results(self):
        self.generate_results("", None, None, False, None)

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image("logos/logo_funding/main_logos_sidebar.png", width=300)

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
            if "slider_id" in st.session_state.keys():
                default_val_slider = st.session_state[st.session_state["slider_id"]]
            else:
                default_val_slider = DEFAULT_VAL_SLIDER
            parse_settings = ParseSettings(self.user_input["input_format"])

            result_performance, all_datapoints, input_df = PeptidoformModule(ModuleSettings).benchmarking(
                parse_settings,
                self.user_input["input_csv"],
                self.user_input,
                st.session_state[ALL_DATAPOINTS],
                default_cutoff_min_prec=default_val_slider,
            )

            st.session_state[ALL_DATAPOINTS] = all_datapoints

            if "Highlight" not in st.session_state[ALL_DATAPOINTS].columns:
                st.session_state[ALL_DATAPOINTS].insert(
                    0, "Highlight", [False] * len(st.session_state[ALL_DATAPOINTS].index)
                )
            else:
                st.session_state[ALL_DATAPOINTS]["Highlight"] = [False] * len(st.session_state[ALL_DATAPOINTS].index)

        except Exception as e:
            status_placeholder.error(":x: Proteobench ran into a problem")
            st.exception(e)
        else:
            self.generate_results(status_placeholder, result_performance, all_datapoints, True, input_df)

    def table_callback(self):
        min_quant = st.session_state[st.session_state["slider_id"]]
        edits = st.session_state[st.session_state["table_id"]]["edited_rows"].items()
        for k, v in edits:
            try:
                st.session_state[ALL_DATAPOINTS][list(v.keys())[0]].iloc[k] = list(v.values())[0]
            except TypeError:
                return
        st.session_state[HIGHLIGHT_LIST] = list(st.session_state[ALL_DATAPOINTS]["Highlight"])
        st.session_state[PLACEHOLDER_TABLE] = st.session_state[ALL_DATAPOINTS]

        fig_metric = PlotDataPoint.plot_metric(st.session_state[ALL_DATAPOINTS])

        st.session_state[FIG_METRIC] = fig_metric

        if RESULT_PERF in st.session_state.keys():
            self.plots_for_current_data(st.session_state[RESULT_PERF], True, False, min_quant)

    def slider_callback(self):
        min_quant = st.session_state[st.session_state["slider_id"]]
        st.session_state[ALL_DATAPOINTS]["median_abs_epsilon"] = [
            filter_df_numquant_median_abs_epsilon(v, min_quant=min_quant)
            for v in st.session_state[ALL_DATAPOINTS]["results"]
        ]
        st.session_state[ALL_DATAPOINTS]["nr_prec"] = [
            filter_df_numquant_nr_prec(v, min_quant=min_quant) for v in st.session_state[ALL_DATAPOINTS]["results"]
        ]

        fig_metric = PlotDataPoint.plot_metric(st.session_state[ALL_DATAPOINTS])

        st.session_state[FIG_METRIC] = fig_metric

        if RESULT_PERF in st.session_state.keys():
            self.plots_for_current_data(st.session_state[RESULT_PERF], True, False, min_quant)

    def generate_results(
        self,
        status_placeholder,
        result_performance,
        all_datapoints,
        recalculate,
        input_df,
    ):
        global FIRST_NEW_PLOT
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if recalculate:
            status_placeholder.success(":heavy_check_mark: Finished!")

            # Show head of result DataFrame
        if FIRST_NEW_PLOT:
            st.header("Results")
            st.subheader("Sample of the processed file")
            st.markdown(
                Path("pages/markdown_files/dda_quant_peptidoform/intermediate_file_description.md").read_text()
            )
        if not recalculate:
            result_performance = st.session_state[RESULT_PERF]
            all_datapoints = st.session_state[ALL_DATAPOINTS]
            input_df = st.session_state[INPUT_DF]
        if FIRST_NEW_PLOT:
            st.session_state[DF_HEAD] = st.dataframe(result_performance.head(100))
        else:
            st.session_state[DF_HEAD] = result_performance.head(100)
            

        if "slider_id" in st.session_state.keys():
            default_val_slider = st.session_state[st.session_state["slider_id"]]
        else:
            default_val_slider = DEFAULT_VAL_SLIDER

        fig_logfc = self.plots_for_current_data(
            result_performance, recalculate, FIRST_NEW_PLOT, slider_value=default_val_slider
        )

        if FIRST_NEW_PLOT:
            st.subheader("Mean error between conditions")
            st.markdown(
                """
                    New figure including your benchmark run. The point corresponding to 
                    your data will appear bigger than the public data sets already available 
                    in ProteoBench.
                        """
            )

        if recalculate:
            all_datapoints["weighted_sum"] = [
                filter_df_numquant_median_abs_epsilon(v, min_quant=default_val_slider)
                for v in all_datapoints["results"]
            ]
            all_datapoints["nr_prec"] = [
                filter_df_numquant_nr_prec(v, min_quant=default_val_slider) for v in all_datapoints["results"]
            ]

            fig_metric = PlotDataPoint.plot_metric(all_datapoints)
            st.session_state[ALL_DATAPOINTS] = all_datapoints
            st.session_state[FIG_METRIC] = fig_metric
            # st.plotly_chart(st.session_state[FIG_METRIC], use_container_width=True)
        else:
            fig_metric = st.session_state[FIG_METRIC]
            # st.plotly_chart(st.session_state[FIG_METRIC], use_container_width=True)

        if FIRST_NEW_PLOT:
            st.markdown(
                """
                    Choose with the slider below the minimum number of quantification value 
                    per raw file.  
                    Example: when 3 is selected, only the precursor ions quantified in 
                    3 or more raw files will be considered for the plot. 
                        """
            )
            st.session_state["slider_id"] = uuid.uuid4()
            f = st.select_slider(
                label="Minimal ion quantifications (# samples)",
                options=[1, 2, 3, 4, 5, 6],
                value=default_val_slider,
                on_change=self.slider_callback,
                key=st.session_state["slider_id"],
            )

            placeholder_fig_compare = st.empty()
            placeholder_fig_compare.plotly_chart(st.session_state[FIG_METRIC], use_container_width=True)
            st.session_state[PLACEHOLDER_FIG_COMPARE] = placeholder_fig_compare

            st.session_state["table_id"] = uuid.uuid4()

            st.data_editor(
                st.session_state[ALL_DATAPOINTS], key=st.session_state["table_id"], on_change=self.table_callback
            )
        else:
            fig_metric = st.session_state[FIG_METRIC]
            st.session_state[FIG_METRIC].data[0].x = fig_metric.data[0].x
            st.session_state[FIG_METRIC].data[0].y = fig_metric.data[0].y

            st.session_state[PLACEHOLDER_FIG_COMPARE].plotly_chart(
                st.session_state[FIG_METRIC], use_container_width=True
            )

        sample_name = "%s-%s-%s-%s" % (
            self.user_input["input_format"],
            self.user_input["software_version"],
            self.user_input["enable_match_between_runs"],
            time_stamp,
        )

        # Download link
        if FIRST_NEW_PLOT:
            st.subheader("Download calculated ratios")
            random_uuid = uuid.uuid4()
            st.download_button(
                label="Download",
                data=streamlit_utils.save_dataframe(result_performance),
                file_name=f"{sample_name}.csv",
                mime="text/csv",
                key=f"{random_uuid}",
            )

            st.subheader("Add results to online repository")
            st.markdown(
                Path("pages/markdown_files/dda_quant_peptidoform/make_results_public.md").read_text()
            )
        st.session_state[FIG_LOGFC] = fig_logfc
        st.session_state[FIG_METRIC] = fig_metric
        st.session_state[RESULT_PERF] = result_performance
        st.session_state[ALL_DATAPOINTS] = all_datapoints
        st.session_state[INPUT_DF] = input_df

        # Create unique element IDs
        if META_FILE_UPLOADER_UUID in st.session_state.keys():
            meta_file_uploader_uuid = st.session_state[META_FILE_UPLOADER_UUID]
        else:
            meta_file_uploader_uuid = uuid.uuid4()
            st.session_state[META_FILE_UPLOADER_UUID] = meta_file_uploader_uuid
        if COMMENTS_SUBMISSION_UUID in st.session_state.keys():
            comments_submission_uuid = st.session_state[COMMENTS_SUBMISSION_UUID]
        else:
            comments_submission_uuid = uuid.uuid4()
            st.session_state[COMMENTS_SUBMISSION_UUID] = comments_submission_uuid
        if CHECK_SUBMISSION_UUID in st.session_state.keys():
            check_submission_uuid = st.session_state[CHECK_SUBMISSION_UUID]
        else:
            check_submission_uuid = uuid.uuid4()
            st.session_state[CHECK_SUBMISSION_UUID] = check_submission_uuid

        if FIRST_NEW_PLOT:
            self.user_input[META_DATA] = st.file_uploader(
                "Meta data for searches",
                help=self.texts.Help.meta_data_file,
                key=meta_file_uploader_uuid,
            )

            self.user_input["comments_for_submission"] = st.text_area(
                "Comments for submission",
                placeholder="Anything else you want to let us know? Please specifically add changes in your search parameters here, that are not obvious from the parameter file.",
                height=200,
                key=comments_submission_uuid,
            )

            st.session_state[META_DATA_TEXT] = self.user_input["comments_for_submission"]

            st.session_state[CHECK_SUBMISSION] = st.checkbox(
                "I confirm that the metadata is correct",
                key=check_submission_uuid,
            )

        # TODO: do we need a better handling of this?
        params = None
        if self.user_input[META_DATA]:
            try:
                params = PeptidoformModule.load_params_file(
                    self.user_input[META_DATA], self.user_input["input_format"]
                )
            except KeyError as e:
                st.error("Parsing of meta parameters file for this software is not supported yet.")
            except Exception as err:
                input_f = self.user_input["input_format"]
                st.error(
                    f"Unexpected error while parsing file. Make sure you privded a meta parameters file produced by {input_f}."
                )

        if st.session_state[CHECK_SUBMISSION] and params != None:
            st.session_state["submission_ready"] = True

            if BUTTON_SUBMISSION_UUID in st.session_state.keys():
                button_submission_uuid = st.session_state[BUTTON_SUBMISSION_UUID]
            else:
                button_submission_uuid = uuid.uuid4()
                st.session_state[BUTTON_SUBMISSION_UUID] = button_submission_uuid
            submit_pr = st.button("I really want to upload it", key=button_submission_uuid)

            # submit_pr = False
            if submit_pr:
                st.session_state[SUBMIT] = True
                user_comments = self.user_input["comments_for_submission"]
                if not LOCAL_DEVELOPMENT:
                    pr_url = PeptidoformModule().clone_pr(
                        st.session_state[ALL_DATAPOINTS],
                        params,
                        st.secrets["gh"]["token"],
                        username="Proteobot",
                        remote_git="github.com/Proteobot/Results_quant_peptidoform_DDA.git",
                        branch_name="new_branch",
                        submission_comments=user_comments,
                    )
                else:
                    DDA_QUANT_RESULTS_PATH = PeptidoformModule().write_json_local_development(
                        st.session_state[ALL_DATAPOINTS], params
                    )

                if not pr_url:
                    del st.session_state[SUBMIT]
                else:
                    id = str(all_datapoints[all_datapoints["old_new"] == "new"].iloc[-1, :]["intermediate_hash"])

                    if "storage" in st.secrets.keys():
                        PeptidoformModule.write_intermediate_raw(
                            st.secrets["storage"]["dir"],
                            id,
                            input_df,
                            result_performance,
                            self.user_input[META_DATA],
                        )
        if SUBMIT in st.session_state:
            if st.session_state[SUBMIT]:
                # status_placeholder.success(":heavy_check_mark: Successfully uploaded data!")
                st.subheader("SUCCESS")
                st.markdown(
                    """
                    **It will take a few working days for your point to be added to the plot**
                    """
                )
                try:
                    st.write(f"Follow your submission approval here: [{pr_url}]({pr_url})")
                except UnboundLocalError:
                    # Happens when pr_url is not defined, e.g., local dev
                    pass

                st.session_state[SUBMIT] = False
                rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)
        FIRST_NEW_PLOT = False

    def plots_for_current_data(self, result_performance, recalculate, FIRST_NEW_PLOT, slider_value):
        # filter result_performance dataframe on nr_observed column
        result_performance = result_performance[result_performance["nr_observed"] >= slider_value]

        if recalculate:
            parse_settings = ParseSettings(self.user_input["input_format"])

            fig_logfc = PlotDataPoint.plot_fold_change_histogram(
                result_performance, parse_settings.species_expected_ratio
            )
            fig_CV = PlotDataPoint.plot_CV_violinplot(result_performance)
            st.session_state[FIG_CV] = fig_CV
            st.session_state[FIG_LOGFC] = fig_logfc
        else:
            fig_logfc = st.session_state[FIG_LOGFC]
            fig_CV = st.session_state[FIG_CV]

        if FIRST_NEW_PLOT:
            # Use st.beta_columns to arrange the figures side by side
            col1, col2 = st.columns(2)
            col1.subheader("Log2 Fold Change distributions by species.")
            col1.markdown(
                """
                    Left Panel : log2 fold changes calculated from your data
                """
            )
            col1.plotly_chart(fig_logfc, use_container_width=True)

            col2.subheader("Coefficient of variation distribution in Group A and B.")
            col2.markdown(
                """
                    Right Panel Panel : CV calculated from your data
                """
            )
            col2.plotly_chart(fig_CV, use_container_width=True)

        else:
            pass
        return fig_logfc


class WebpageTexts:
    class Sidebar:
        about = f"""
            """

    class Help:
        input_file = Path("pages/markdown_files/dda_quant_peptidoform/help_input.md").read_text()

        pull_req = """
            It is open to the public indefinitely.
            """

        input_format = Path("pages/markdown_files/dda_quant_peptidoform/help_implementedTools.md").read_text()

        parse_button = """
            Click here to see the output of your benchmark run
        """

        meta_data_file =  Path("pages/markdown_files/dda_quant_peptidoform/help_metadata.md").read_text()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()
