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
from pages.pages_variables.Quant.lfq.ion.DDA.variables import VariablesDDAQuant
from streamlit_extras.let_it_rain import rain

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.lfq.ion.DDA.quant_lfq_ion_DDA import (
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
        self.variables_quant: VariablesDDAQuant = variables_quant
        self.ionmodule: IonModule = ionmodule
        self.parsesettingsbuilder: ParseSettingsBuilder = parsesettingsbuilder
        self.user_input: Dict[str, Any] = dict()

        # Create page config and sidebar
        pbb.proteobench_page_config()
        pbb.proteobench_sidebar()

        self.first_point_plotted = False
        st.session_state[self.variables_quant.submit] = False
        self.stop_duplicating = False

    def display_submission_form(self) -> None:
        """Creates the main submission form for the Streamlit UI."""
        with st.form(key="main_form"):
            self.generate_input_fields()
            self.generate_additional_parameters_fields()
            st.markdown(self.variables_quant.texts.ShortMessages.run_instructions)
            submit_button = st.form_submit_button("Parse and bench", help=self.variables_quant.texts.Help.parse_button)

        if submit_button:
            self.process_submission_form()

    def generate_input_widget(self, input_format: str, content: dict) -> Any:
        """Generates input fields in the Streamlit UI based on the specified format and content."""
        field_type = content.get("type")
        if field_type == "text_area":
            return self.generate_text_area_widget(input_format, content)
        elif field_type == "text_input":
            return self._generate_text_input(input_format, content)
        elif field_type == "number_input":
            return self._generate_number_input(content)
        elif field_type == "selectbox":
            return self._generate_selectbox(input_format, content)
        elif field_type == "checkbox":
            return self._generate_checkbox(input_format, content)

    def initialize_main_slider(self) -> None:
        if self.variables_quant.slider_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_uuid] = uuid.uuid4()
        if st.session_state[self.variables_quant.slider_id_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_quant.slider_id_uuid]] = (
                self.variables_quant.default_val_slider
            )

    def generate_main_selectbox(self) -> None:
        """Creates the selectbox for the Streamlit UI."""
        if self.variables_quant.selectbox_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.selectbox_id_uuid] = uuid.uuid4()

        try:
            # TODO: Other labels based on different modules, e.g. mass tolerances are less relevant for DIA
            st.selectbox(
                "Select label to plot",
                ["None", "precursor_mass_tolerance", "fragment_mass_tolerance", "enable_match_between_runs"],
                key=st.session_state[self.variables_quant.selectbox_id_uuid],
            )
        except Exception as e:
            st.error(f"Unable to create the selectbox: {e}", icon="🚨")

    def generate_submitted_selectbox(self) -> None:
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

    def initialize_submitted_slider(self) -> None:
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = uuid.uuid4()
        if st.session_state[self.variables_quant.slider_id_submitted_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]] = (
                self.variables_quant.default_val_slider
            )

    def display_submitted_results(self) -> None:
        """Displays the results section of the page for submitted data."""
        # handled_submission = self.process_submission_form()
        # if handled_submission == False:
        #    return

        self.initialize_submitted_data_points()
        data_points_filtered = self.filter_data_submitted_slider()

        metric = st.radio(
            "Select metric to plot",
            options=["Median", "Mean"],
            help="Toggle between median and mean absolute difference metrics.",
            key="placeholder2",  # TODO: add to variables
        )

        if len(data_points_filtered) == 0:
            st.error(f"No datapoints available for plotting", icon="🚨")

        try:
            fig_metric = PlotDataPoint.plot_metric(
                data_points_filtered,
                metric=metric,
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_submitted_uuid]],
            )
            st.plotly_chart(fig_metric, use_container_width=True)
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_quant.table_id_uuid] = uuid.uuid4()
        st.data_editor(
            st.session_state[self.variables_quant.all_datapoints_submitted],
            key=st.session_state[self.variables_quant.table_id_uuid],
            on_change=self.handle_submitted_table_edits,
        )

        st.title("Public submission")
        st.markdown(
            "If you want to make this point — and the associated data — publicly available, please go to “Public Submission"
        )

    def display_existing_results(self) -> None:
        """Displays the results section of the page for existing data."""
        self.initialize_main_data_points()
        data_points_filtered = self.filter_data_main_slider()

        metric = st.radio(
            "Select metric to plot",
            options=["Median", "Mean"],
            help="Toggle between median and mean absolute difference metrics.",
        )

        if len(data_points_filtered) == 0:
            st.error(f"No datapoints available for plotting", icon="🚨")

        try:
            fig_metric = PlotDataPoint.plot_metric(
                data_points_filtered,
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
                metric=metric,
            )
            st.plotly_chart(fig_metric, use_container_width=True)
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.dataframe(data_points_filtered)
        self.display_download_section()

    def submit_to_repository(self, params) -> Optional[str]:
        """Handles the submission process of the benchmark results to the ProteoBench repository."""
        st.session_state[self.variables_quant.submit] = True
        button_pressed = self.generate_submission_button()  # None or 'button_pressed'

        if not button_pressed:  # if button_pressed is None
            return None

        self.clear_highlight_column()
        pr_url = self.create_pull_request(params)

        if pr_url:
            self.save_intermediate_submission_data()

        return pr_url

    def show_submission_success_message(self, pr_url) -> None:
        """Handles the UI updates and notifications after a successful submission."""
        if st.session_state[self.variables_quant.submit]:
            st.subheader("SUCCESS")
            st.markdown(self.variables_quant.texts.ShortMessages.submission_processing_warning)
            try:
                st.write(f"Follow your submission approval here: [{pr_url}]({pr_url})")
            except UnboundLocalError:
                pass

            st.session_state[self.variables_quant.submit] = False
            rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)

    def generate_submission_ui_elements(self) -> None:
        """Creates the UI elements necessary for data submission, including metadata uploader and comments section."""
        try:
            self.copy_dataframes_for_submission()
            self.submission_ready = True
        except:
            self.submission_ready = False
            st.error(":x: Please provide a result file", icon="🚨")
        self.generate_metadata_uploader()
        self.generate_comments_section()
        self.generate_confirmation_checkbox()

    def generate_input_fields(self) -> None:
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

    # TODO: change additional_params_json for other modules, to capture relevant parameters
    def generate_additional_parameters_fields(self) -> None:
        """Creates the additional parameters section of the form and initializes the parameter fields."""
        st.markdown(self.variables_quant.texts.ShortMessages.initial_parameters)
        with open(self.variables_quant.additional_params_json) as file:
            config = json.load(file)
        for key, value in config.items():
            if key == "comments_for_plotting":
                self.user_input[key] = self.generate_input_widget(self.user_input["input_format"], value)
            else:
                self.user_input[key] = None

    def process_submission_form(self) -> None:
        """Handles the form submission logic."""
        if not self.user_input["input_csv"]:
            st.error(":x: Please provide a result file", icon="🚨")
            return False
        self.execute_proteobench()
        self.first_point_plotted = True

        # Inform the user with a link to the next tab
        st.info(
            "Form submitted successfully! Please navigate to the 'Results In-Depth' or 'Results New Data' tab for the next step."
        )

    def generate_text_area_widget(self, input_format: str, content: dict) -> Any:
        """Generates a text area input field."""
        placeholder = content.get("placeholder")
        value = content.get("value", {}).get(input_format)
        height = content.get("height", 200)
        return st.text_area(content["label"], placeholder=placeholder, value=value, height=height)

    def initialize_main_data_points(self) -> None:
        """Initializes the all_datapoints variable in the session state."""
        if self.variables_quant.all_datapoints not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints] = None
            st.session_state[self.variables_quant.all_datapoints] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints]
            )

    def initialize_submitted_data_points(self) -> None:
        """Initializes the all_datapoints variable in the session state."""
        if self.variables_quant.all_datapoints_submitted not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints_submitted] = None
            st.session_state[self.variables_quant.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints_submitted]
            )

    def filter_data_main_slider(self) -> None:
        """Filters the data points based on the slider value."""
        if self.variables_quant.slider_id_uuid in st.session_state.keys():
            return self.ionmodule.filter_data_point(
                st.session_state[self.variables_quant.all_datapoints],
                st.session_state[st.session_state[self.variables_quant.slider_id_uuid]],
            )

    def filter_data_submitted_slider(self) -> None:
        """Filters the data points based on the slider value."""
        if (
            self.variables_quant.slider_id_submitted_uuid in st.session_state.keys()
            and self.variables_quant.all_datapoints_submitted in st.session_state.keys()
        ):
            return self.ionmodule.filter_data_point(
                st.session_state[self.variables_quant.all_datapoints_submitted],
                st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]],
            )

    def set_highlight_column_in_submitted_data(self) -> None:
        """Initializes the highlight column in the data points."""
        df = st.session_state[self.variables_quant.all_datapoints_submitted]
        if (
            self.variables_quant.highlight_list_submitted not in st.session_state.keys()
            and "Highlight" not in df.columns
        ):
            df.insert(0, "Highlight", [False] * len(df.index))
        elif "Highlight" not in df.columns:
            df.insert(0, "Highlight", st.session_state[self.variables_quant.highlight_list_submitted])
        elif "Highlight" in df.columns:
            # Not sure how 'Highlight' column became object dtype
            df["Highlight"] = df["Highlight"].astype(bool).fillna(False)
        # only needed for last elif, but to be sure apply always:
        st.session_state[self.variables_quant.all_datapoints_submitted] = df

    def generate_main_slider(self) -> None:
        """Creates a slider input."""
        if self.variables_quant.slider_id_uuid not in st.session_state:
            st.session_state[self.variables_quant.slider_id_uuid] = uuid.uuid4()
        slider_key = st.session_state[self.variables_quant.slider_id_uuid]

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal ion quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state.get(slider_key, self.variables_quant.default_val_slider),
            key=slider_key,
        )

    def generate_submitted_slider(self) -> None:
        """Creates a slider input."""
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state:
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = uuid.uuid4()
        slider_key = st.session_state[self.variables_quant.slider_id_submitted_uuid]

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal ion quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state.get(slider_key, self.variables_quant.default_val_slider),
            key=slider_key,
        )

    def display_download_section(self, reset_uuid=False) -> None:
        """Render the selector and area for raw data download."""
        if len(st.session_state[self.variables_quant.all_datapoints]) == 0:
            st.error("No data available for download.", icon="🚨")
            return

        downloads_df = st.session_state[self.variables_quant.all_datapoints][["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        if self.variables_quant.placeholder_downloads_container not in st.session_state.keys() or reset_uuid:
            st.session_state[self.variables_quant.placeholder_downloads_container] = st.empty()
            st.session_state[self.variables_quant.download_selector_id_uuid] = uuid.uuid4()

        with st.session_state[self.variables_quant.placeholder_downloads_container].container(border=True):
            st.subheader("Download raw datasets")

            st.selectbox(
                "Select dataset",
                downloads_df["intermediate_hash"],
                index=None,
                key=st.session_state[self.variables_quant.download_selector_id_uuid],
                format_func=lambda x: downloads_df["id"][x],
            )

            if (
                st.session_state[st.session_state[self.variables_quant.download_selector_id_uuid]] != None
                and st.secrets["storage"]["dir"] != None
            ):
                dataset_path = (
                    st.secrets["storage"]["dir"]
                    + "/"
                    + st.session_state[st.session_state[self.variables_quant.download_selector_id_uuid]]
                )
                if os.path.isdir(dataset_path):
                    files = os.listdir(dataset_path)
                    for file_name in files:
                        path_to_file = dataset_path + "/" + file_name
                        with open(path_to_file, "rb") as file:
                            st.download_button(file_name, file, file_name=file_name)
                else:
                    st.write("Directory for this dataset does not exist, this should not happen.")

    def generate_submission_button(self) -> Optional[str]:
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

    def clear_highlight_column(self) -> None:
        """Removes the highlight column from the submission data if it exists."""
        if "Highlight" in st.session_state[self.variables_quant.all_datapoints_submission].columns:
            st.session_state[self.variables_quant.all_datapoints_submission].drop("Highlight", inplace=True, axis=1)

    def create_pull_request(self, params: Any) -> Optional[str]:
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

    def save_intermediate_submission_data(self) -> None:
        """Stores intermediate and input data to the storage directory if available."""
        _id = str(
            st.session_state[self.variables_quant.all_datapoints_submission][
                st.session_state[self.variables_quant.all_datapoints_submission]["old_new"] == "new"
            ].iloc[-1, :]["intermediate_hash"]
        )

        self.user_input["input_csv"].getbuffer()

        if "storage" in st.secrets.keys():
            logger.info("Save intermediate raw")
            self.ionmodule.write_intermediate_raw(
                dir=st.secrets["storage"]["dir"],
                ident=_id,
                input_file_obj=self.user_input["input_csv"],
                result_performance=st.session_state[self.variables_quant.result_performance_submission],
                param_loc=self.user_input[self.variables_quant.meta_data],
                comment=st.session_state[self.variables_quant.meta_data_text],
            )

    def copy_dataframes_for_submission(self) -> None:
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

    def generate_metadata_uploader(self) -> None:
        """Creates the file uploader for meta data."""
        self.user_input[self.variables_quant.meta_data] = st.file_uploader(
            "Meta data for searches",
            help=self.variables_quant.texts.Help.meta_data_file,
            accept_multiple_files=True,
        )

    def generate_comments_section(self) -> None:
        """Creates the text area for submission comments."""
        self.user_input["comments_for_submission"] = st.text_area(
            "Comments for submission",
            placeholder=self.variables_quant.texts.ShortMessages.parameters_additional,
            height=200,
        )
        st.session_state[self.variables_quant.meta_data_text] = self.user_input["comments_for_submission"]

    def generate_confirmation_checkbox(self) -> None:
        """Creates the confirmation checkbox for metadata correctness."""
        st.session_state[self.variables_quant.check_submission] = st.checkbox(
            "I confirm that the metadata is correct",
        )
        self.stop_duplicating = True

    def execute_proteobench(self) -> None:
        """Executes the ProteoBench benchmarking process."""
        if self.variables_quant.all_datapoints_submitted not in st.session_state:
            self.initialize_main_data_points()

        result_performance, all_datapoints, input_df = self.run_benchmarking_process()
        st.session_state[self.variables_quant.all_datapoints_submitted] = all_datapoints

        self.set_highlight_column_in_submitted_data()

        st.session_state[self.variables_quant.result_perf] = result_performance

        st.session_state[self.variables_quant.input_df] = input_df

    def run_benchmarking_process(self):
        """Executes the benchmarking process and returns the results."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(self.user_input["input_csv"].getbuffer())

        # reload buffer: https://stackoverflow.com/a/64478151/9684872
        self.user_input["input_csv"].seek(0)
        if st.session_state[self.variables_quant.slider_id_submitted_uuid] in st.session_state.keys():
            set_slider_val = st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]]
        else:
            set_slider_val = self.variables_quant.default_val_slider

        if self.variables_quant.all_datapoints_submitted in st.session_state.keys():
            all_datapoints = st.session_state[self.variables_quant.all_datapoints_submitted]
        else:
            all_datapoints = st.session_state[self.variables_quant.all_datapoints]

        return self.ionmodule.benchmarking(
            self.user_input["input_csv"],
            self.user_input["input_format"],
            self.user_input,
            all_datapoints,
            default_cutoff_min_prec=set_slider_val,
        )

    def handle_submitted_table_edits(self) -> None:
        """Callback function for handling edits made to the data table in the UI."""
        edits = st.session_state[st.session_state[self.variables_quant.table_id_uuid]]["edited_rows"].items()
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

        if len(st.session_state[self.variables_quant.all_datapoints]) == 0:
            st.error(f"No datapoints available for plotting", icon="🚨")

        try:
            fig_metric = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_quant.fig_metric] = fig_metric

    def load_user_parameters(self) -> Any:
        """Reads and processes the parameter files provided by the user."""
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

    def generate_sample_name(self) -> str:
        """Generates a unique sample name based on the input format, software version, and the current timestamp."""
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_name = "-".join(
            [
                self.user_input["input_format"],
                time_stamp,
            ]
        )

        return sample_name

    def display_public_submission_ui(self) -> None:
        if self.variables_quant.first_new_plot:
            self.generate_submission_ui_elements()

        if self.user_input[self.variables_quant.meta_data]:
            params = self.load_user_parameters()
        else:
            params = None

        if st.session_state[self.variables_quant.check_submission] and params != None:
            pr_url = self.submit_to_repository(params)
        if self.submission_ready == False:
            return
        if (
            st.session_state[self.variables_quant.check_submission]
            and params != None
            and self.variables_quant.submit in st.session_state
            and pr_url != None
        ):
            self.show_submission_success_message(pr_url)

    def generate_current_data_plots(self, recalculate: bool) -> go.Figure:
        """Generates and returns plots based on the current benchmark data."""
        if self.variables_quant.result_perf not in st.session_state.keys():
            st.error(":x: Please provide a result file", icon="🚨")
            return False

        st.session_state[self.variables_quant.result_perf] = st.session_state[self.variables_quant.result_perf][
            st.session_state[self.variables_quant.result_perf]["nr_observed"]
            >= st.session_state[st.session_state[self.variables_quant.slider_id_uuid]]
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

        st.subheader("Download table")
        random_uuid = uuid.uuid4()
        sample_name = self.generate_sample_name()
        st.download_button(
            label="Download",
            data=streamlit_utils.save_dataframe(st.session_state[self.variables_quant.result_perf]),
            file_name=f"{sample_name}.csv",
            mime="text/csv",
            key=f"{random_uuid}",
        )

        return fig_logfc

    def display_all_data_results_main(self) -> None:
        """Displays the results for all data in Tab 1."""
        st.title("Results (All Data)")
        self.initialize_main_slider()
        self.generate_main_slider()
        self.generate_main_selectbox()
        self.display_existing_results()

    def display_all_data_results_submitted(self) -> None:
        """Displays the results for all data in Tab 1."""
        st.title("Results (All Data)")
        self.initialize_submitted_slider()
        self.generate_submitted_slider()
        self.generate_submitted_selectbox()
        self.display_submitted_results()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    QuantUIObjects()
