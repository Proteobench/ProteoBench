"""Streamlit-based web interface for ProteoBench."""

import json
import logging
import uuid
from datetime import datetime
from pprint import pformat
from typing import Any, Dict, Optional, Type

import pages.texts.proteobench_builder as pbb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_utils
from pages.pages_variables.dda_quant_variables import VariablesDDAQuant
from pages.texts.generic_texts import WebpageTexts
from streamlit_extras.let_it_rain import rain

from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.modules.dda_quant_ion.module import IonModule
from proteobench.utils.plotting.plot import PlotDataPoint
from proteobench.utils.quant_datapoint import (
    filter_df_numquant_median_abs_epsilon,
    filter_df_numquant_nr_prec,
)

logger: logging.Logger = logging.getLogger(__name__)

if "submission_ready" not in st.session_state:
    st.session_state["submission_ready"] = False


class StreamlitUI:
    """
    Main class for the Streamlit interface of ProteoBench DDA quantification for ions.

    This class manages the user interface, forms, and interactions within the ProteoBench application.
    It handles user input, processes data using the IonModule, and displays results.
    """

    def __init__(self):
        """Proteobench Streamlit UI."""
        self.variables_dda_quant: VariablesDDAQuant = VariablesDDAQuant()
        self.texts: Type[WebpageTexts] = WebpageTexts
        self.user_input: Dict[str, Any] = dict()

        pbb.proteobench_page_config()
        pbb.proteobench_sidebar()

        if self.variables_dda_quant.submit not in st.session_state:
            st.session_state[self.variables_dda_quant.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule: IonModule = IonModule(token=token)
        self._main_page()

    def generate_input_field(self, input_format: str, content: dict) -> Any:
        """
        Generates input fields in the Streamlit UI based on the specified format and content.

        Args:
            input_format: The format of the input (e.g., 'text_input', 'number_input').
            content: Dictionary containing the configuration for the input field.

        Returns:
            A Streamlit widget corresponding to the specified input type.
        """
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

    def _main_page(self) -> None:
        """
        Sets up the main page layout for the Streamlit application.
        This includes the title, module descriptions, input forms, and configuration settings.
        """
        st.title("DDA quantification - precursor ions")
        st.warning(
            "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
        )
        st.header("Description of the module")
        st.markdown(open("pages/markdown_files/DDA_Quant_ion/introduction.md", "r").read())
        st.header("Downloading associated files")
        st.markdown(open("pages/markdown_files/DDA_Quant_ion/file_description.md", "r").read(), unsafe_allow_html=True)
        st.header("Input and configuration")
        st.markdown(self.texts.ShortMessages.initial_results)

        with st.form(key="main_form"):
            st.subheader("Input files")
            st.markdown(open("pages/markdown_files/DDA_Quant_ion/input_file_description.md", "r").read())
            self.user_input["input_format"] = st.selectbox(
                "Software tool", ParseSettingsBuilder().INPUT_FORMATS, help=self.texts.Help.input_format
            )

            self.user_input["input_csv"] = st.file_uploader(
                "Software tool result file", help=self.texts.Help.input_file
            )

            st.markdown(self.texts.ShortMessages.initial_parameters)

            with st.expander("Additional parameters"):
                with open("../webinterface/configuration/dda_quant.json") as file:
                    config = json.load(file)

                for key, value in config.items():
                    self.user_input[key] = self.generate_input_field(self.user_input["input_format"], value)

            st.markdown(self.texts.ShortMessages.run_instructions)

            submit_button = st.form_submit_button("Parse and bench", help=self.texts.Help.parse_button)

        if submit_button:
            if self.user_input["input_csv"]:
                if self.variables_dda_quant.meta_file_uploader_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.meta_file_uploader_uuid]
                if self.variables_dda_quant.comments_submission_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.comments_submission_uuid]
                if self.variables_dda_quant.check_submission_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.check_submission_uuid]
                if self.variables_dda_quant.button_submission_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.button_submission_uuid]
                self._run_proteobench()
            else:
                st.error(":x: Please provide a result file", icon="🚨")

        if "slider_id" not in st.session_state.keys():
            st.session_state["slider_id"] = uuid.uuid4()
        if st.session_state["slider_id"] not in st.session_state.keys():
            st.session_state[st.session_state["slider_id"]] = self.variables_dda_quant.default_val_slider

        if self.variables_dda_quant.fig_logfc in st.session_state:
            self._populate_results()

        if (
            self.variables_dda_quant.all_datapoints not in st.session_state
            or self.variables_dda_quant.first_new_plot == True
        ):
            st.session_state[self.variables_dda_quant.all_datapoints] = None
            st.session_state[self.variables_dda_quant.all_datapoints] = self.ionmodule.obtain_all_data_point(
                st.session_state[self.variables_dda_quant.all_datapoints]
            )
            st.session_state[self.variables_dda_quant.all_datapoints] = self.ionmodule.filter_data_point(
                st.session_state[self.variables_dda_quant.all_datapoints],
                st.session_state[st.session_state["slider_id"]],
            )

            if (
                self.variables_dda_quant.highlight_list not in st.session_state.keys()
                and "Highlight" not in st.session_state[self.variables_dda_quant.all_datapoints].columns
            ):
                st.session_state[self.variables_dda_quant.all_datapoints].insert(
                    0, "Highlight", [False] * len(st.session_state[self.variables_dda_quant.all_datapoints].index)
                )
            elif "Highlight" not in st.session_state[self.variables_dda_quant.all_datapoints].columns:
                st.session_state[self.variables_dda_quant.all_datapoints].insert(
                    0, "Highlight", st.session_state[self.variables_dda_quant.highlight_list]
                )

            st.markdown(open("pages/markdown_files/DDA_Quant_ion/slider_description.md", "r").read())

            st.session_state[self.variables_dda_quant.placeholder_slider] = st.empty()
            st.session_state[self.variables_dda_quant.placeholder_fig_compare] = st.empty()
            st.session_state[self.variables_dda_quant.placeholder_table] = st.empty()
            st.session_state["table_id"] = uuid.uuid4()

            st.session_state[self.variables_dda_quant.placeholder_slider].select_slider(
                label="Minimal ion quantifications (# samples)",
                options=[1, 2, 3, 4, 5, 6],
                value=st.session_state[st.session_state["slider_id"]],
                on_change=self.slider_callback,
                key=st.session_state["slider_id"],
            )

            try:
                st.session_state[self.variables_dda_quant.fig_metric] = PlotDataPoint.plot_metric(
                    st.session_state[self.variables_dda_quant.all_datapoints]
                )
            except Exception as e:
                st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

            st.session_state[self.variables_dda_quant.placeholder_fig_compare].plotly_chart(
                st.session_state[self.variables_dda_quant.fig_metric], use_container_width=True
            )

            st.session_state[self.variables_dda_quant.placeholder_table].data_editor(
                st.session_state[self.variables_dda_quant.all_datapoints],
                key=st.session_state["table_id"],
                on_change=self.table_callback,
            )

    def _populate_results(self) -> None:
        """
        Populates the results section of the UI. This is called after data processing is complete.
        """
        self.generate_results("", None, None, False, None)

    def _run_proteobench(self) -> None:
        """
        Executes the ProteoBench benchmarking process. It handles the user's file submission,
        runs the benchmarking module, and updates the session state with the results.
        """
        st.header("Running Proteobench")
        status_placeholder = st.empty()
        status_placeholder.info(":hourglass_flowing_sand: Running Proteobench...")

        if self.variables_dda_quant.all_datapoints not in st.session_state:
            st.session_state[self.variables_dda_quant.all_datapoints] = None

        try:
            result_performance, all_datapoints, input_df = self.ionmodule.benchmarking(
                self.user_input["input_csv"],
                self.user_input["input_format"],
                self.user_input,
                st.session_state[self.variables_dda_quant.all_datapoints],
                default_cutoff_min_prec=st.session_state[st.session_state["slider_id"]],
            )

            st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints

            if "Highlight" not in st.session_state[self.variables_dda_quant.all_datapoints].columns:
                st.session_state[self.variables_dda_quant.all_datapoints].insert(
                    0, "Highlight", [False] * len(st.session_state[self.variables_dda_quant.all_datapoints].index)
                )
            else:
                st.session_state[self.variables_dda_quant.all_datapoints]["Highlight"] = [False] * len(
                    st.session_state[self.variables_dda_quant.all_datapoints].index
                )
        except Exception as e:
            status_placeholder.error(":x: Proteobench ran into a problem")
            st.error(e, icon="🚨")
        else:
            self.generate_results(status_placeholder, result_performance, all_datapoints, True, input_df)

    def table_callback(self) -> None:
        """
        Callback function for handling edits made to the data table in the UI.
        It updates the session state to reflect changes made to the data points.
        """
        min_quant = st.session_state[st.session_state["slider_id"]]
        edits = st.session_state[st.session_state["table_id"]]["edited_rows"].items()
        for k, v in edits:
            try:
                st.session_state[self.variables_dda_quant.all_datapoints][list(v.keys())[0]].iloc[k] = list(v.values())[
                    0
                ]
            except TypeError:
                return
        st.session_state[self.variables_dda_quant.highlight_list] = list(
            st.session_state[self.variables_dda_quant.all_datapoints]["Highlight"]
        )
        st.session_state[self.variables_dda_quant.placeholder_table] = st.session_state[
            self.variables_dda_quant.all_datapoints
        ]

        try:
            fig_metric = PlotDataPoint.plot_metric(st.session_state[self.variables_dda_quant.all_datapoints])
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_dda_quant.fig_metric] = fig_metric

        if self.variables_dda_quant.result_perf in st.session_state.keys():
            self.plots_for_current_data(True)

    def slider_callback(self) -> None:
        """
        Callback function for the slider input. It adjusts the data points displayed based on
        the selected slider value, such as the minimum number of ion quantifications.
        """
        st.session_state[self.variables_dda_quant.all_datapoints] = self.ionmodule.filter_data_point(
            st.session_state[self.variables_dda_quant.all_datapoints], st.session_state[st.session_state["slider_id"]]
        )

        try:
            fig_metric = PlotDataPoint.plot_metric(st.session_state[self.variables_dda_quant.all_datapoints])
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_dda_quant.fig_metric] = fig_metric

        if self.variables_dda_quant.result_perf in st.session_state.keys():
            self.plots_for_current_data(True)

    def make_submission_webinterface(self, params) -> Optional[str]:
        """
        Handles the submission process of the benchmark results to the ProteoBench repository.

        Args:
            params: Parameters used for the benchmarking.
            input_df: The input DataFrame.
            result_performance: DataFrame containing the performance results.

        Returns:
            The URL of the submission if successful, None otherwise.
        """
        st.session_state["submission_ready"] = True
        pr_url = None

        if self.variables_dda_quant.button_submission_uuid in st.session_state.keys():
            button_submission_uuid = st.session_state[self.variables_dda_quant.button_submission_uuid]
        else:
            button_submission_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.button_submission_uuid] = button_submission_uuid
        submit_pr = st.button("I really want to upload it", key=button_submission_uuid)

        if submit_pr:
            st.session_state[self.variables_dda_quant.submit] = True
            user_comments = self.user_input["comments_for_submission"]

            # TODO I have written a copy to a different variable as it is reset when meta data file is uploaded
            # TODO this needs to change in the future!
            submit_df = st.session_state[self.variables_dda_quant.all_datapoints_submission]
            input_df = st.session_state[self.variables_dda_quant.input_df_submission]
            result_performance = st.session_state[self.variables_dda_quant.result_performance_submission]

            if "Highlight" in submit_df.columns:
                submit_df.drop("Highlight", inplace=True, axis=1)

            try:
                pr_url = self.ionmodule.clone_pr(
                    temporary_datapoints=submit_df,
                    datapoint_params=params,
                    remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
                    submission_comments=user_comments,
                )
            except Exception as e:
                st.error(f"Unable to create the pull request: {e}", icon="🚨")

            if not pr_url:
                del st.session_state[self.variables_dda_quant.submit]
            else:
                id = str(
                    st.session_state[self.variables_dda_quant.all_datapoints_submission][
                        st.session_state[self.variables_dda_quant.all_datapoints_submission]["old_new"] == "new"
                    ].iloc[-1, :]["intermediate_hash"]
                )

                if "storage" in st.secrets.keys():
                    self.ionmodule.write_intermediate_raw(
                        st.secrets["storage"]["dir"],
                        id,
                        input_df,
                        result_performance,
                        self.user_input[self.variables_dda_quant.meta_data],
                    )

        return pr_url

    def successful_submission(self, pr_url) -> None:
        """
        Handles the UI updates and notifications after a successful submission of benchmark results.

        Args:
            pr_url: The URL of the submitted pull request.
        """
        if st.session_state[self.variables_dda_quant.submit]:
            # status_placeholder.success(":heavy_check_mark: Successfully uploaded data!")
            st.subheader("SUCCESS")
            st.markdown(self.texts.ShortMessages.submission_processing_warning)
            try:
                st.write(f"Follow your submission approval here: [{pr_url}]({pr_url})")
            except UnboundLocalError:
                # Happens when pr_url is not defined, e.g., local dev
                pass

            st.session_state[self.variables_dda_quant.submit] = False
            rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)

    def read_parameters(self) -> Any:
        """
        Reads and processes the parameter files provided by the user.

        Returns:
            The parameters read from the file, or None if there's an error.
        """
        params = None

        try:
            params = self.ionmodule.load_params_file(
                self.user_input[self.variables_dda_quant.meta_data], self.user_input["input_format"]
            )
            st.text(f"Parsed and selected parameters:\n{pformat(params.__dict__)}")
        except KeyError as e:
            st.error("Parsing of meta parameters file for this software is not supported yet.", icon="🚨")
        except Exception as e:
            input_f = self.user_input["input_format"]
            st.error(
                f"Unexpected error while parsing file. Make sure you provided a meta parameters file produced by {input_f}: {e}",
                icon="🚨",
            )
        return params

    def create_submission_elements(self) -> None:
        """
        Creates the UI elements necessary for data submission, including metadata uploader and comments section.
        """
        # TODO I have to write a copy to a different variable as it is reset when meta data file is uploaded
        # TODO this needs to change in the future!
        if st.session_state[self.variables_dda_quant.all_datapoints] is not None:
            st.session_state[self.variables_dda_quant.all_datapoints_submission] = st.session_state[
                self.variables_dda_quant.all_datapoints
            ].copy()
        if st.session_state[self.variables_dda_quant.input_df] is not None:
            st.session_state[self.variables_dda_quant.input_df_submission] = st.session_state[
                self.variables_dda_quant.input_df
            ].copy()
        if st.session_state[self.variables_dda_quant.result_perf] is not None:
            st.session_state[self.variables_dda_quant.result_performance_submission] = st.session_state[
                self.variables_dda_quant.result_perf
            ].copy()

        self.user_input[self.variables_dda_quant.meta_data] = st.file_uploader(
            "Meta data for searches",
            help=self.texts.Help.meta_data_file,
            key="meta_data_fileuploader",  # self.variables_dda_quant.meta_file_uploader_uuid,
            accept_multiple_files=True,
        )

        self.user_input["comments_for_submission"] = st.text_area(
            "Comments for submission",
            placeholder=self.texts.ShortMessages.parameters_additional,
            height=200,
            # key=self.variables_dda_quant.comments_submission_uuid,
        )

        st.session_state[self.variables_dda_quant.meta_data_text] = self.user_input["comments_for_submission"]

        st.session_state[self.variables_dda_quant.check_submission] = st.checkbox(
            "I confirm that the metadata is correct",
            # key=self.variables_dda_quant.check_submission_uuid,
        )

    def create_sample_name(self) -> str:
        """
        Generates a unique sample name based on the input format, software version, and the current timestamp.

        Returns:
            A string representing the generated sample name.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_name = "%s-%s-%s-%s" % (
            self.user_input["input_format"],
            self.user_input["software_version"],
            self.user_input["enable_match_between_runs"],
            time_stamp,
        )

        return sample_name

    def create_first_new_plot(self) -> None:
        """
        Generates and displays the initial plots and data tables based on the benchmark results.
        This includes setting up UI elements for displaying these results.
        """
        st.header("Results")
        st.subheader("Sample of the processed file")
        st.markdown(open("pages/markdown_files/DDA_Quant_ion/table_description.md", "r").read())
        st.session_state[self.variables_dda_quant.df_head] = st.dataframe(
            st.session_state[self.variables_dda_quant.result_perf].head(100)
        )

        st.markdown(st.markdown(open("pages/markdown_files/DDA_Quant_ion/result_description.md", "r").read()))

        st.subheader("Mean error between conditions")
        st.markdown(self.texts.ShortMessages.submission_result_description)

        sample_name = self.create_sample_name()

        st.markdown(open("pages/markdown_files/DDA_Quant_ion/slider_description.md", "r").read())
        # st.session_state["slider_id"] = uuid.uuid4()
        f = st.select_slider(
            label="Minimal ion quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state[st.session_state["slider_id"]],
            on_change=self.slider_callback,
            key=st.session_state["slider_id"],
        )

        st.session_state[self.variables_dda_quant.all_datapoints] = self.ionmodule.filter_data_point(
            st.session_state[self.variables_dda_quant.all_datapoints], st.session_state[st.session_state["slider_id"]]
        )

        try:
            st.session_state[self.variables_dda_quant.fig_metric] = PlotDataPoint.plot_metric(
                st.session_state[self.variables_dda_quant.all_datapoints]
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        placeholder_fig_compare = st.empty()
        placeholder_fig_compare.plotly_chart(
            st.session_state[self.variables_dda_quant.fig_metric], use_container_width=True
        )
        st.session_state[self.variables_dda_quant.placeholder_fig_compare] = placeholder_fig_compare

        st.session_state["table_id"] = uuid.uuid4()

        st.data_editor(
            st.session_state[self.variables_dda_quant.all_datapoints],
            key=st.session_state["table_id"],
            on_change=self.table_callback,
        )

        st.subheader("Download calculated ratios")
        random_uuid = uuid.uuid4()
        st.download_button(
            label="Download",
            data=streamlit_utils.save_dataframe(st.session_state[self.variables_dda_quant.result_perf]),
            file_name=f"{sample_name}.csv",
            mime="text/csv",
            key=f"{random_uuid}",
        )

        st.subheader("Add results to online repository")
        st.markdown(open("pages/markdown_files/DDA_Quant_ion/submit_description.md", "r").read())

    def call_later_plot(self) -> None:
        """
        Updates the plot data and UI elements after re-running the benchmark with new parameters or data.
        """
        fig_metric = st.session_state[self.variables_dda_quant.fig_metric]
        st.session_state[self.variables_dda_quant.fig_metric].data[0].x = fig_metric.data[0].x
        st.session_state[self.variables_dda_quant.fig_metric].data[0].y = fig_metric.data[0].y

        st.session_state[self.variables_dda_quant.placeholder_fig_compare].plotly_chart(
            st.session_state[self.variables_dda_quant.fig_metric], use_container_width=True
        )

    def generate_results(
        self,
        status_placeholder: Any,
        result_performance: pd.DataFrame,
        all_datapoints: pd.DataFrame,
        recalculate: bool,
        input_df: pd.DataFrame,
    ) -> None:
        """
        Generates and displays the final results of the benchmark process. It updates the UI with plots,
        data tables, and other elements based on the benchmark results.

        Args:
            status_placeholder: UI element for displaying the processing status.
            result_performance: DataFrame with performance results.
            all_datapoints: DataFrame with all data points.
            recalculate: Boolean indicating whether the results need to be recalculated.
            input_df: DataFrame of the input data.
        """
        if recalculate:
            status_placeholder.success(":heavy_check_mark: Finished!")
            st.session_state[self.variables_dda_quant.result_perf] = result_performance
            st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints
            st.session_state[self.variables_dda_quant.input_df] = input_df
        if not self.variables_dda_quant.first_new_plot:
            st.session_state[self.variables_dda_quant.df_head] = st.session_state[
                self.variables_dda_quant.result_perf
            ].head(100)

        st.session_state[self.variables_dda_quant.fig_logfc] = self.plots_for_current_data(recalculate)

        if recalculate:
            try:
                st.session_state[self.variables_dda_quant.fig_metric] = PlotDataPoint.plot_metric(
                    st.session_state[self.variables_dda_quant.all_datapoints]
                )
            except Exception as e:
                st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        if self.variables_dda_quant.first_new_plot:
            self.create_first_new_plot()
        else:
            self.call_later_plot()

        if all_datapoints is not None:
            # TODO do we need add this to the session state?
            st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints
            st.session_state[self.variables_dda_quant.input_df] = input_df

        # Create unique element IDs
        if self.variables_dda_quant.meta_file_uploader_uuid not in st.session_state.keys():
            meta_file_uploader_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.meta_file_uploader_uuid] = meta_file_uploader_uuid
        if self.variables_dda_quant.comments_submission_uuid not in st.session_state.keys():
            comments_submission_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.comments_submission_uuid] = comments_submission_uuid
        if self.variables_dda_quant.check_submission_uuid not in st.session_state.keys():
            check_submission_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.check_submission_uuid] = check_submission_uuid

        if self.variables_dda_quant.first_new_plot:
            self.create_submission_elements()
        if self.user_input[self.variables_dda_quant.meta_data]:
            params = self.read_parameters()
        if st.session_state[self.variables_dda_quant.check_submission] and params != None:
            pr_url = self.make_submission_webinterface(params)
        if (
            st.session_state[self.variables_dda_quant.check_submission]
            and params != None
            and self.variables_dda_quant.submit in st.session_state
        ):
            self.successful_submission(pr_url)
        self.variables_dda_quant.first_new_plot = False

    def plots_for_current_data(self, recalculate: bool) -> go.Figure:
        """
        Generates and returns plots based on the current benchmark data.

        Args:
            recalculate: Boolean to determine if the plot needs to be recalculated.

        Returns:
            A Plotly graph object containing the generated plot.
        """

        # filter result_performance dataframe on nr_observed column
        st.session_state[self.variables_dda_quant.result_perf] = st.session_state[self.variables_dda_quant.result_perf][
            st.session_state[self.variables_dda_quant.result_perf]["nr_observed"]
            >= st.session_state[st.session_state["slider_id"]]
        ]

        if recalculate:
            parse_settings = ParseSettingsBuilder().build_parser(self.user_input["input_format"])

            fig_logfc = PlotDataPoint.plot_fold_change_histogram(
                st.session_state[self.variables_dda_quant.result_perf], parse_settings.species_expected_ratio()
            )
            fig_CV = PlotDataPoint.plot_CV_violinplot(st.session_state[self.variables_dda_quant.result_perf])
            st.session_state[self.variables_dda_quant.fig_cv] = fig_CV
            st.session_state[self.variables_dda_quant.fig_logfc] = fig_logfc
        else:
            fig_logfc = st.session_state[self.variables_dda_quant.fig_logfc]
            fig_CV = st.session_state[self.variables_dda_quant.fig_cv]

        if self.variables_dda_quant.first_new_plot:
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


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()
