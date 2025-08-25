"""Streamlit-based web interface for ProteoBench."""

import copy
import logging
import uuid
from typing import Any, Dict

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.pages_variables.Quant.lfq_DDA_ion_QExactive_variables import (
    VariablesDDAQuant,
)

from proteobench.exceptions import DatasetAlreadyExistsOnServerError
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import (
    DDAQuantIonModuleQExactive as IonModule,
)
from proteobench.utils.server_io import dataset_folder_exists

from . import (
    tab1_results,
    tab2_form_upload_data,
    tab3_indepth_plots,
    tab4_display_results_submitted,
    tab5_public_submission,
)

logger: logging.Logger = logging.getLogger(__name__)


class QuantUIObjects:
    """Main class for the Streamlit interface of ProteoBench quantification.
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
        self.user_input: Dict[str, Any] = {}
        self.page_name = page_name
        self.submission_ready = False
        self.params_file_dict_copy: Dict[str, Any] = {}

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
            st.session_state[self.variables_quant.params_file_dict] = {}
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = str()

    def display_submission_form(self) -> None:
        """Create the main submission form for the Streamlit UI in Tab 2."""
        with st.form(key="main_form"):
            tab2_form_upload_data.generate_input_fields(
                variables_quant=self.variables_quant,
                parsesettingsbuilder=self.parsesettingsbuilder,
                user_input=self.user_input,
            )
            # TODO: Investigate the necessity of generating additional parameters fields in the first tab.
            tab2_form_upload_data.generate_additional_parameters_fields(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )
            text = self.variables_quant.texts.ShortMessages.run_instructions
            st.markdown(text)
            submit_button = st.form_submit_button(
                "Parse and bench",
                help=self.variables_quant.texts.Help.parse_button,
            )

        if submit_button:
            self.first_point_plotted = tab2_form_upload_data.process_submission_form(
                variables_quant=self.variables_quant,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )

    def display_indepth_plots(self) -> None:
        """
        Display the dataset selection dropdown and plot the selected dataset (Tab 3).
        """
        # the key is a string and links to a pandas.DataFrame
        key_in_state = self.variables_quant.all_datapoints
        if key_in_state not in st.session_state.keys():
            st.error("No data available for plotting.", icon="🚨")
            return
        df = st.session_state[key_in_state]
        if df.empty:
            st.error("No data available for plotting.", icon="🚨")
            return
        downloads_df = df[["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        key_in_state = self.variables_quant.placeholder_dataset_selection_container
        if key_in_state not in st.session_state.keys():
            st.session_state[key_in_state] = st.empty()
            key_in_state = self.variables_quant.dataset_selector_id_uuid
            st.session_state[key_in_state] = uuid.uuid4()

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
        tab3_indepth_plots.generate_indepth_plots(
            variables_quant=self.variables_quant,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
            recalculate=True,
            public_id=public_id,
            public_hash=selected_hash,
        )

    def display_public_submission_ui(self) -> None:
        """
        Display the public submission section of the page in Tab 5.
        """
        try:
            resolved_hash = st.session_state[self.variables_quant.all_datapoints][
                st.session_state[self.variables_quant.all_datapoints][st.session_state["old_new"] == "new"]
            ]["intermediate_hash"].values[0]
            if resolved_hash and dataset_folder_exists(resolved_hash):
                st.error(
                    f":no_entry: This dataset was already submitted. A folder for hash '{resolved_hash}' exists on the server. Submission disabled.",
                    icon="🚫",
                )
                return
        except Exception:
            # Fail-soft; backend will still enforce protection
            pass

        # Initialize Unchecked submission box variable
        if self.variables_quant.check_submission not in st.session_state:
            st.session_state[self.variables_quant.check_submission] = False

        if self.variables_quant.first_new_plot:
            self.submission_ready = tab5_public_submission.generate_submission_ui_elements(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )

        if self.user_input[self.variables_quant.meta_data]:
            params = tab5_public_submission.load_user_parameters(
                variables_quant=self.variables_quant,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )
            st.session_state[self.variables_quant.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)

            tab5_public_submission.generate_additional_parameters_fields_submission(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )
            tab5_public_submission.generate_comments_section(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )
            # ? stop_duplicating is not used?
            self.stop_duplicating = tab5_public_submission.generate_confirmation_checkbox(
                check_submission=self.variables_quant.check_submission
            )
        else:
            params = None

        pr_url = None
        if st.session_state[self.variables_quant.check_submission] and params is not None:
            get_form_values = tab5_public_submission.get_form_values(
                variables_quant=self.variables_quant,
            )
            params = ProteoBenchParameters(**get_form_values, filename=self.variables_quant.additional_params_json)
            try:
                pr_url = tab5_public_submission.submit_to_repository(
                    variables_quant=self.variables_quant,
                    ionmodule=self.ionmodule,
                    user_input=self.user_input,
                    params_from_file=self.params_file_dict_copy,
                    params=params,
                )
            except DatasetAlreadyExistsOnServerError as e:
                st.error(str(e), icon="🚫")
                return
        if not self.submission_ready:
            return
        if (
            st.session_state[self.variables_quant.check_submission]
            and params is not None
            and self.variables_quant.submit in st.session_state
            and pr_url is not None
        ):
            tab5_public_submission.show_submission_success_message(
                variables_quant=self.variables_quant,
                pr_url=pr_url,
            )

    @st.fragment
    def display_all_data_results_main(self) -> None:
        """Display the results for all data in Tab 1."""
        st.title("Results (All Data)")
        tab1_results.initialize_main_slider(
            slider_id_uuid=self.variables_quant.slider_id_uuid,
            default_val_slider=self.variables_quant.default_val_slider,
        )
        tab1_results.generate_main_slider(
            slider_id_uuid=self.variables_quant.slider_id_uuid,
            description_slider_md=self.variables_quant.description_slider_md,
            default_val_slider=self.variables_quant.default_val_slider,
        )
        tab1_results.generate_main_selectbox(
            self.variables_quant, selectbox_id_uuid=self.variables_quant.selectbox_id_uuid
        )
        tab1_results.display_existing_results(variables_quant=self.variables_quant, ionmodule=self.ionmodule)

    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")
        tab4_display_results_submitted.initialize_submitted_slider(
            self.variables_quant.slider_id_submitted_uuid,
            self.variables_quant.default_val_slider,
        )
        tab4_display_results_submitted.generate_submitted_slider(self.variables_quant)
        tab4_display_results_submitted.generate_submitted_selectbox(self.variables_quant)
        tab4_display_results_submitted.display_submitted_results(
            variables_quant=self.variables_quant,
            ionmodule=self.ionmodule,
        )
