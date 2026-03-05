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

from .base import BaseUIModule
from .tabs import (
    tab1_results,
    tab2_form_upload_data,
    tab3_indepth_plots,
    tab4_display_results_submitted,
    tab5_public_submission,
    tab_compare_workflows,
)

logger: logging.Logger = logging.getLogger(__name__)


class QuantUIObjects(BaseUIModule):
    """Main class for the Streamlit interface of ProteoBench quantification.
    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.

    Parameters
    ----------
    variables : VariablesDDAQuant
        The variables for the quantification module.
    ionmodule : IonModule
        The quantification module.
    parsesettingsbuilder : ParseSettingsBuilder
        The parse settings builder.
    """

    def __init__(
        self,
        variables: VariablesDDAQuant,
        ionmodule: IonModule,
        parsesettingsbuilder: ParseSettingsBuilder,
        page_name: str = "/",
    ) -> None:
        """
        Initialize the Streamlit UI objects for the quantification modules.

        Parameters
        ----------
        variables : VariablesDDAQuant
            The variables for the quantification module.
        ionmodule : IonModule
            The quantification module.
        parsesettingsbuilder : ParseSettingsBuilder
            The parse settings builder.
        """
        super().__init__(
            variables=variables, ionmodule=ionmodule, parsesettingsbuilder=parsesettingsbuilder, page_name=page_name
        )

        # Quant-specific attributes
        self.first_point_plotted = False
        st.session_state[self.variables.submit] = False
        self.stop_duplicating = False

    def display_submission_form(self) -> None:
        """Create the main submission form for the Streamlit UI in Tab 2."""
        # Display software selector and AlphaDIA info outside the form so it updates immediately
        tab2_form_upload_data.show_software_selector_and_alphadia_info(
            variables=self.variables,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
        )
        with st.form(key="main_form"):
            tab2_form_upload_data.generate_input_fields(
                user_input=self.user_input,
            )
            # TODO: Investigate the necessity of generating additional parameters fields in the first tab.
            tab2_form_upload_data.generate_additional_parameters_fields(
                variables=self.variables,
                user_input=self.user_input,
            )
            text = self.variables.texts.ShortMessages.run_instructions
            st.markdown(text)
            submit_button = st.form_submit_button(
                "Parse and bench",
                help=self.variables.texts.Help.parse_button,
            )

        if submit_button:
            self.first_point_plotted = tab2_form_upload_data.process_submission_form(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )

    def display_indepth_plots(self) -> None:
        """
        Display the dataset selection dropdown and plot the selected dataset (Tab 3).
        """
        # the key is a string and links to a pandas.DataFrame
        key_in_state = self.variables.all_datapoints
        if key_in_state not in st.session_state.keys():
            st.error("No data available for plotting.", icon="🚨")
            return
        df = st.session_state[key_in_state]
        if df.empty:
            st.error("No data available for plotting.", icon="🚨")
            return
        downloads_df = df[["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        key_in_state = self.variables.placeholder_dataset_selection_container
        if key_in_state not in st.session_state.keys():
            st.session_state[key_in_state] = st.empty()
            key_in_state = self.variables.dataset_selector_id_uuid
            st.session_state[key_in_state] = uuid.uuid4()

        st.subheader("Select dataset to plot")

        dataset_options = [("Uploaded dataset", None)] + list(
            zip(downloads_df["id"], downloads_df["intermediate_hash"])
        )

        dataset_selection = st.selectbox(
            "Select dataset",
            dataset_options,
            index=0,
            key=st.session_state[self.variables.dataset_selector_id_uuid],
            format_func=lambda x: x[0],
        )

        public_id, selected_hash = dataset_selection
        tab3_indepth_plots.generate_indepth_plots(
            module=self.ionmodule,
            variables=self.variables,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
            public_id=public_id,
            public_hash=selected_hash,
        )

    def display_public_submission_ui(self) -> None:
        """
        Display the public submission section of the page in Tab 5.
        """
        try:
            resolved_hash = st.session_state[self.variables.all_datapoints][
                st.session_state[self.variables.all_datapoints][st.session_state["old_new"] == "new"]
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
        if self.variables.check_submission not in st.session_state:
            st.session_state[self.variables.check_submission] = False

        if self.variables.first_new_plot:
            self.submission_ready = tab5_public_submission.generate_submission_ui_elements(
                variables=self.variables,
                user_input=self.user_input,
            )

        if self.user_input[self.variables.meta_data]:
            params = tab5_public_submission.load_user_parameters(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )
            st.session_state[self.variables.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)

            tab5_public_submission.generate_additional_parameters_fields_submission(
                variables=self.variables,
                user_input=self.user_input,
            )
            tab5_public_submission.generate_comments_section(
                variables=self.variables,
                user_input=self.user_input,
            )
            # ? stop_duplicating is not used?
            self.stop_duplicating = tab5_public_submission.generate_confirmation_checkbox(
                check_submission=self.variables.check_submission
            )
        else:
            params = None

        pr_url = None
        if st.session_state[self.variables.check_submission] and params is not None:
            get_form_values = tab5_public_submission.get_form_values(
                variables=self.variables,
            )
            params = ProteoBenchParameters(**get_form_values, filename=self.variables.additional_params_json)
            try:
                pr_url = tab5_public_submission.submit_to_repository(
                    variables=self.variables,
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
            st.session_state[self.variables.check_submission]
            and params is not None
            and self.variables.submit in st.session_state
            and pr_url is not None
        ):
            tab5_public_submission.show_submission_success_message(
                variables=self.variables,
                pr_url=pr_url,
            )

    @st.fragment
    def display_all_data_results_main(self) -> None:
        """Display the results for all data in Tab 1."""
        tab1_results.initialize_main_slider(
            slider_id_uuid=self.variables.slider_id_uuid,
            default_val_slider=self.variables.default_val_slider,
        )
        tab1_results.initialize_main_selectbox(
            selectbox_id_uuid=self.variables.selectbox_id_uuid,
            default_value="None",
        )

        # Define callbacks for plot options
        def render_slider():
            tab1_results.generate_main_slider(
                slider_id_uuid=self.variables.slider_id_uuid,
                description_slider_md=self.variables.description_slider_md,
                default_val_slider=self.variables.default_val_slider,
            )

        def render_selectbox():
            tab1_results.generate_main_selectbox(self.variables, selectbox_id_uuid=self.variables.selectbox_id_uuid)

        # Store metric in a container to share between callbacks
        metric_container = {"metric": None}

        def render_metric_selector():
            metric = tab1_results.display_metric_selector(self.variables)
            metric_container["metric"] = metric
            return metric

        def render_mode_selector():
            # ROC-AUC has no mode variants (it's already species-aware by design)
            if metric_container["metric"] == "ROC-AUC":
                return None
            else:
                return tab1_results.display_metric_calc_approach_selector(self.variables)

        def render_colorblind_selector():
            return tab1_results.display_colorblindmode_selector(self.variables)

        # Render plot options expander and capture return values
        results = self.render_plot_options_expander(
            filter_callbacks=[render_slider, render_selectbox],
            selector_callbacks=[render_metric_selector, render_mode_selector, render_colorblind_selector],
            filter_cols_spec=2,
            selector_cols_spec=[1, 1, 1, 1],
        )

        # Extract returned values
        metric = results[2] if len(results) > 2 else "Median"
        mode = results[3] if len(results) > 3 else "Global"
        colorblind_mode = results[4] if len(results) > 4 else False

        tab1_results.display_existing_results(
            variables=self.variables,
            ionmodule=self.ionmodule,
            plot_params={
                "metric": metric,
                "mode": mode,
                "colorblind_mode": colorblind_mode,
                "label": st.session_state.get(st.session_state.get(self.variables.selectbox_id_uuid, ""), "None"),
            },
        )

    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")
        tab4_display_results_submitted.initialize_submitted_slider(
            self.variables.slider_id_submitted_uuid,
            self.variables.default_val_slider,
        )
        tab4_display_results_submitted.generate_submitted_slider(self.variables)
        tab4_display_results_submitted.generate_submitted_selectbox(self.variables)

        # Get current selections from session state
        label = st.session_state.get(st.session_state.get(self.variables.selectbox_id_submitted_uuid, ""), "None")

        tab4_display_results_submitted.display_submitted_results(
            variables=self.variables,
            ionmodule=self.ionmodule,
            plot_params={
                "metric": "Median",  # Default for submitted results
                "mode": "Global",  # Default for submitted results
                "colorblind_mode": False,
                "label": label,
            },
        )

    def display_workflow_comparison(self) -> None:
        """Display the workflow comparison tab."""
        tab_compare_workflows.display_workflow_comparison(
            variables=self.variables,
            ionmodule=self.ionmodule,
        )
