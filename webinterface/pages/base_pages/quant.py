"""Streamlit-based web interface for ProteoBench."""

import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from pprint import pformat
from typing import Any, Dict, Optional

import pages.texts.proteobench_builder as pbb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_utils
from pages.pages_variables.dda_quant_variables import VariablesDDAQuant
from streamlit_extras.let_it_rain import rain

from proteobench.io.parsing.parse_settings_ion import ParseSettingsBuilder
from proteobench.modules.dda_quant_ion.dda_quant_ion_module import (
    DDAQuantIonModule as IonModule,
)
from proteobench.plotting.plot_quant import PlotDataPoint

logger: logging.Logger = logging.getLogger(__name__)


class QuantUIObjects:
    """
    Main class for the Streamlit interface of ProteoBench quantification.

    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.
    """

    def __init__(
        self, variables_quant: VariablesDDAQuant, ionmodule: IonModule, parsesettingsbuilder: ParseSettingsBuilder
    ) -> None:
        """Initializes the Streamlit UI objects for the quantification modules."""
        # Assign instances of objects to class variables

        # Variables for dda quant specify var names and locations of texts, such as markdown files
        self.variables_quant: VariablesDDAQuant = variables_quant

        # IonModule is the main module for the quantification process (calculations, parsing, etc.)
        self.ionmodule: IonModule = ionmodule

        # ParseSettingsBuilder is used to build the parser settings for the input,
        # mainly used to get possible parsing options for the input file
        self.parsesettingsbuilder: ParseSettingsBuilder = parsesettingsbuilder

        # Initialize a dictionary to store user input
        self.user_input: Dict[str, Any] = dict()

        # Create page config and sidebar
        pbb.proteobench_page_config()
        pbb.proteobench_sidebar()

        self.first_point_plotted = False
        st.session_state[self.variables_quant.submit] = False
        self.stop_duplicating = False

        # Make sure when initialized the submission is False
        if self.variables_quant.submit not in st.session_state:
            st.session_state[self.variables_quant.submit] = False
            self.first_point_plotted = False

    def create_main_submission_form(self) -> None:
        """
        Creates the main submission form for the Streamlit UI.
        This includes the input file uploader, additional parameters, and the main submission button.
        """
        with st.form(key="main_form"):
            self._create_input_section()
            self._create_additional_parameters_section()
            st.markdown(self.variables_quant.texts.ShortMessages.run_instructions)
            submit_button = st.form_submit_button("Parse and bench", help=self.variables_quant.texts.Help.parse_button)

        if submit_button:
            self._handle_form_submission()

    def generate_input_field(self, input_format: str, content: dict) -> Any:
        """
        Generates input fields in the Streamlit UI based on the specified format and content.

        Args:
            input_format: The format of the input (e.g., 'text_input', 'number_input').
            content: Dictionary containing the configuration for the input field.

        Returns:
            A Streamlit widget corresponding to the specified input type.
        """
        field_type = content.get("type")
        if field_type == "text_area":
            return self._generate_text_area(input_format, content)
        elif field_type == "text_input":
            return self._generate_text_input(input_format, content)
        elif field_type == "number_input":
            return self._generate_number_input(content)
        elif field_type == "selectbox":
            return self._generate_selectbox(input_format, content)
        elif field_type == "checkbox":
            return self._generate_checkbox(input_format, content)

    def init_slider(self) -> None:
        ##########################################
        # Initialize slider ID and default value #
        ##########################################
        if "slider_id" not in st.session_state.keys():
            st.session_state["slider_id"] = uuid.uuid4()
        if st.session_state["slider_id"] not in st.session_state.keys():
            st.session_state[st.session_state["slider_id"]] = self.variables_quant.default_val_slider

    def create_selectbox(self) -> None:
        """Creates the selectbox for the Streamlit UI."""
        if self.variables_quant.selectbox_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.selectbox_id_uuid] = uuid.uuid4()

        try:
            st.selectbox(
                "Select label to plot",
                ["None", "precursor_mass_tolerance", "fragment_mass_tolerance"],
                key=st.session_state[self.variables_quant.selectbox_id_uuid],
            )
        except Exception as e:
            st.error(f"Unable to create the selectbox: {e}", icon="🚨")

    def create_selectbox_submitted(self) -> None:
        """Creates the selectbox for the Streamlit UI."""
        if self.variables_quant.selectbox_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.selectbox_id_submitted_uuid] = uuid.uuid4()

        try:
            st.selectbox(
                "Select label to plot",
                ["None", "precursor_mass_tolerance", "fragment_mass_tolerance"],
                key=st.session_state[self.variables_quant.selectbox_id_submitted_uuid],
            )
        except Exception as e:
            st.error(f"Unable to create the selectbox: {e}", icon="🚨")

    def init_slider_submitted(self) -> None:
        ##########################################
        # Initialize slider ID and default value #
        ##########################################
        if "slider_id_submitted" not in st.session_state.keys():
            st.session_state["slider_id_submitted"] = uuid.uuid4()
        if st.session_state["slider_id_submitted"] not in st.session_state.keys():
            st.session_state[st.session_state["slider_id_submitted"]] = self.variables_quant.default_val_slider

    def create_results_submitted(self) -> None:
        """
        Creates the results section of the page.

        Args:
            show_new_submissions: If True, only display new submissions.
        """
        handled_submission = self._handle_form_submission()
        if handled_submission == False:
            return

        # Fetch the appropriate data
        self._initialize_all_datapoints_submitted()

        # Filter data based on slider
        data_points_filtered = self._filter_data_points_by_slider_submitted()

        # Plot
        try:
            fig_metric = PlotDataPoint.plot_metric(
                data_points_filtered,
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_submitted_uuid]],
            )
            st.plotly_chart(fig_metric, use_container_width=True)
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state["table_id"] = uuid.uuid4()
        # Data Table
        st.data_editor(
            st.session_state[self.variables_quant.all_datapoints_submitted],
            key=st.session_state["table_id"],
            on_change=self.table_callback_submitted,
        )

    def create_results_existing(self) -> None:
        """
        Creates the results section of the page.

        Args:
            show_new_submissions: If True, only display new submissions.
        """
        # Fetch the appropriate data
        self._initialize_all_datapoints()

        # Filter data based on slider
        data_points_filtered = self._filter_data_points_by_slider()

        # Plot
        try:
            fig_metric = PlotDataPoint.plot_metric(
                data_points_filtered, label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]]
            )
            st.plotly_chart(fig_metric, use_container_width=True)
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        # Data Table
        st.dataframe(data_points_filtered)

        self.render_download_container()

    def create_text_header(self) -> None:
        """
        Creates the text header for the main page of the Streamlit UI. This includes the title,
        module description, input and configuration description.
        """
        st.title(self.variables_quant.texts.ShortMessages.title)
        if self.variables_quant.beta_warning:
            st.warning(
                "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
            )

        st.header("Description of the module")
        st.markdown(open(self.variables_quant.description_module_md, "r").read())
        st.header("Downloading associated files")
        st.markdown(open(self.variables_quant.description_files_md, "r").read(), unsafe_allow_html=True)

    def populate_results(self) -> None:
        """
        Populates the results section of the UI. This is called after data processing is complete.
        """
        self.generate_results("", None, None, False, None)

    def make_submission_webinterface(self, params) -> Optional[str]:
        """
        Handles the submission process of the benchmark results to the ProteoBench repository.

        Args:
            params: Parameters used for the benchmarking.

        Returns:
            The URL of the submission if successful, None otherwise.
        """
        st.session_state[self.variables_quant.submit] = True
        pr_url = self._create_submission_button()

        if not pr_url:
            return None

        self._remove_highlight_column()
        pr_url = self._submit_pull_request(params, pr_url)

        if pr_url:
            self._store_intermediate_data(pr_url)

        return pr_url

    def successful_submission(self, pr_url) -> None:
        """
        Handles the UI updates and notifications after a successful submission of benchmark results.

        Args:
            pr_url: The URL of the submitted pull request.
        """
        if st.session_state[self.variables_quant.submit]:
            st.subheader("SUCCESS")
            st.markdown(self.variables_quant.texts.ShortMessages.submission_processing_warning)
            try:
                st.write(f"Follow your submission approval here: [{pr_url}]({pr_url})")
            except UnboundLocalError:
                # Happens when pr_url is not defined, e.g., local dev
                pass

            st.session_state[self.variables_quant.submit] = False
            rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)

    def create_submission_elements(self) -> None:
        """
        Creates the UI elements necessary for data submission, including metadata uploader and comments section.
        """
        try:
            self._create_dataframe_copies()
            self.submission_ready = True
        except:
            self.submission_ready = False
            st.error(":x: Please provide a result file", icon="🚨")
        self._create_meta_data_uploader()
        self._create_comments_text_area()
        self._create_confirmation_checkbox()

    def _create_input_section(self) -> None:
        """Creates the input section of the form."""
        st.subheader("Input files")
        st.markdown(open(self.variables_quant.description_input_file_md, "r").read())
        self.user_input["input_format"] = st.selectbox(
            "Software tool",
            self.parsesettingsbuilder.INPUT_FORMATS,
            help=self.variables_quant.texts.Help.input_format,
        )
        self.user_input["input_csv"] = st.file_uploader(
            "Software tool result file", help=self.variables_quant.texts.Help.input_file
        )

    def _create_additional_parameters_section(self) -> None:
        """Creates the additional parameters section of the form and initialize the paramter fields."""
        st.markdown(self.variables_quant.texts.ShortMessages.initial_parameters)
        with open(self.variables_quant.additional_params_json) as file:
            config = json.load(file)
        for key, value in config.items():
            if key == "comments_for_plotting":
                self.user_input[key] = self.generate_input_field(self.user_input["input_format"], value)
            else:
                self.user_input[key] = None

    def _handle_form_submission(self) -> None:
        """Handles the form submission logic."""
        if not self.user_input["input_csv"]:
            st.error(":x: Please provide a result file", icon="🚨")
            return False
        # self._reset_session_state_variables()
        self._run_proteobench()
        self.first_point_plotted = True

    def _reset_session_state_variables(self) -> None:
        """Resets specific session state variables."""
        session_keys = [
            self.variables_quant.meta_file_uploader_uuid,
            self.variables_quant.comments_submission_uuid,
            self.variables_quant.check_submission_uuid,
            self.variables_quant.button_submission_uuid,
        ]
        for key in session_keys:
            if key in st.session_state:
                del st.session_state[key]

    def _generate_text_area(self, input_format: str, content: dict) -> Any:
        """Generates a text area input field."""
        placeholder = content.get("placeholder")
        value = content.get("value", {}).get(input_format)
        height = content.get("height", 200)  # Default height if not specified
        return st.text_area(content["label"], placeholder=placeholder, value=value, height=height)

    def _generate_text_input(self, input_format: str, content: dict) -> Any:
        """Generates a text input field."""
        placeholder = content.get("placeholder")
        value = content.get("value", {}).get(input_format)
        return st.text_input(content["label"], placeholder=placeholder, value=value)

    def _generate_number_input(self, content: dict) -> Any:
        """Generates a number input field."""
        return st.number_input(
            content["label"],
            value=None,
            format=content["format"],
            min_value=content["min_value"],
            max_value=content["max_value"],
        )

    def _generate_selectbox(self, input_format: str, content: dict) -> Any:
        """Generates a selectbox input field."""
        options = content.get("options", [])
        value = content.get("value", {}).get(input_format)
        index = options.index(value) if value in options else 0
        return st.selectbox(content["label"], options, index=index)

    def _generate_checkbox(self, input_format: str, content: dict) -> Any:
        """Generates a checkbox input field."""
        value = content.get("value", {}).get(input_format, False)
        return st.checkbox(content["label"], value=value)

    def _results_already_initialized(self) -> bool:
        """Checks if the results are already initialized."""
        return self.variables_quant.all_datapoints in st.session_state or self.variables_quant.first_new_plot == False

    def _initialize_all_datapoints(self) -> None:
        """Initializes the all_datapoints variable in the session state."""
        if self.variables_quant.all_datapoints not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints] = None
            st.session_state[self.variables_quant.all_datapoints] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints]
            )

    def _initialize_all_datapoints_submitted(self) -> None:
        """Initializes the all_datapoints variable in the session state."""
        if self.variables_quant.all_datapoints_submitted not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints_submitted] = None
            st.session_state[self.variables_quant.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints_submitted]
            )

    def _filter_data_points_by_slider(self) -> None:
        """Filters the data points based on the slider value."""
        if "slider_id" in st.session_state.keys():
            return self.ionmodule.filter_data_point(
                st.session_state[self.variables_quant.all_datapoints],
                st.session_state[st.session_state["slider_id"]],
            )

    def _filter_data_points_by_slider_submitted(self) -> None:
        """Filters the data points based on the slider value."""
        if (
            "slider_id_submitted" in st.session_state.keys()
            and self.variables_quant.all_datapoints_submitted in st.session_state.keys()
        ):
            return self.ionmodule.filter_data_point(
                st.session_state[self.variables_quant.all_datapoints_submitted],
                st.session_state[st.session_state["slider_id_submitted"]],
            )

    def _initialize_highlight_column(self) -> None:
        """Initializes the highlight column in the data points."""
        if (
            self.variables_quant.highlight_list not in st.session_state.keys()
            and "Highlight" not in st.session_state[self.variables_quant.all_datapoints].columns
        ):
            st.session_state[self.variables_quant.all_datapoints].insert(
                0, "Highlight", [False] * len(st.session_state[self.variables_quant.all_datapoints].index)
            )
        elif "Highlight" not in st.session_state[self.variables_quant.all_datapoints].columns:
            st.session_state[self.variables_quant.all_datapoints].insert(
                0, "Highlight", st.session_state[self.variables_quant.highlight_list]
            )

    def _initialize_highlight_column_submitted(self) -> None:
        """Initializes the highlight column in the data points."""
        if (
            self.variables_quant.highlight_list_submitted not in st.session_state.keys()
            and "Highlight" not in st.session_state[self.variables_quant.all_datapoints_submitted].columns
        ):
            st.session_state[self.variables_quant.all_datapoints_submitted].insert(
                0, "Highlight", [False] * len(st.session_state[self.variables_quant.all_datapoints_submitted].index)
            )
        elif "Highlight" not in st.session_state[self.variables_quant.all_datapoints_submitted].columns:
            st.session_state[self.variables_quant.all_datapoints_submitted].insert(
                0, "Highlight", st.session_state[self.variables_quant.highlight_list_submitted]
            )

    def _create_slider(self) -> None:
        """Creates a slider input."""
        if "slider_id" not in st.session_state:
            st.session_state["slider_id"] = uuid.uuid4()
        slider_key = st.session_state["slider_id"]

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal ion quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state.get(slider_key, self.variables_quant.default_val_slider),
            key=slider_key,
        )

    def _create_slider_submitted(self) -> None:
        """Creates a slider input."""
        if "slider_id_submitted" not in st.session_state:
            st.session_state["slider_id_submitted"] = uuid.uuid4()
        slider_key = st.session_state["slider_id_submitted"]
        # st.session_state[slider_key] = st.empty()

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal ion quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state.get(slider_key, self.variables_quant.default_val_slider),
            key=slider_key,
        )

    def _initialize_placeholders(self) -> None:
        """Initializes the placeholders for the figure and table."""
        st.session_state[self.variables_quant.placeholder_fig_compare] = st.empty()
        st.session_state[self.variables_quant.placeholder_table] = st.empty()
        st.session_state[self.variables_quant.placeholder_downloads_container] = st.empty()
        st.session_state["table_id"] = uuid.uuid4()

    def _generate_and_display_metric_plot(self) -> None:
        """Generates and displays the metric plot."""
        try:
            st.session_state[self.variables_quant.fig_metric] = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
        st.session_state[self.variables_quant.placeholder_fig_compare].plotly_chart(
            st.session_state[self.variables_quant.fig_metric], use_container_width=True
        )

    def _initialize_data_editor(self) -> None:
        """Initializes the data editor."""
        try:
            st.session_state[self.variables_quant.placeholder_table].data_editor(
                st.session_state[self.variables_quant.all_datapoints],
                key=st.session_state["table_id"],
                on_change=self.table_callback,
            )
        except:
            self.stop_duplicating = True

    def render_download_container(self, reset_uuid=False) -> None:
        """Render the selector and ares for raw data download"""

        # create a dataframe for dataset selection from the submitted datasets
        downloads_df = st.session_state[self.variables_quant.all_datapoints][["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        # create a uuid for the selector (if necessary)
        if self.variables_quant.placeholder_downloads_container not in st.session_state.keys() or reset_uuid:
            st.session_state[self.variables_quant.placeholder_downloads_container] = st.empty()
            st.session_state["download_selector_id"] = uuid.uuid4()

        with st.session_state[self.variables_quant.placeholder_downloads_container].container(border=True):
            # render everything into the "download"-container
            st.subheader("Download raw datasets")

            st.selectbox(
                "Select dataset",
                downloads_df["intermediate_hash"],
                index=None,
                key=st.session_state["download_selector_id"],
                format_func=lambda x: downloads_df["id"][x],
            )

            if (
                st.session_state[st.session_state["download_selector_id"]] != None
                and st.secrets["storage"]["dir"] != None
            ):
                # if some dataset is already selected, render the download buttons
                st.write(
                    "Available files for "
                    + downloads_df["id"][st.session_state[st.session_state["download_selector_id"]]]
                    + ":"
                )

                dataset_path = (
                    st.secrets["storage"]["dir"] + "/" + st.session_state[st.session_state["download_selector_id"]]
                )
                if os.path.isdir(dataset_path):
                    files = os.listdir(dataset_path)
                    for file_name in files:
                        path_to_file = dataset_path + "/" + file_name
                        with open(path_to_file, "rb") as file:
                            st.download_button(file_name, file, file_name=file_name)
                else:
                    st.write("Directory for this dataset does not exist, this should not happen.")

    def _create_submission_button(self) -> Optional[str]:
        """Creates a button for public submission and returns the PR URL if the button is pressed."""
        if self.variables_quant.button_submission_uuid not in st.session_state.keys():
            button_submission_uuid = uuid.uuid4()
            st.session_state[self.variables_quant.button_submission_uuid] = button_submission_uuid

        submit_pr = st.button(
            "I really want to upload it", key=st.session_state[self.variables_quant.button_submission_uuid]
        )
        if not submit_pr:
            return None

        return "button_pressed"

    def _remove_highlight_column(self) -> None:
        """Removes the highlight column from the submission data if it exists."""
        if "Highlight" in st.session_state[self.variables_quant.all_datapoints_submission].columns:
            st.session_state[self.variables_quant.all_datapoints_submission].drop("Highlight", inplace=True, axis=1)

    def _submit_pull_request(self, params: Any, pr_url: str) -> Optional[str]:
        """Submits the pull request with the benchmark results and returns the PR URL."""
        user_comments = self.user_input["comments_for_submission"]

        try:
            pr_url = self.ionmodule.clone_pr(
                st.session_state[self.variables_quant.all_datapoints_submission],
                params,
                remote_git=self.variables_quant.github_link_pr,
                submission_comments=user_comments,
            )
        except Exception as e:
            st.error(f"Unable to create the pull request: {e}", icon="🚨")
            pr_url = None

        if not pr_url:
            del st.session_state[self.variables_quant.submit]

        return pr_url

    def _store_intermediate_data(self, pr_url: str) -> None:
        """Stores intermediate and input data to the storage directory if available."""
        id = str(
            st.session_state[self.variables_quant.all_datapoints_submission][
                st.session_state[self.variables_quant.all_datapoints_submission]["old_new"] == "new"
            ].iloc[-1, :]["intermediate_hash"]
        )

        if "storage" in st.secrets.keys():
            self.ionmodule.write_intermediate_raw(
                st.secrets["storage"]["dir"],
                id,
                st.session_state[self.variables_quant.input_df_submission],
                st.session_state[self.variables_quant.result_performance_submission],
                self.user_input[self.variables_quant.meta_data],
            )

    def _create_dataframe_copies(self) -> None:
        """Creates copies of the dataframes before submission."""
        if st.session_state[self.variables_quant.all_datapoints_submitted] is not None:
            st.session_state[self.variables_quant.all_datapoints_submission] = st.session_state[
                self.variables_quant.all_datapoints_submitted
            ].copy()
        if st.session_state[self.variables_quant.input_df] is not None:
            st.session_state[self.variables_quant.input_df_submission] = st.session_state[
                self.variables_quant.input_df
            ].copy()
        if st.session_state[self.variables_quant.result_perf] is not None:
            st.session_state[self.variables_quant.result_performance_submission] = st.session_state[
                self.variables_quant.result_perf
            ].copy()

    def _create_meta_data_uploader(self) -> None:
        """Creates the file uploader for meta data."""
        self.user_input[self.variables_quant.meta_data] = st.file_uploader(
            "Meta data for searches",
            help=self.variables_quant.texts.Help.meta_data_file,
            # key=self.variables_quant.meta_file_uploader_uuid,
            accept_multiple_files=True,
        )

    def _create_comments_text_area(self) -> None:
        """Creates the text area for submission comments."""
        self.user_input["comments_for_submission"] = st.text_area(
            "Comments for submission",
            placeholder=self.variables_quant.texts.ShortMessages.parameters_additional,
            height=200,
        )
        st.session_state[self.variables_quant.meta_data_text] = self.user_input["comments_for_submission"]

    def _create_confirmation_checkbox(self) -> None:
        """Creates the confirmation checkbox for metadata correctness."""
        st.session_state[self.variables_quant.check_submission] = st.checkbox(
            "I confirm that the metadata is correct",
        )
        self.stop_duplicating = True

    def _run_proteobench(self) -> None:
        """
        Executes the ProteoBench benchmarking process. It handles the user's file submission,
        runs the benchmarking module, and updates the session state with the results.
        """
        # st.header("Running Proteobench")

        # status_placeholder = st.empty()
        # status_placeholder.info(":hourglass_flowing_sand: Running Proteobench...")

        if self.variables_quant.all_datapoints_submitted not in st.session_state:
            self._initialize_all_datapoints()

        result_performance, all_datapoints, input_df = self._execute_benchmarking()
        st.session_state[self.variables_quant.all_datapoints_submitted] = all_datapoints

        self._initialize_highlight_column_submitted()

        st.session_state[self.variables_quant.result_perf] = result_performance

        st.session_state[self.variables_quant.input_df] = input_df

    def _execute_benchmarking(self):
        """Executes the benchmarking process and returns the results."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(self.user_input["input_csv"].getbuffer())
            temp_file_name = tmp_file.name
        f = open(temp_file_name)
        f.seek(0)

        if st.session_state["slider_id_submitted"] in st.session_state.keys():
            set_slider_val = st.session_state[st.session_state["slider_id_submitted"]]
        else:
            set_slider_val = self.variables_quant.default_val_slider

        if self.variables_quant.all_datapoints_submitted in st.session_state.keys():
            all_datapoints = st.session_state[self.variables_quant.all_datapoints_submitted]
        else:
            all_datapoints = st.session_state[self.variables_quant.all_datapoints]

        return self.ionmodule.benchmarking(
            f,  # self.user_input["input_csv"],
            self.user_input["input_format"],
            self.user_input,
            all_datapoints,
            default_cutoff_min_prec=set_slider_val,
        )

    def _update_session_state_with_results(self, all_datapoints: pd.DataFrame) -> None:
        """Updates the session state with the results of the benchmarking."""

    def _initialize_highlight_column(self) -> None:
        """Initializes the highlight column in the all_datapoints DataFrame."""
        if "Highlight" not in st.session_state[self.variables_quant.all_datapoints].columns:
            st.session_state[self.variables_quant.all_datapoints].insert(
                0, "Highlight", [False] * len(st.session_state[self.variables_quant.all_datapoints].index)
            )
        else:
            st.session_state[self.variables_quant.all_datapoints]["Highlight"] = [False] * len(
                st.session_state[self.variables_quant.all_datapoints].index
            )

    def _handle_benchmarking_exception(self, status_placeholder: Any, exception: Exception) -> None:
        """Handles exceptions that occur during the benchmarking process."""
        status_placeholder.error(":x: Proteobench ran into a problem")
        st.error(exception, icon="🚨")

    def _generate_results_after_benchmarking(
        self,
        result_performance: pd.DataFrame,
        all_datapoints: pd.DataFrame,
        input_df: pd.DataFrame,
    ) -> None:
        """Generates and displays the results after the benchmarking process."""
        self.generate_results(result_performance, all_datapoints, True, input_df)

    def table_callback_submitted(self) -> None:
        """
        Callback function for handling edits made to the data table in the UI.
        It updates the session state to reflect changes made to the data points.
        """
        edits = st.session_state[st.session_state["table_id"]]["edited_rows"].items()
        for k, v in edits:
            try:
                st.session_state[self.variables_quant.all_datapoints_submitted][list(v.keys())[0]].iloc[k] = list(
                    v.values()
                )[0]
            except TypeError:
                return
        st.session_state[self.variables_quant.highlight_list_submitted] = list(
            st.session_state[self.variables_quant.all_datapoints_submitted]["Highlight"]
        )
        st.session_state[self.variables_quant.placeholder_table] = st.session_state[
            self.variables_quant.all_datapoints_submitted
        ]

        # Plot any changes made to the data points
        try:
            fig_metric = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_quant.fig_metric] = fig_metric

    def slider_callback(self) -> None:
        """
        Callback function for the slider input. It adjusts the data points displayed based on
        the selected slider value, such as the minimum number of ion quantifications.
        """
        st.session_state[self.variables_quant.all_datapoints] = self.ionmodule.filter_data_point(
            st.session_state[self.variables_quant.all_datapoints], st.session_state[st.session_state["slider_id"]]
        )

        try:
            fig_metric = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_quant.fig_metric] = fig_metric

    def slider_callback_submitted(self) -> None:
        """
        Callback function for the slider input. It adjusts the data points displayed based on
        the selected slider value, such as the minimum number of ion quantifications.
        """
        st.session_state[self.variables_quant.all_datapoints_submitted] = self.ionmodule.filter_data_point(
            st.session_state[self.variables_quant.all_datapoints_submitted],
            st.session_state[st.session_state["slider_id_submitted"]],
        )

        try:
            fig_metric = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_quant.fig_metric] = fig_metric

    def read_parameters(self) -> Any:
        """
        Reads and processes the parameter files provided by the user.

        Returns:
            The parameters read from the file, or None if there's an error.
        """
        params = None

        try:
            params = self.ionmodule.load_params_file(
                self.user_input[self.variables_quant.meta_data], self.user_input["input_format"]
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

    def create_sample_name(self) -> str:
        """
        Generates a unique sample name based on the input format, software version, and the current timestamp.

        Returns:
            A string representing the generated sample name.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_name = "-".join(
            [
                self.user_input["input_format"],
                # self.user_input["software_version"],
                # self.user_input["enable_match_between_runs"],
                time_stamp,
            ]
        )

        return sample_name

    def create_first_new_plot(self) -> None:
        """
        Generates and displays the initial plots and data tables based on the benchmark results.
        This includes setting up UI elements for displaying these results.
        """
        st.header("Results")
        st.subheader("Sample of the processed file")
        st.markdown(open(self.variables_quant.description_table_md, "r").read())
        st.session_state[self.variables_quant.df_head] = st.dataframe(
            st.session_state[self.variables_quant.result_perf].head(100)
        )

        st.markdown(st.markdown(open(self.variables_quant.description_results_md, "r").read()))

        st.subheader("Download calculated ratios")
        random_uuid = uuid.uuid4()
        sample_name = self.create_sample_name()
        st.download_button(
            label="Download",
            data=streamlit_utils.save_dataframe(st.session_state[self.variables_quant.result_perf]),
            file_name=f"{sample_name}.csv",
            mime="text/csv",
            key=f"{random_uuid}",
        )

        st.subheader("Mean error between conditions")
        st.markdown(self.variables_quant.texts.ShortMessages.submission_result_description)

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal ion quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state[st.session_state["slider_id"]],
            on_change=self.slider_callback,
            key=st.session_state["slider_id"],
        )

        st.session_state[self.variables_quant.all_datapoints] = self.ionmodule.filter_data_point(
            st.session_state[self.variables_quant.all_datapoints], st.session_state[st.session_state["slider_id"]]
        )

        try:
            st.session_state[self.variables_quant.fig_metric] = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        placeholder_fig_compare = st.empty()
        placeholder_fig_compare.plotly_chart(
            st.session_state[self.variables_quant.fig_metric], use_container_width=True
        )
        st.session_state[self.variables_quant.placeholder_fig_compare] = placeholder_fig_compare

        st.session_state["table_id"] = uuid.uuid4()

        st.data_editor(
            st.session_state[self.variables_quant.all_datapoints_submitted],
            key=st.session_state["table_id"],
            on_change=self.table_callback_submitted,
        )

        self.render_download_container(reset_uuid=True)

        st.subheader("Add results to online repository")
        st.markdown(open(self.variables_quant.description_submission_md, "r").read())

    def call_later_plot(self) -> None:
        """
        Updates the plot data and UI elements after re-running the benchmark with new parameters or data.
        """
        fig_metric = st.session_state[self.variables_quant.fig_metric]
        st.session_state[self.variables_quant.fig_metric].data[0].x = fig_metric.data[0].x
        st.session_state[self.variables_quant.fig_metric].data[0].y = fig_metric.data[0].y

        st.session_state[self.variables_quant.placeholder_fig_compare].plotly_chart(
            st.session_state[self.variables_quant.fig_metric], use_container_width=True
        )

    def generate_results(
        self,
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
            st.session_state[self.variables_quant.result_perf] = result_performance
            st.session_state[self.variables_quant.all_datapoints] = all_datapoints
            st.session_state[self.variables_quant.input_df] = input_df

            # if not self.variables_quant.first_new_plot:
            #    st.session_state[self.variables_quant.df_head] = st.session_state[self.variables_quant.result_perf].head(
            #        100
            #    )

            # st.session_state[self.variables_quant.fig_logfc] = self.plots_for_current_data(recalculate)

            # if recalculate:
            #    try:
            #        st.session_state[self.variables_quant.fig_metric] = PlotDataPoint.plot_metric(
            #            st.session_state[self.variables_quant.all_datapoints]
            #        )
            #    except Exception as e:
            #        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

            # if self.variables_quant.first_new_plot:
            #    self.create_first_new_plot()
            # else:
            # self.call_later_plot()

        if all_datapoints is not None:
            st.session_state[self.variables_quant.all_datapoints] = all_datapoints
            st.session_state[self.variables_quant.input_df] = input_df

        # Create unique element IDs
        # uuids = [
        #    self.variables_quant.meta_file_uploader_uuid,
        #    self.variables_quant.comments_submission_uuid,
        #    self.variables_quant.check_submission_uuid,
        # ]

        # for uuid_key in uuids:
        #    if uuid_key not in st.session_state:
        #        st.session_state[uuid_key] = uuid.uuid4()

        # if self.variables_quant.first_new_plot:
        #    self.create_submission_elements()
        # if self.user_input[self.variables_quant.meta_data]:
        #    params = self.read_parameters()
        # if st.session_state[self.variables_quant.check_submission] and params != None:
        #    pr_url = self.make_submission_webinterface(params)
        # if (
        #    st.session_state[self.variables_quant.check_submission]
        #    and params != None
        #    and self.variables_quant.submit in st.session_state
        #    and pr_url != None
        # ):
        #    self.successful_submission(pr_url)
        # self.variables_quant.first_new_plot = False

    def wrap_public_submission_form(self) -> None:
        if self.variables_quant.first_new_plot:
            self.create_submission_elements()

        if self.user_input[self.variables_quant.meta_data]:
            params = self.read_parameters()
        else:
            params = None

        if st.session_state[self.variables_quant.check_submission] and params != None:
            pr_url = self.make_submission_webinterface(params)
        if self.submission_ready == False:
            return
        if (
            st.session_state[self.variables_quant.check_submission]
            and params != None
            and self.variables_quant.submit in st.session_state
            and pr_url != None
        ):
            self.successful_submission(pr_url)

    def plots_for_current_data(self, recalculate: bool) -> go.Figure:
        """
        Generates and returns plots based on the current benchmark data.

        Args:
            recalculate: Boolean to determine if the plot needs to be recalculated.

        Returns:
            A Plotly graph object containing the generated plot.
        """
        if self.variables_quant.result_perf not in st.session_state.keys():
            st.error(":x: Please provide a result file", icon="🚨")
            return False

        # filter result_performance dataframe on nr_observed column
        st.session_state[self.variables_quant.result_perf] = st.session_state[self.variables_quant.result_perf][
            st.session_state[self.variables_quant.result_perf]["nr_observed"]
            >= st.session_state[st.session_state["slider_id"]]
        ]

        if recalculate:
            parse_settings = self.parsesettingsbuilder.build_parser(self.user_input["input_format"])

            fig_logfc = PlotDataPoint.plot_fold_change_histogram(
                st.session_state[self.variables_quant.result_perf], parse_settings.species_expected_ratio()
            )
            fig_CV = PlotDataPoint.plot_CV_violinplot(st.session_state[self.variables_quant.result_perf])
            st.session_state[self.variables_quant.fig_cv] = fig_CV
            st.session_state[self.variables_quant.fig_logfc] = fig_logfc
        else:
            fig_logfc = st.session_state[self.variables_quant.fig_logfc]
            fig_CV = st.session_state[self.variables_quant.fig_cv]

        if self.variables_quant.first_new_plot:
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

        st.subheader("Sample of the processed file")
        st.markdown(open(self.variables_quant.description_table_md, "r").read())
        st.session_state[self.variables_quant.df_head] = st.dataframe(
            st.session_state[self.variables_quant.result_perf].head(100)
        )

        st.subheader("Download calculated ratios")
        random_uuid = uuid.uuid4()
        sample_name = self.create_sample_name()
        st.download_button(
            label="Download",
            data=streamlit_utils.save_dataframe(st.session_state[self.variables_quant.result_perf]),
            file_name=f"{sample_name}.csv",
            mime="text/csv",
            key=f"{random_uuid}",
        )

        return fig_logfc

    def display_results_all_data(self) -> None:
        """
        Displays the results for all data in Tab 1.
        """
        st.title("Results (All Data)")
        self.init_slider()
        self._create_slider()
        self.create_selectbox()
        self.create_results_existing()

    def display_results_all_data_submitted(self) -> None:
        """
        Displays the results for all data in Tab 1.
        """
        st.title("Results (All Data)")
        self.init_slider_submitted()
        self._create_slider_submitted()
        self.create_selectbox_submitted()
        self.create_results_submitted()

    def display_submission_details(self) -> None:
        """
        Displays the submission form and details on the data in Tab 2.
        """
        st.title("Submission Details")
        self.create_submission_elements()
        if self.user_input[self.variables_quant.meta_data]:
            params = self.read_parameters()
        else:
            params = None
        if st.session_state[self.variables_quant.check_submission] and params is not None:
            pr_url = self.make_submission_webinterface(params)
            if pr_url is not None:
                self.successful_submission(pr_url)

    def display_results_new_submissions(self) -> None:
        """
        Displays the results for new submissions in Tab 3.
        """
        st.title("Results (New Submissions)")
        self.init_slider()
        self.create_results(show_new_submissions=True)

    def display_public_submission_form(self) -> None:
        """
        Displays the public submission form in Tab 4.
        """
        st.title("Public Submission Form")
        # Implement the public submission form here
        st.write("Public submission form goes here.")

    def get_all_data(self) -> Optional[pd.DataFrame]:
        """
        Returns all data points.
        """
        return st.session_state.get(self.variables_quant.all_datapoints)

    def get_new_submissions_data(self) -> Optional[pd.DataFrame]:
        """
        Returns data points from new submissions only.
        """
        return st.session_state.get(self.variables_quant.all_datapoints_submission)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    QuantUIObjects()
