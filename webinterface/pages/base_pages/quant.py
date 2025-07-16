"""Streamlit-based web interface for ProteoBench."""

import copy
import glob
import json
import logging
import os
import tempfile
import uuid
import zipfile
from datetime import datetime
from pprint import pformat
from typing import Any, Dict, Optional

import pages.texts.proteobench_builder as pbb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_utils
from pages.pages_variables.Quant.lfq_DDA_ion_QExactive_variables import (
    VariablesDDAQuant,
)
from streamlit_extras.let_it_rain import rain

from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.io.parsing.utils import add_maxquant_fixed_modifications
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import (
    DDAQuantIonModuleQExactive as IonModule,
)
from proteobench.plotting.plot_quant import PlotDataPoint

logger: logging.Logger = logging.getLogger(__name__)


def compare_dictionaries(old_dict, new_dict):
    """
    Generate a human-readable string describing differences between two dictionaries.

    Parameters
    ----------
    old_dict : dict
        The old dictionary.
    new_dict : dict
        The new dictionary.

    Returns
    -------
    str
        The human-readable string describing the differences between the two dictionaries.
    """
    changes = []

    # Get all unique keys across both dictionaries
    all_keys = set(old_dict.keys()).union(set(new_dict.keys()))

    for key in all_keys:
        old_value = old_dict.get(key, "[MISSING]")
        new_value = new_dict.get(key, "[MISSING]")
        if str(old_value) != str(new_value) and not (old_value == None and new_value == "[MISSING]"):
            changes.append(f"- **{key}**: `{old_value}` → `{new_value}`")

    if changes:
        return "\n ### Parameter changes detected:\n" + "\n".join(changes)
    else:
        return "\n ### No parameter changes detected. \n"


class QuantUIObjects:
    """
    Main class for the Streamlit interface of ProteoBench quantification.
    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.

    Parameters
    ----------
    variables_quant : VariablesDDAQuant
        The variables for the quantification module.
    ionmodule : IonModule
        The quantification module.
    parsesettingsbuilder : ParseSettingsBuilder
        The parse settings builder.
    """

    def __init__(
        self,
        variables_quant: VariablesDDAQuant,
        ionmodule: IonModule,
        parsesettingsbuilder: ParseSettingsBuilder,
        page_name: str = "/",
    ) -> None:
        """
        Initialize the Streamlit UI objects for the quantification modules.

        Parameters
        ----------
        variables_quant : VariablesDDAQuant
            The variables for the quantification module.
        ionmodule : IonModule
            The quantification module.
        parsesettingsbuilder : ParseSettingsBuilder
            The parse settings builder.
        """
        self.variables_quant: VariablesDDAQuant = variables_quant
        self.ionmodule: IonModule = ionmodule
        self.parsesettingsbuilder: ParseSettingsBuilder = parsesettingsbuilder
        self.page_name = page_name
        self.user_input: Dict[str, Any] = dict()

        # Create page config and sidebar
        pbb.proteobench_page_config()

        st.markdown(
            """
            <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        pbb.proteobench_sidebar(current_page=self.page_name)

        self.first_point_plotted = False
        st.session_state[self.variables_quant.submit] = False
        self.stop_duplicating = False

        if self.variables_quant.params_file_dict not in st.session_state.keys():
            st.session_state[self.variables_quant.params_file_dict] = dict()
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = str()

    def display_submission_form(self) -> None:
        """
        Create the main submission form for the Streamlit UI in Tab 2.
        """
        with st.form(key="main_form"):
            self.generate_input_fields()
            # TODO: Investigate the necessity of generating additional parameters fields in the first tab.
            self.generate_additional_parameters_fields()
            st.markdown(self.variables_quant.texts.ShortMessages.run_instructions)
            submit_button = st.form_submit_button("Parse and bench", help=self.variables_quant.texts.Help.parse_button)

        if submit_button:
            self.process_submission_form()

    def generate_input_widget(self, input_format: str, content: dict, key: str = "", editable: bool = True) -> Any:
        """
        Generate input fields in the Streamlit UI based on the specified format and content.

        Parameters
        ----------
        input_format : str
            The input format.
        content : dict
            The content of the input fields.
        key : str
            The key of the input fields.
        editable : bool
            Whether the input fields are editable.

        Returns
        -------
        Any
            The input fields.
        """
        field_type = content.get("type")
        if field_type == "text_area":
            return self.generate_text_area_widget(input_format, content, editable=editable)
        elif field_type == "text_input":
            return self._generate_text_input(input_format, content, key, editable=editable)
        elif field_type == "number_input":
            return self._generate_number_input(content, key, editable=editable)
        elif field_type == "selectbox":
            return self._generate_selectbox(input_format, content, key, editable=editable)
        elif field_type == "checkbox":
            return self._generate_checkbox(content=content, key=key, editable=editable)

    def _generate_text_area(self, input_format: str, content: dict, key: str = "") -> Any:
        """
        Generate a text area input field.

        Parameters
        ----------
        input_format : str
            The input format.
        content : dict
            The content of the text area.
        key : str
            The key of the text area.

        Returns
        -------
        Any
            The text area input field.
        """
        placeholder = content.get("placeholder")
        if key in st.session_state[self.variables_quant.params_file_dict].keys():
            value = st.session_state[self.variables_quant.params_file_dict].get(key)  # Get parsed value if available
        else:
            value = content.get("value", {}).get(input_format)
        height = content.get("height", 200)  # Default height if not specified
        return st.text_area(
            content["label"],
            placeholder=placeholder,
            key=self.variables_quant.prefix_params + key,
            value=value,
            height=height,
            on_change=self.update_parameters_submission_form(
                key, st.session_state.get(self.variables_quant.prefix_params + key, 0)
            ),
        )

        # Function to update session state dictionary

    def update_parameters_submission_form(self, field, value) -> None:
        """
        Update the session state dictionary with the specified field and value.

        Parameters
        ----------
        field : str
            The field to update.
        value : Any
            The value to update the field with.
        """
        try:
            st.session_state[self.variables_quant.params_json_dict][field] = value
        except KeyError:
            st.session_state[self.variables_quant.params_json_dict] = {}
            st.session_state[self.variables_quant.params_json_dict][field] = value

    def _generate_text_input(self, input_format: str, content: dict, key: str = "", editable: bool = True) -> Any:
        """
        Generate a text input field.

        Parameters
        ----------
        input_format : str
            The input format.
        content : dict
            The content of the text input field.
        key : str
            The key of the text input field.

        Returns
        -------
        Any
            The text input field.
        """
        placeholder = content.get("placeholder")
        if key in st.session_state[self.variables_quant.params_file_dict].keys():
            value = st.session_state[self.variables_quant.params_file_dict].get(key)  # Get parsed value if available
        else:
            value = content.get("value", {}).get(input_format)

        return st.text_input(
            content["label"],
            placeholder=placeholder,
            key=self.variables_quant.prefix_params + key,
            value=value,
            on_change=self.update_parameters_submission_form(
                key, st.session_state.get(self.variables_quant.prefix_params + key, 0)
            ),
            disabled=not editable,
        )

    def _generate_number_input(self, content: dict, key: str = "", editable: bool = True) -> Any:
        """
        Generate a number input field.

        Parameters
        ----------
        content : dict
            The content of the number input field.
        key : str
            The key of the number input field.
        editable : bool
            Whether the number input field is editable.

        Returns
        -------
        Any
            The number input field.
        """
        if key in st.session_state[self.variables_quant.params_file_dict].keys():
            value = st.session_state[self.variables_quant.params_file_dict].get(key)  # Get parsed value if available
        else:
            value = content.get("value", {}).get("min_value")
        return st.number_input(
            content["label"],
            value=value,
            key=self.variables_quant.prefix_params + key,
            format=content["format"],
            min_value=content["min_value"],
            max_value=content["max_value"],
            on_change=self.update_parameters_submission_form(
                key, st.session_state.get(self.variables_quant.prefix_params + key, 0)
            ),
            disabled=not editable,
        )

    def _generate_selectbox(self, input_format: str, content: dict, key: str = "", editable: bool = True) -> Any:
        """
        Generate a selectbox input field.

        Parameters
        ----------
        input_format : str
            The input format.
        content : dict
            The content of the selectbox.
        key : str
            The key of the selectbox.
        editable : bool
            Whether the selectbox is editable.

        Returns
        -------
        Any
            The selectbox input field.
        """
        options = content.get("options", [])
        if key in st.session_state[self.variables_quant.params_file_dict].keys():
            value = st.session_state[self.variables_quant.params_file_dict].get(key)  # Get parsed value if available
        else:
            value = content.get("value", {}).get(input_format)
        index = options.index(value) if value in options else 0

        return st.selectbox(
            content["label"],
            options,
            key=self.variables_quant.prefix_params + key,
            index=index,
            on_change=self.update_parameters_submission_form(
                key, st.session_state.get(self.variables_quant.prefix_params + key, 0)
            ),
            disabled=not editable,
        )

    def _generate_checkbox(self, content: dict, key: str = "", editable: bool = True) -> Any:
        """
        Generate a checkbox input field.

        Parameters
        ----------
        content : dict
            The content of the checkbox.
        key : str
            The key of the checkbox.
        editable : bool
            Whether the checkbox is editable.

        Returns
        -------
        Any
            The checkbox input field.
        """
        value = content.get("value", {})
        if key in st.session_state[self.variables_quant.params_file_dict].keys():
            value = st.session_state[self.variables_quant.params_file_dict].get(key)
        return st.checkbox(
            content["label"],
            key=self.variables_quant.prefix_params + key,
            value=value,
            on_change=self.update_parameters_submission_form(
                key, st.session_state.get(self.variables_quant.prefix_params + key, 0)
            ),
            disabled=not editable,
        )

    def initialize_main_slider(self) -> None:
        """
        Initialize the slider for the main data.
        """
        if self.variables_quant.slider_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_uuid] = uuid.uuid4()
        if st.session_state[self.variables_quant.slider_id_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_quant.slider_id_uuid]] = (
                self.variables_quant.default_val_slider
            )

    def generate_main_selectbox(self) -> None:
        """
        Create the selectbox for the Streamlit UI.
        """
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
        """
        Create the selectbox for the Streamlit UI.
        """
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
        """
        Initialize the slider for the submitted data.
        """
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = uuid.uuid4()
        if st.session_state[self.variables_quant.slider_id_submitted_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]] = (
                self.variables_quant.default_val_slider
            )

    def display_submitted_results(self) -> None:
        """
        Display the results section of the page for submitted data.
        """
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
            st.error("No datapoints available for plotting", icon="🚨")
            return

        try:
            fig_metric = PlotDataPoint.plot_metric(
                data_points_filtered,
                metric=metric,
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_submitted_uuid]],
            )

            try:
                st.plotly_chart(fig_metric, use_container_width=True)
            except Exception as e:
                st.error("No (new) datapoints available for plotting", icon="🚨")
                return
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
        """
        Display the results section of the page for existing data.
        """
        self.initialize_main_data_points()
        data_points_filtered = self.filter_data_main_slider()

        metric = st.radio(
            "Select metric to plot",
            options=["Median", "Mean"],
            help="Toggle between median and mean absolute difference metrics.",
        )

        if len(data_points_filtered) == 0:
            st.error("No datapoints available for plotting", icon="🚨")

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
        """
        Handle the submission process of the benchmark results to the ProteoBench repository.

        Parameters
        ----------
        params : ProteoBenchParameters
            The parameters for the submission.

        Returns
        -------
        str, optional
            The URL of the pull request if the submission was successful.
        """
        st.session_state[self.variables_quant.submit] = True
        button_pressed = self.generate_submission_button()  # None or 'button_pressed'

        if not button_pressed:  # if button_pressed is None
            return None

        # MaxQuant fixed modification handling
        if self.user_input["input_format"] == "MaxQuant":
            st.session_state[self.variables_quant.result_perf] = add_maxquant_fixed_modifications(
                params, st.session_state[self.variables_quant.result_perf]
            )
            # Overwrite the dataframes for submission
            self.copy_dataframes_for_submission()

        self.clear_highlight_column()

        pr_url = self.create_pull_request(params)

        if pr_url:
            self.save_intermediate_submission_data()

        return pr_url

    def show_submission_success_message(self, pr_url) -> None:
        """
        Handle the UI updates and notifications after a successful submission.

        Parameters
        ----------
        pr_url : str
            The URL of the pull request.
        """
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
        """
        Create the UI elements necessary for data submission, including metadata uploader and comments section.
        """
        try:
            self.copy_dataframes_for_submission()
            self.submission_ready = True
        except:
            self.submission_ready = False
            st.error(":x: Please provide a result file", icon="🚨")
        self.generate_metadata_uploader()

    def generate_input_fields(self) -> None:
        """
        Create the input section of the form.
        """
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
        """
        Create the additional parameters section of the form and initializes the parameter fields.
        """
        with open(self.variables_quant.additional_params_json) as file:
            config = json.load(file)
        for key, value in config.items():
            if key.lower() == "software_name":
                editable = False
            else:
                editable = True

            if key == "comments_for_plotting":
                self.user_input[key] = self.generate_input_widget(self.user_input["input_format"], value, editable)
            else:
                self.user_input[key] = None

    def process_submission_form(self) -> None:
        """
        Handle the form submission logic.

        Returns
        -------
        bool, optional
            Whether the submission was handled unsuccessfully.
        """
        if not self.user_input["input_csv"]:
            st.error(":x: Please provide a result file", icon="🚨")
            return False
        self.execute_proteobench()
        self.first_point_plotted = True

        # Inform the user with a link to the next tab
        st.info(
            "Form submitted successfully! Please navigate to the 'Results In-Depth' or 'Results New Data' tab for the next step."
        )

    def generate_text_area_widget(self, input_format: str, content: dict, editable: bool = True) -> Any:
        """
        Generate a text area input field.

        Parameters
        ----------
        input_format : str
            The input format.
        content : dict
            The content of the text area.
        editable : bool
            Whether the text area is editable.

        Returns
        -------
        Any
            The text area input field.
        """
        placeholder = content.get("placeholder")
        value = content.get("value", {}).get(input_format)
        height = content.get("height", 200)
        return st.text_area(
            content["label"], placeholder=placeholder, value=value, height=height, disabled=not editable
        )

    def initialize_main_data_points(self) -> None:
        """
        Initialize the all_datapoints variable in the session state.
        """
        if self.variables_quant.all_datapoints not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints] = None
            st.session_state[self.variables_quant.all_datapoints] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints]
            )

    def initialize_submitted_data_points(self) -> None:
        """
        Initialize the all_datapoints variable in the session state.
        """
        if self.variables_quant.all_datapoints_submitted not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints_submitted] = None
            st.session_state[self.variables_quant.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints_submitted]
            )

    def filter_data_main_slider(self) -> pd.DataFrame:
        """
        Filter the data points based on the slider value.

        Returns
        -------
        pandas.DataFrame
            The filtered data points.
        """
        if self.variables_quant.slider_id_uuid in st.session_state.keys():
            return self.ionmodule.filter_data_point(
                st.session_state[self.variables_quant.all_datapoints],
                st.session_state[st.session_state[self.variables_quant.slider_id_uuid]],
            )

    def filter_data_submitted_slider(self) -> pd.DataFrame:
        """
        Filter the data points based on the slider value.

        Returns
        -------
        pd.DataFrame
            The filtered data points.
        """
        if (
            self.variables_quant.slider_id_submitted_uuid in st.session_state.keys()
            and self.variables_quant.all_datapoints_submitted in st.session_state.keys()
        ):
            return self.ionmodule.filter_data_point(
                st.session_state[self.variables_quant.all_datapoints_submitted],
                st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]],
            )

    def set_highlight_column_in_submitted_data(self) -> None:
        """
        Initialize the highlight column in the data points.
        """
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
        """
        Create a slider input.
        """
        if self.variables_quant.slider_id_uuid not in st.session_state:
            st.session_state[self.variables_quant.slider_id_uuid] = uuid.uuid4()
        slider_key = st.session_state[self.variables_quant.slider_id_uuid]

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal precursor quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state.get(slider_key, self.variables_quant.default_val_slider),
            key=slider_key,
        )

    def generate_submitted_slider(self) -> None:
        """
        Create a slider input.
        """
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state:
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = uuid.uuid4()
        slider_key = st.session_state[self.variables_quant.slider_id_submitted_uuid]

        st.markdown(open(self.variables_quant.description_slider_md, "r").read())

        st.select_slider(
            label="Minimal precursor quantifications (# samples)",
            options=[1, 2, 3, 4, 5, 6],
            value=st.session_state.get(slider_key, self.variables_quant.default_val_slider),
            key=slider_key,
        )

    def display_download_section(self, reset_uuid=False) -> None:
        """
        Render the selector and area for raw data download.

        Parameters
        ----------
        reset_uuid : bool, optional
            Whether to reset the UUID, by default False.
        """
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

            # Sort the intermediate_hash values and get the corresponding ids
            sorted_indices = sorted(range(len(downloads_df["id"])), key=lambda i: downloads_df["id"].iloc[i])
            sorted_intermediate_hash = [downloads_df["intermediate_hash"].iloc[i] for i in sorted_indices]
            sorted_ids = [downloads_df["id"].iloc[i] for i in sorted_indices]

            st.selectbox(
                "Select dataset",
                sorted_intermediate_hash,
                index=None,
                key=st.session_state[self.variables_quant.download_selector_id_uuid],
                format_func=lambda x: sorted_ids[sorted_intermediate_hash.index(x)],
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

    def display_indepth_plots(self) -> None:
        """
        Display the dataset selection dropdown and plot the selected dataset.
        """

        if self.variables_quant.all_datapoints_submitted not in st.session_state.keys():
            st.error("No data available for plotting.", icon="🚨")
            return
        if st.session_state[self.variables_quant.all_datapoints_submitted].empty:
            st.error("No data available for plotting.", icon="🚨")
            return
        downloads_df = st.session_state[self.variables_quant.all_datapoints_submitted][["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        if self.variables_quant.placeholder_dataset_selection_container not in st.session_state.keys():
            st.session_state[self.variables_quant.placeholder_dataset_selection_container] = st.empty()
            st.session_state[self.variables_quant.dataset_selector_id_uuid] = uuid.uuid4()

        st.subheader("Select dataset to plot")

        dataset_options = [("Uploaded dataset", None)] + list(
            zip(downloads_df["id"], downloads_df["intermediate_hash"])
        )

        dataset_selection = st.selectbox(
            "Select dataset",
            dataset_options,
            index=0,
            key=st.session_state[self.variables_quant.dataset_selector_id_uuid],
            format_func=lambda x: x[0],
        )

        public_id, selected_hash = dataset_selection
        self.generate_indepth_plots(True, public_id=public_id, public_hash=selected_hash)

    def generate_submission_button(self) -> Optional[str]:
        """
        Create a button for public submission and returns the PR URL if the button is pressed.

        Returns
        -------
        Optional[str]
            The URL of the pull request.
        """
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
        """
        Remove the highlight column from the submission data if it exists.
        """
        if "Highlight" in st.session_state[self.variables_quant.all_datapoints_submission].columns:
            st.session_state[self.variables_quant.all_datapoints_submission].drop("Highlight", inplace=True, axis=1)

    def create_pull_request(self, params: Any) -> Optional[str]:
        """
        Submit the pull request with the benchmark results and returns the PR URL.

        Parameters
        ----------
        params : Any
            The parameters object.

        Returns
        -------
        Optional[str]
            The URL of the pull request.
        """
        user_comments = self.user_input["comments_for_submission"]

        changed_params_str = compare_dictionaries(self.params_file_dict_copy, params.__dict__)

        try:
            pr_url = self.ionmodule.clone_pr(
                st.session_state[self.variables_quant.all_datapoints_submission],
                params,
                remote_git=self.variables_quant.github_link_pr,
                submission_comments=user_comments + "\n" + changed_params_str,
            )
        except Exception as e:
            st.error(f"Unable to create the pull request: {e}", icon="🚨")
            pr_url = None

        if not pr_url:
            del st.session_state[self.variables_quant.submit]

        return pr_url

    def save_intermediate_submission_data(self) -> None:
        """
        Store intermediate and input data to the storage directory if available.
        """
        _id = str(
            st.session_state[self.variables_quant.all_datapoints_submission][
                st.session_state[self.variables_quant.all_datapoints_submission]["old_new"] == "new"
            ].iloc[-1, :]["intermediate_hash"]
        )

        self.user_input["input_csv"].getbuffer()

        if "storage" in st.secrets.keys():
            extension_input_file = os.path.splitext(self.user_input["input_csv"].name)[1]
            extension_input_parameter_file = os.path.splitext(self.user_input[self.variables_quant.meta_data][0].name)[
                1
            ]
            logger.info("Save intermediate raw")
            self.ionmodule.write_intermediate_raw(
                dir=st.secrets["storage"]["dir"],
                ident=_id,
                input_file_obj=self.user_input["input_csv"],
                result_performance=st.session_state[self.variables_quant.result_performance_submission],
                param_loc=self.user_input[self.variables_quant.meta_data],
                comment=st.session_state[self.variables_quant.meta_data_text],
                extension_input_file=extension_input_file,
                extension_input_parameter_file=extension_input_parameter_file,
            )

    def copy_dataframes_for_submission(self) -> None:
        """
        Create copies of the dataframes before submission.
        """
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
        """
        Create the file uploader for meta data.
        """
        self.user_input[self.variables_quant.meta_data] = st.file_uploader(
            "Meta data for searches",
            help=self.variables_quant.texts.Help.meta_data_file,
            accept_multiple_files=True,
        )

    def generate_comments_section(self) -> None:
        """
        Create the text area for submission comments.
        """
        self.user_input["comments_for_submission"] = st.text_area(
            "Comments for submission",
            placeholder=self.variables_quant.texts.ShortMessages.parameters_additional,
            height=200,
        )
        st.session_state[self.variables_quant.meta_data_text] = self.user_input["comments_for_submission"]

    def generate_confirmation_checkbox(self) -> None:
        """
        Create the confirmation checkbox for metadata correctness.
        """
        st.session_state[self.variables_quant.check_submission] = st.checkbox(
            "I confirm that the metadata is correct",
        )
        self.stop_duplicating = True

    def execute_proteobench(self) -> None:
        """
        Execute the ProteoBench benchmarking process.
        """
        if self.variables_quant.all_datapoints_submitted not in st.session_state:
            self.initialize_main_data_points()

        result_performance, all_datapoints, input_df = self.run_benchmarking_process()
        st.session_state[self.variables_quant.all_datapoints_submitted] = all_datapoints

        self.set_highlight_column_in_submitted_data()

        st.session_state[self.variables_quant.result_perf] = result_performance

        st.session_state[self.variables_quant.input_df] = input_df

    def run_benchmarking_process(self):
        """
        Execute the benchmarking process and returns the results.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            The benchmarking results, all data points, and the input data frame.
        """
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
            st.error("No datapoints available for plotting", icon="🚨")

        try:
            fig_metric = PlotDataPoint.plot_metric(
                st.session_state[self.variables_quant.all_datapoints],
                label=st.session_state[st.session_state[self.variables_quant.selectbox_id_uuid]],
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_quant.fig_metric] = fig_metric

    def load_user_parameters(self) -> Any:
        """
        Read and process the parameter files provided by the user.

        Returns
        -------
        Any
            The parsed parameters.
        """
        params = None

        try:
            params = self.ionmodule.load_params_file(
                self.user_input[self.variables_quant.meta_data], self.user_input["input_format"]
            )
            st.session_state[self.variables_quant.params_json_dict] = (
                params.__dict__ if hasattr(params, "__dict__") else params
            )

        except KeyError:
            st.error("Parsing of meta parameters file for this software is not supported yet.", icon="🚨")
        except Exception as e:
            input_f = self.user_input["input_format"]
            st.error(
                f"Unexpected error while parsing file. Make sure you provided a meta parameters file produced by {input_f}: {e}",
                icon="🚨",
            )
        return params

    def generate_additional_parameters_fields_submission(self) -> None:
        """
        Create the additional parameters section of the form and initializes the parameter fields.
        """
        st.markdown(self.variables_quant.texts.ShortMessages.initial_parameters)

        # Load JSON config
        with open(self.variables_quant.additional_params_json) as file:
            config = json.load(file)

        # Check if parsed values exist in session state
        parsed_params = st.session_state.get(self.variables_quant.params_json_dict, {})

        st_col1, st_col2, st_col3 = st.columns(3)
        input_param_len = int(len(config.items()) / 3)

        for idx, (key, value) in enumerate(config.items()):
            if key.lower() == "software_name":
                editable = False
            else:
                editable = True

            if idx < input_param_len:
                with st_col1:
                    self.user_input[key] = self.generate_input_widget(
                        self.user_input["input_format"], value, key, editable=editable
                    )
            elif idx < input_param_len * 2:
                with st_col2:
                    self.user_input[key] = self.generate_input_widget(
                        self.user_input["input_format"], value, key, editable=editable
                    )
            else:
                with st_col3:
                    self.user_input[key] = self.generate_input_widget(
                        self.user_input["input_format"], value, key, editable=editable
                    )

    def generate_sample_name(self) -> str:
        """
        Generate a unique sample name based on the input format, software version, and the current timestamp.

        Returns
        -------
        str
            The generated sample name.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_name = "-".join(
            [
                self.user_input["input_format"],
                time_stamp,
            ]
        )

        return sample_name

    def get_form_values(self) -> Dict[str, Any]:
        """
        Retrieve all user inputs from Streamlit session state and returns them as a dictionary.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing all user inputs.
        """
        form_values = {}

        # Load JSON config (same file used to create fields)
        with open(self.variables_quant.additional_params_json, "r") as file:
            config = json.load(file)

        # Extract values from session state
        for key in config.keys():
            form_key = self.variables_quant.prefix_params + key  # Ensure correct session key
            form_values[key] = st.session_state.get(form_key, None)  # Retrieve value, default to None if missing

        return form_values

    def display_public_submission_ui(self) -> None:
        """
        Display the public submission section of the page in Tab 4.
        """
        # Initialize Unchecked submission box variable
        if self.variables_quant.check_submission not in st.session_state:
            st.session_state[self.variables_quant.check_submission] = False
        if self.variables_quant.first_new_plot:
            self.generate_submission_ui_elements()

        if self.user_input[self.variables_quant.meta_data]:
            params = self.load_user_parameters()
            st.session_state[self.variables_quant.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)
            print(self.params_file_dict_copy)
            self.generate_additional_parameters_fields_submission()
            self.generate_comments_section()
            self.generate_confirmation_checkbox()
        else:
            params = None

        if st.session_state[self.variables_quant.check_submission] and params != None:
            get_form_values = self.get_form_values()
            params = ProteoBenchParameters(**get_form_values)
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

    def generate_indepth_plots(
        self, recalculate: bool, public_id: Optional[str], public_hash: Optional[str]
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
        if self.variables_quant.result_perf not in st.session_state.keys():
            if public_hash is None:
                st.error(":x: Please submit a result file or select a public run for display", icon="🚨")
                return False
            elif public_id == "Uploaded dataset":
                st.error(":x: Please submit a result file in the Submit New Data Tab", icon="🚨")
                return False

        if public_id == "Uploaded dataset":
            performance_data = st.session_state[self.variables_quant.result_perf]
        else:
            # Downloading the public performance data
            performance_data = None
            if st.secrets["storage"]["dir"] != None:
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
            performance_data["nr_observed"] >= st.session_state[st.session_state[self.variables_quant.slider_id_uuid]]
        ]

        if recalculate:
            parse_settings = self.parsesettingsbuilder.build_parser(self.user_input["input_format"])

            fig_logfc = PlotDataPoint.plot_fold_change_histogram(
                performance_data, parse_settings.species_expected_ratio()
            )
            fig_CV = PlotDataPoint.plot_CV_violinplot(performance_data)
            fig_MA = PlotDataPoint.plot_ma_plot(
                performance_data,
                parse_settings.species_expected_ratio(),
            )
            st.session_state[self.variables_quant.fig_cv] = fig_CV
            st.session_state[self.variables_quant.fig_logfc] = fig_logfc
        else:
            fig_logfc = st.session_state[self.variables_quant.fig_logfc]
            fig_CV = st.session_state[self.variables_quant.fig_cv]
            fig_MA = st.session_state[self.variables_quant.fig_ma_plot]

        if self.variables_quant.first_new_plot:
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
        st.markdown(open(self.variables_quant.description_table_md, "r").read())
        st.session_state[self.variables_quant.df_head] = st.dataframe(performance_data.head(100))

        st.subheader("Download table")
        random_uuid = uuid.uuid4()
        if public_id == "Uploaded dataset":
            # user uploaded data does not have sample name yet
            sample_name = self.generate_sample_name()
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

    def display_all_data_results_main(self) -> None:
        """Display the results for all data in Tab 1."""
        st.title("Results (All Data)")
        self.initialize_main_slider()
        self.generate_main_slider()
        self.generate_main_selectbox()
        self.display_existing_results()

    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 3."""
        st.title("Results (All Data)")
        self.initialize_submitted_slider()
        self.generate_submitted_slider()
        self.generate_submitted_selectbox()
        self.display_submitted_results()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    QuantUIObjects()
