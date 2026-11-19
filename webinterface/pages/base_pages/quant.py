"""Streamlit-based web interface for ProteoBench."""

import copy
import logging
import uuid

import pandas as pd
import streamlit as st
from pages.pages_variables.base import VariablesBase

from pages.utils.submission_source import get_submission_source, is_official_server

from proteobench.exceptions import DatasetAlreadyExistsOnServerError
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_base_module import QuantModule as IonModule
from proteobench.utils.server_io import dataset_folder_exists

from .base import BaseUIModule
from .tabs import (
    tab1_view_public_results,
    tab2_upload_results,
    tab3_view_single_result,
    tab5_compare_results,
    tab6_submit_results,
)

logger: logging.Logger = logging.getLogger(__name__)


class QuantUIObjects(BaseUIModule):
    """Main class for the Streamlit interface of ProteoBench quantification.
    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.

    Parameters
    ----------
    variables : VariablesBase
        The variables for the quantification module.
    ionmodule : IonModule
        The quantification module.
    parsesettingsbuilder : ParseSettingsBuilder
        The parse settings builder.
    """

    def __init__(
        self,
        variables: VariablesBase,
        ionmodule: IonModule,
        parsesettingsbuilder: ParseSettingsBuilder,
        page_name: str = "/",
    ) -> None:
        """
        Initialize the Streamlit UI objects for the quantification modules.

        Parameters
        ----------
        variables : VariablesBase
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

    def get_tour_steps(self) -> list:
        """Return tour steps for this quantification module."""
        from pages.base_pages.tour_steps import get_quant_tour_steps

        return get_quant_tour_steps(module_name=getattr(self.variables, "title", "this module"))

    def display_submission_form(self) -> None:
        """Create the main submission form for the Streamlit UI in Tab 2."""
        # Display software selector and AlphaDIA info outside the form so it updates immediately
        tab2_upload_results.show_software_selector_and_alphadia_info(
            variables=self.variables,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
        )
        with st.container(key="tour_upload_form"):
            with st.form(key="main_form"):
                tab2_upload_results.generate_input_fields(
                    user_input=self.user_input,
                )
                # TODO: Investigate the necessity of generating additional parameters fields in the first tab.
                tab2_upload_results.generate_additional_parameters_fields(
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
            self.first_point_plotted = tab2_upload_results.process_submission_form(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )

    @st.fragment
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
        downloads_df = pd.DataFrame()
        if not df.empty:
            # st.error("No data available for plotting.", icon="🚨")
            # return
            downloads_df = df[["id", "intermediate_hash"]]
            downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        key_in_state = self.variables.placeholder_dataset_selection_container
        if key_in_state not in st.session_state.keys():
            st.session_state[key_in_state] = st.empty()
            key_in_state = self.variables.dataset_selector_id_uuid
            st.session_state[key_in_state] = uuid.uuid4()

        st.subheader("Select dataset to plot")

        if not downloads_df.empty:
            dataset_options = [("Uploaded dataset", None)] + list(zip(downloads_df["id"], downloads_df["intermediate_hash"]))
        else:
            dataset_options = [("Uploaded dataset", None)]

        with st.container(key="tour_dataset_selector"):
            dataset_selection = st.selectbox(
                "Select dataset",
                dataset_options,
                index=0,
                key=st.session_state[self.variables.dataset_selector_id_uuid],
                format_func=lambda x: x[0],
            )

        public_id, selected_hash = dataset_selection
        with st.container(key="tour_indepth_plots"):
            tab3_view_single_result.generate_indepth_plots(
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
        is_tour = st.session_state.get("_module_tour_in_progress", False)

        submission_source = get_submission_source()
        if not is_official_server():
            st.warning(
                "You are running ProteoBench locally. Submissions from local installs "
                "will be labeled as 'local' and will NOT be merged into the public dataset. "
                "To submit data for public inclusion, please use the official web server at "
                "https://proteobench.cubimed.rub.de/"
            )

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

        self.submission_ready = tab6_submit_results.generate_submission_ui_elements(
            variables=self.variables,
            user_input=self.user_input,
            parsesettingsbuilder=self.parsesettingsbuilder,
        )

        if self.user_input[self.variables.meta_data]:
            params = tab6_submit_results.load_user_parameters(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )
            st.session_state[self.variables.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)

            tab6_submit_results.generate_additional_parameters_fields_submission(
                variables=self.variables,
                user_input=self.user_input,
            )
            tab6_submit_results.generate_comments_section(
                variables=self.variables,
                user_input=self.user_input,
            )
            tab6_submit_results.generate_confirmation_checkbox(check_submission=self.variables.check_submission)
        elif is_tour:
            # Tour preview: render parameter fields with defaults so users can see the form.
            if self.variables.params_file_dict not in st.session_state:
                st.session_state[self.variables.params_file_dict] = {}
            self.user_input.setdefault(
                "input_format",
                st.session_state.get("software_tool_selector") or next(iter(self.parsesettingsbuilder.INPUT_FORMATS)),
            )
            st.info(
                "These fields are auto-filled when you upload a parameter file above. "
                "Shown here with default values as a preview.",
                icon="ℹ️",
            )
            tab6_submit_results.generate_additional_parameters_fields_submission(
                variables=self.variables,
                user_input=self.user_input,
            )
            return
        else:
            params = None

        pr_url = None
        if st.session_state[self.variables.check_submission] and params is not None:
            get_form_values = tab6_submit_results.get_form_values(
                variables=self.variables,
            )
            params = ProteoBenchParameters(**get_form_values, filename=self.variables.additional_params_json)
            try:
                pr_url = tab6_submit_results.submit_to_repository(
                    variables=self.variables,
                    ionmodule=self.ionmodule,
                    user_input=self.user_input,
                    params_from_file=self.params_file_dict_copy,
                    params=params,
                    submission_source=submission_source,
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
            tab6_submit_results.show_submission_success_message(
                variables=self.variables,
                pr_url=pr_url,
            )

    @st.fragment
    def display_all_data_results_main(self) -> None:
        """Display the results for all data in Tab 1."""
        self._display_results(submitted=False)

    @st.fragment
    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        self._display_results(submitted=True)

    def _display_results(self, submitted: bool) -> None:
        """
        Render the plot options, metric plot and results table for Tab 1 (public data) or,
        with ``submitted=True``, Tab 4 (public + new data). The two tabs use separate widget
        keys so their selections are independent.
        """
        v = self.variables
        slider_id = v.slider_id_submitted_uuid if submitted else v.slider_id_uuid
        selectbox_id = v.selectbox_id_submitted_uuid if submitted else v.selectbox_id_uuid
        tab = 4 if submitted else 1
        metric_key = f"_tab{tab}_metric_{v.sidebar_path}"
        mode_key = f"_tab{tab}_mode_{v.sidebar_path}"

        if submitted:
            st.title("Results (All Data)")

        tab1_view_public_results.initialize_main_slider(slider_id_uuid=slider_id, default_val_slider=v.default_val_slider)
        tab1_view_public_results.initialize_main_selectbox(selectbox_id_uuid=selectbox_id, default_value="None")
        st.session_state.setdefault(metric_key, "Median")
        st.session_state.setdefault(mode_key, "Species-weighted")

        def render_slider():
            tab1_view_public_results.generate_main_slider(
                slider_id_uuid=slider_id,
                description_slider_md=v.description_slider_md,
                default_val_slider=v.default_val_slider,
                max_nr_observed=getattr(v, "max_nr_observed", 6),
            )

        def render_selectbox():
            tab1_view_public_results.generate_main_selectbox(v, selectbox_id_uuid=selectbox_id)

        def render_metric_selector():
            return st.radio("Select metric", ["Median", "Mean"], key=metric_key, horizontal=True)

        def render_mode_selector():
            return st.radio(
                "Select metric calculation approach", ["Species-weighted", "Global"], key=mode_key, horizontal=True
            )

        def render_colorblind_selector():
            return tab1_view_public_results.display_colorblindmode_selector(v, use_submitted=submitted)

        _, _, metric, mode, colorblind_mode = self.render_plot_options_expander(
            filter_callbacks=[render_slider, render_selectbox],
            selector_callbacks=[render_metric_selector, render_mode_selector, render_colorblind_selector],
            filter_cols_spec=2,
            selector_cols_spec=[1, 1, 1],
            expander_key=None if submitted else "tour_plot_options",
        )

        tab1_view_public_results.display_existing_results(
            variables=v,
            ionmodule=self.ionmodule,
            plot_params={
                "metric": metric,
                "mode": mode,
                "colorblind_mode": colorblind_mode,
                "label": st.session_state.get(st.session_state.get(selectbox_id, ""), "None"),
                "min_nr_observed": st.session_state.get(st.session_state.get(slider_id)),
                "alpha_warning": getattr(v, "alpha_warning", False),
                "beta_warning": getattr(v, "beta_warning", False),
                "archived_warning": getattr(v, "archived_warning", False),
            },
            submitted=submitted,
        )

    def display_workflow_comparison(self) -> None:
        """Display the workflow comparison tab."""
        tab5_compare_results.display_workflow_comparison(
            variables=self.variables,
            ionmodule=self.ionmodule,
        )
