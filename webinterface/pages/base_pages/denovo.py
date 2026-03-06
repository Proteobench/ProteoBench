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
from pages.pages_variables.DeNovo.DDA_HCD_variables import VariablesDDADeNovo
from streamlit_extras.let_it_rain import rain

from proteobench.exceptions import DatasetAlreadyExistsOnServerError
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.io.parsing.utils import add_maxquant_fixed_modifications
from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule as IonModule
from proteobench.utils.server_io import dataset_folder_exists

from .base import BaseUIModule
from .tabs import tab1_view_public_results as tab1
from .tabs import tab2_upload_results as tab2
from .tabs import tab2_upload_results as tab2_quant
from .tabs import tab4_view_public_and_new_results as tab4
from .tabs import tab5_compare_results
from .tabs import tab6_submit_results as tab5_quant

logger: logging.Logger = logging.getLogger(__name__)


class DeNovoUIObjects(BaseUIModule):
    """
    Main class for the Streamlit interface of ProteoBench de novo identification.
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
        variables: VariablesDDADeNovo,
        ionmodule: IonModule,
        parsesettingsbuilder: ParseSettingsBuilder,
        page_name: str = "/",
    ) -> None:
        """
        Initialize the Streamlit UI objects for the de novo modules.

        Parameters
        ----------
        variables : VariablesDDADeNovo
            The variables for the de novo module.
        ionmodule : IonModule
            The de novo module.
        parsesettingsbuilder : ParseSettingsBuilder
            The parse settings builder.
        """
        super().__init__(
            variables=variables, ionmodule=ionmodule, parsesettingsbuilder=parsesettingsbuilder, page_name=page_name
        )

        # Specific to the 'de novo' module.
        self.level_mapping = {"Precision": "precision", "Recall": "recall"}
        self.level_mapping_submitted = {"Precision": "precision", "Recall": "recall"}
        self.evaluation_type_mapping = {"Exact": "exact", "Mass-based": "mass"}

    @st.fragment
    def display_all_data_results_main(self):
        """Display the results for all data in Tab 1."""
        st.title("Results (All Data)")

        # Initialize selectbox
        tab1.initialize_main_selectbox(
            selectbox_id_uuid=self.variables.selectbox_id_uuid,
            default_value="None",
        )

        # Radio for level (Precision or Recall)
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_level_id_uuid, default_value=self.variables.default_level
        )

        # Radio for evaluation type (Exact or Mass-Based)
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_evaluation_id_uuid, default_value=self.variables.default_evaluation
        )

        # Define callbacks for plot options
        def render_selectbox():
            tab1.generate_main_selectbox(self.variables, selectbox_id_uuid=self.variables.selectbox_id_uuid)

        def render_level_radio():
            tab1.generate_main_radio(
                radio_id_uuid=self.variables.radio_level_id_uuid,
                description="Select the classification metric",
                options=["Precision", "Recall"],
                help=self.variables.texts.Help.radio_level,
            )

        def render_evaluation_radio():
            tab1.generate_main_radio(
                radio_id_uuid=self.variables.radio_evaluation_id_uuid,
                description="Select the stringency of evaluation",
                options=["Exact", "Mass-based"],
                help=self.variables.texts.Help.radio_evaluation,
            )

        def render_colorblind_selector():
            return tab1.display_colorblindmode_selector(self.variables)

        # Render plot options expander
        results = self.render_plot_options_expander(
            filter_callbacks=[render_selectbox],
            selector_callbacks=[render_level_radio, render_evaluation_radio, render_colorblind_selector],
            filter_cols_spec=1,
            selector_cols_spec=[1, 1, 1, 1],
        )

        # Extract colorblind mode from results
        colorblind_mode = results[3] if len(results) > 3 else False

        tab1.display_existing_results(
            variables=self.variables,
            ionmodule=self.ionmodule,
            plot_params={
                "label": st.session_state.get(st.session_state.get(self.variables.selectbox_id_uuid, ""), "None"),
                "level": self.level_mapping[
                    st.session_state.get(st.session_state.get(self.variables.radio_level_id_uuid, ""), "Precision")
                ],
                "evaluation_type": self.evaluation_type_mapping[
                    st.session_state.get(st.session_state.get(self.variables.radio_evaluation_id_uuid, ""), "Exact")
                ],
                "colorblind_mode": colorblind_mode,
            },
            use_slider=False,
        )

    def display_submission_form(self) -> None:
        """Create the main submission form for the Streamlit UI in Tab 2."""
        # Display software selector and AlphaDIA info outside the form so it updates immediately
        tab2_quant.show_software_selector_and_alphadia_info(
            variables=self.variables,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
        )
        with st.form(key="main_form"):
            tab2_quant.generate_input_fields(
                user_input=self.user_input,
            )
            # TODO: Investigate the necessity of generating additional parameters fields in the first tab.
            tab2_quant.generate_additional_parameters_fields(
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
            st.info("Calculating metrics. This will take around two minutes. Please be patient.")
            self.first_point_plotted = tab2.process_submission_form(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )

    # Almost entirely unique to denovo module
    def display_indepth_plots(self) -> None:
        """
        Display the dataset selection dropdown and plot the selected dataset (Tab 3).
        """
        if self.variables.all_datapoints_submitted not in st.session_state:
            tab2.initialize_main_data_points(variables=self.variables, ionmodule=self.ionmodule)
            st.session_state[self.variables.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables.all_datapoints]
            )

        if self.variables.all_datapoints_submitted not in st.session_state.keys():
            st.error("No data available for plotting.", icon="🚨")
            return
        if st.session_state[self.variables.all_datapoints_submitted].empty:
            st.error("No data available for plotting.", icon="🚨")
            return
        downloads_df = st.session_state[self.variables.all_datapoints_submitted][["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        if self.variables.placeholder_dataset_selection_container not in st.session_state.keys():
            st.session_state[self.variables.placeholder_dataset_selection_container] = st.empty()
            st.session_state[self.variables.dataset_selector_id_uuid] = uuid.uuid4()

        st.subheader("Select dataset to plot")

        dataset_options = [("Uploaded dataset", None)] + list(
            zip(downloads_df["id"], downloads_df["intermediate_hash"])
        )

        dataset_selection = st.multiselect(
            label="Select datasets",
            options=dataset_options,
            key=st.session_state[self.variables.dataset_selector_id_uuid],
            format_func=lambda x: x[0],
            default=[dataset_options[0]],
            help=self.variables.texts.Help.dataset_selection_indepth,
        )

        # Use default values for plot rendering (no user controls on this tab)
        level = "precision"
        evaluation_type = "exact"
        colorblind_mode = False

        modifications = [
            "M-Oxidation",
            "Q-Deamidation",
            "N-Deamidation",
            "N-term Acetylation",
            "N-term Carbamylation",
            "N-term Ammonia-loss",
        ]
        feature_names = ["Missing Fragmentation Sites", "Peptide Length", "% Explained Intensity"]

        # Handle dataset selection - separate uploaded data from public data
        all_datapoints_df = st.session_state[self.variables.all_datapoints_submitted]
        selected_dtps = pd.DataFrame()

        for dtp_id, dtp_hash in dataset_selection:
            if dtp_hash is None:  # "Uploaded dataset" case
                # Get the newly uploaded data (marked as "new")
                uploaded_data = all_datapoints_df[all_datapoints_df["old_new"] == "new"]
                selected_dtps = pd.concat([selected_dtps, uploaded_data], ignore_index=True)
            else:
                # Get public dataset by hash
                public_data = all_datapoints_df[all_datapoints_df["intermediate_hash"] == dtp_hash]
                selected_dtps = pd.concat([selected_dtps, public_data], ignore_index=True)

        # Generate in-depth plots using plot generator
        if not selected_dtps.empty:
            plot_generator = self.ionmodule.get_plot_generator()

            # Create kwargs with De Novo-specific parameters (now using user selections)
            plot_kwargs = {
                "mod_labels": modifications,
                "feature": feature_names[0] if feature_names else "Missing Fragmentation Sites",
                "level": level,
                "evaluation_type": evaluation_type,
                "colorblind_mode": colorblind_mode,
            }

            try:
                # Generate all plots
                plots = plot_generator.generate_in_depth_plots(selected_dtps, **plot_kwargs)

                # Display plots using layout from plot generator
                layout = plot_generator.get_in_depth_plot_layout()
                descriptions = plot_generator.get_in_depth_plot_descriptions()

                for section in layout:
                    st.subheader(section.get("title", ""))
                    cols = st.columns(section.get("columns", 1))
                    for idx, plot_name in enumerate(section["plots"]):
                        with cols[idx % len(cols)]:
                            if plot_name in plots:
                                st.plotly_chart(plots[plot_name], use_container_width=True)
                                if plot_name in descriptions:
                                    st.caption(descriptions[plot_name])
            except Exception as e:
                st.error(f"Error generating in-depth plots: {e}", icon="🚨")
                import traceback

                with st.expander("Error details"):
                    st.code(traceback.format_exc())
        else:
            st.info("No datasets selected for plotting.")

    @st.fragment
    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")

        # Initialize selectbox
        tab1.initialize_main_selectbox(
            selectbox_id_uuid=self.variables.selectbox_id_submitted_uuid,
            default_value="None",
        )

        # Radio one for precision or recall
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_level_id_submitted_uuid, default_value=self.variables.default_level
        )

        # Radio two for evaluation stringency
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_evaluation_id_submitted_uuid,
            default_value=self.variables.default_evaluation,
        )

        # Define callbacks for plot options
        def render_selectbox():
            tab1.generate_main_selectbox(
                variables=self.variables, selectbox_id_uuid=self.variables.selectbox_id_submitted_uuid
            )

        def render_level_radio():
            tab1.generate_main_radio(
                radio_id_uuid=self.variables.radio_level_id_submitted_uuid,
                description="Select the classification metric",
                options=["Precision", "Recall"],
                help=self.variables.texts.Help.radio_level,
            )

        def render_evaluation_radio():
            tab1.generate_main_radio(
                radio_id_uuid=self.variables.radio_evaluation_id_submitted_uuid,
                description="Select the stringency of evaluation",
                options=["Exact", "Mass-based"],
                help=self.variables.texts.Help.radio_evaluation,
            )

        def render_colorblind_selector():
            return tab1.display_colorblindmode_selector(self.variables, use_submitted=True)

        # Render plot options expander
        results = self.render_plot_options_expander(
            filter_callbacks=[render_selectbox],
            selector_callbacks=[render_level_radio, render_evaluation_radio, render_colorblind_selector],
            filter_cols_spec=1,
            selector_cols_spec=[1, 1, 1, 1],
        )

        # Extract colorblind mode from results
        colorblind_mode = results[3] if len(results) > 3 else False

        # Get current selections from session state
        label = st.session_state.get(st.session_state.get(self.variables.selectbox_id_submitted_uuid, ""), "None")
        level = self.level_mapping[
            st.session_state.get(st.session_state.get(self.variables.radio_level_id_submitted_uuid, ""), "Precision")
        ]
        evaluation_type = self.evaluation_type_mapping[
            st.session_state.get(st.session_state.get(self.variables.radio_evaluation_id_submitted_uuid, ""), "Exact")
        ]

        # Plot the datapoints
        tab4.display_submitted_results(
            self.variables,
            self.ionmodule,
            plot_params={
                "label": label,
                "level": level,
                "evaluation_type": evaluation_type,
                "colorblind_mode": colorblind_mode,
            },
        )
        st.session_state[self.variables.table_id_uuid] = uuid.uuid4()
        st.data_editor(
            st.session_state[self.variables.all_datapoints_submitted],
            key=st.session_state[self.variables.table_id_uuid],
            on_change=self._handle_submitted_table_edits,
        )

        st.title("Public submission")
        st.markdown(
            "If you want to make this point — and the associated data — publicly available, please go to “Public Submission"
        )

    def display_workflow_comparison(self) -> None:
        """Display the workflow comparison tab."""
        tab5_compare_results.display_workflow_comparison(
            variables=self.variables,
            ionmodule=self.ionmodule,
        )

    def display_public_submission_ui(self) -> None:
        """Display the public submission section of the page in Tab 5."""
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
            self.submission_ready = tab5_quant.generate_submission_ui_elements(
                variables=self.variables,
                user_input=self.user_input,
            )

        if self.user_input[self.variables.meta_data]:
            params = tab5_quant.load_user_parameters(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )
            st.session_state[self.variables.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)

            tab5_quant.generate_additional_parameters_fields_submission(
                variables=self.variables,
                user_input=self.user_input,
            )
            tab5_quant.generate_comments_section(
                variables=self.variables,
                user_input=self.user_input,
            )
            # ? stop_duplicating is not used?
            self.stop_duplicating = tab5_quant.generate_confirmation_checkbox(
                check_submission=self.variables.check_submission
            )
        else:
            params = None

        pr_url = None
        if st.session_state[self.variables.check_submission] and params is not None:
            get_form_values = tab5_quant.get_form_values(
                variables=self.variables,
            )
            params = ProteoBenchParameters(**get_form_values, filename=self.variables.additional_params_json)
            try:
                pr_url = tab5_quant.submit_to_repository(
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
            tab5_quant.show_submission_success_message(
                variables=self.variables,
                pr_url=pr_url,
            )

    #####################
    ### TAB 4 METHODS ###
    #####################
    def _handle_submitted_table_edits(self) -> None:
        """Callback function for handling edits made to the data table in the UI."""
        edits = st.session_state[st.session_state[self.variables.table_id_uuid]]["edited_rows"].items()
        for k, v in edits:
            try:
                st.session_state[self.variables.all_datapoints_submitted][list(v.keys())[0]].iloc[k] = list(v.values())[
                    0
                ]
            except TypeError:
                return
        st.session_state[self.variables.highlight_list_submitted] = list(
            st.session_state[self.variables.all_datapoints_submitted]["Highlight"]
        )
        st.session_state[self.variables.placeholder_table] = st.session_state[self.variables.all_datapoints_submitted]

        if len(st.session_state[self.variables.all_datapoints]) == 0:
            st.error("No datapoints available for plotting", icon="🚨")

        try:
            # Get plot generator from module (following Quant pattern)
            plot_generator = self.ionmodule.get_plot_generator()

            # Get colorblind mode from session state
            colorblind_key = self.variables.colorblind_mode_selector_uuid
            if colorblind_key in st.session_state:
                colorblind_mode_id = st.session_state[colorblind_key]
                colorblind_mode = st.session_state.get(colorblind_mode_id, False)
            else:
                colorblind_mode = False

            fig_metric = plot_generator.plot_main_metric(
                result_df=st.session_state[self.variables.all_datapoints],
                hide_annot=False,
                label=st.session_state[st.session_state[self.variables.selectbox_id_uuid]],
                level=self.level_mapping[st.session_state[st.session_state[self.variables.radio_level_id_uuid]]],
                evaluation_type=self.evaluation_type_mapping[
                    st.session_state[st.session_state[self.variables.radio_evaluation_id_uuid]]
                ],
                colorblind_mode=colorblind_mode,
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables.fig_metric] = fig_metric
