"""Streamlit-based web interface for ProteoBench."""

import copy
import logging
import uuid
from typing import Any, Dict

import pages.texts.proteobench_builder as pbb
import pandas as pd
import streamlit as st

from pages.pages_variables.Entrapment.Entrapment_DIA_ion_Astral_variables import (
    VariablesDIAEntrapmentAstral,
)
from proteobench.modules.entrapment.entrapment_ion_DIA_Astral import (
    DIAEntrapmentIonModuleAstral as IonModule,
)
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder

from proteobench.exceptions import DatasetAlreadyExistsOnServerError
from proteobench.github.gh import get_submission_source, is_official_server
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.entrapment.entrapment_ion_DIA_Astral import (
    DIAEntrapmentIonModuleAstral as IonModule,
)
from proteobench.utils.server_io import dataset_folder_exists

from .base import BaseUIModule
from .tabs_entrapment import (
    tab1_view_public_results,
    tab2_upload_results,
    tab3_view_single_result,
    tab4_view_public_and_new_results,
    tab6_submit_results,
)


class EntrapmentUIObjects(BaseUIModule):
    """Main class for the Streamlit interface of ProteoBench entrapment.
    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.

    Parameters
    ----------
    variables : VariablesDIAEntrapmentAstral
        The variables for the entrapment module.
    ionmodule : IonModule
        The entrapment module.
    parsesettingsbuilder : ParseSettingsBuilder
        The parse settings builder.
    """

    def __init__(
        self,
        variables: VariablesDIAEntrapmentAstral,
        ionmodule: IonModule,
        parsesettingsbuilder: ParseSettingsBuilder,
        page_name: str = "/",
    ) -> None:
        """
        Initialize the Streamlit UI objects for the entrapment modules.

        Parameters
        ----------
        variables : VariablesDIAEntrapment
            The variables for the entrapment module.
        ionmodule : IonModule
            The entrapment module.
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
        tab2_upload_results.show_software_selector_and_alphadia_info(
            variables=self.variables,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
        )
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
            dataset_options = [("Uploaded dataset", None)] + list(
                zip(downloads_df["id"], downloads_df["intermediate_hash"])
            )
        else:
            dataset_options = [("Uploaded dataset", None)]

        dataset_selection = st.selectbox(
            "Select dataset",
            dataset_options,
            index=0,
            key=st.session_state[self.variables.dataset_selector_id_uuid],
            format_func=lambda x: x[0],
        )

        public_id, selected_hash = dataset_selection

        # For the uploaded dataset, reuse the fdp_curve already computed during
        # benchmarking rather than recomputing it from the intermediate DataFrame.
        plot_kwargs = {}
        if public_id == "Uploaded dataset":
            all_dp = st.session_state.get(self.variables.all_datapoints)
            if all_dp is not None and not all_dp.empty and "fdp_curve" in all_dp.columns:
                new_rows = all_dp[all_dp.get("old_new", pd.Series()) == "new"] if "old_new" in all_dp.columns else pd.DataFrame()
                if not new_rows.empty:
                    candidate = new_rows.iloc[0]["fdp_curve"]
                    if isinstance(candidate, dict) and candidate:
                        plot_kwargs["fdp_curve"] = candidate

        tab3_view_single_result.generate_indepth_plots(
            module=self.ionmodule,
            variables=self.variables,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
            public_id=public_id,
            public_hash=selected_hash,
            **plot_kwargs,
        )

    def display_public_submission_ui(self) -> None:
        """
        Display the public submission section of the page in Tab 5.
        """
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

        if self.variables.first_new_plot:
            self.submission_ready = tab6_submit_results.generate_submission_ui_elements(
                variables=self.variables,
                user_input=self.user_input,
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
            # ? stop_duplicating is not used?
            self.stop_duplicating = tab6_submit_results.generate_confirmation_checkbox(
                check_submission=self.variables.check_submission
            )
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

    def _render_fdp_ratio_plot(self, session_key: str, metric: str, colorblind_mode: bool, is_public_only: bool = False) -> None:
        """Render the FDP / reported-FDR ratio plot from the given session-state key."""
        all_data = st.session_state.get(session_key)
        if all_data is None or not isinstance(all_data, pd.DataFrame):
            st.info("No data loaded yet — please wait for public results to load.", icon="ℹ️")
            return

        st.subheader("FDP / Reported FDR by Workflow")
        st.markdown(
            "Ratio of empirical false discovery proportion (FDP) to the FDR threshold "
            "declared for each workflow. A ratio ≤ 1 means the empirical FDP does not "
            "exceed the claimed FDR. Workflows are coloured by validity category: "
            ":green[valid] (upper bound ≤ reported FDR), "
            ":red[invalid] (lower bound > reported FDR), "
            ":orange[inconclusive] (lower bound ≤ reported FDR < upper bound). "
            "Newly uploaded results are shown with larger open markers (⬤)."
        )

        if is_public_only:
            submitted_key = self.variables.all_datapoints_submitted
            if submitted_key in st.session_state and isinstance(st.session_state[submitted_key], pd.DataFrame):
                new_df = st.session_state[submitted_key]
                if "old_new" in new_df.columns and (new_df["old_new"] == "new").any():
                    st.info(
                        "You have an uploaded result. Switch to **Tab 4 (View Public + New Results)** "
                        "to see it in this plot.",
                        icon="ℹ️",
                    )

        if all_data.empty:
            st.info("No datapoints available to plot.", icon="ℹ️")
            return

        if "old_new" in all_data.columns:
            new_rows = all_data[all_data["old_new"] == "new"]
            if not new_rows.empty and "reported_fdr_parsed_from_input" in new_rows.columns:
                fdr_vals = pd.to_numeric(new_rows["reported_fdr_parsed_from_input"], errors="coerce")
                missing = fdr_vals.isna() | (fdr_vals == 0)
                if missing.any():
                    st.warning(
                        "Your uploaded result has no FDR threshold set — the plot uses 0.01 as a fallback. "
                        "To see the correct ratio, re-upload and fill in the **FDR PSM** field in the form.",
                        icon="⚠️",
                    )

        try:
            fdp_ratio_fig = self.ionmodule.get_plot_generator().plot_fdp_ratio(
                all_data,
                metric=metric,
                colorblind_mode=colorblind_mode,
            )
            st.plotly_chart(fdp_ratio_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render FDP ratio plot: {e}", icon="🚨")

    def _render_category_strip(self, session_key: str) -> None:
        """Render the category strip plot from the given session-state key."""
        all_data = st.session_state.get(session_key)
        if all_data is None or not isinstance(all_data, pd.DataFrame) or all_data.empty:
            return

        st.subheader("Identified Features by Validity Category")
        st.markdown(
            "Points are grouped into the three validity categories based on the paired FDP bounds "
            "vs each workflow's declared PSM-level FDR. "
            "**Point colour** indicates the software tool. "
            "Within each category, points are spread horizontally for readability and sorted "
            "by number of identified features."
        )
        try:
            fig = self.ionmodule.get_plot_generator().plot_category_strip(all_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render category strip plot: {e}", icon="🚨")

    def _render_fdp_id_scatter(self, session_key: str) -> None:
        """Render the FDP/FDR ratio vs number of IDs scatter from the given session-state key."""
        all_data = st.session_state.get(session_key)
        if all_data is None or not isinstance(all_data, pd.DataFrame) or all_data.empty:
            return

        st.subheader("FDP/FDR Ratio vs Identified Features")
        st.markdown(
            "Each point is one submitted workflow. "
            "**Colour** indicates the software tool; **shape** indicates the validity category "
            "(○ valid, △ inconclusive, ✕ invalid). "
            "The x-axis shows the ratio of the paired upper FDP bound to the declared PSM-level FDR; "
            "a ratio below 1 (left of the dashed line) means the empirical FDP is within the claimed threshold."
        )
        try:
            fig = self.ionmodule.get_plot_generator().plot_fdp_id_scatter(all_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render FDP/FDR scatter: {e}", icon="🚨")

    def _render_forest_plot(self, session_key: str) -> None:
        """Render the FDP interval forest plot from the given session-state key."""
        all_data = st.session_state.get(session_key)
        if all_data is None or not isinstance(all_data, pd.DataFrame) or all_data.empty:
            return

        st.subheader("FDP Interval Plot")
        st.markdown(
            "Each row is one submitted workflow. The thick horizontal bar spans the FDP "
            "uncertainty interval from the **lower bound** (left) to the **paired upper bound** "
            "(right); open circles mark both endpoints. "
            "The diamond marker (◆) shows the workflow's declared FDR threshold "
            "(``reported_fdr_parsed_from_input``); a star (★) marks newly uploaded results. "
            "Bar colour indicates the validity category: "
            "**green** = valid, **orange** = inconclusive, **red** = invalid."
        )
        sort_dir = st.radio(
            "Sort by number of identified features",
            ["Ascending ↑", "Descending ↓"],
            index=1,
            horizontal=True,
            key=f"forest_sort_{session_key}",
        )
        sort_ascending = sort_dir.startswith("Ascending")
        try:
            fig = self.ionmodule.get_plot_generator().plot_forest(
                all_data,
                sort_ascending=sort_ascending,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render forest plot: {e}", icon="🚨")

    @st.fragment
    def display_all_data_results_main(self) -> None:
        """Display the results for all data in Tab 1."""
        tab1_view_public_results.initialize_main_selectbox(
            selectbox_id_uuid=self.variables.selectbox_id_uuid,
            default_value="None",
        )

        # Define callbacks for plot options
        def render_selectbox():
            tab1_view_public_results.generate_main_selectbox(
                self.variables, selectbox_id_uuid=self.variables.selectbox_id_uuid
            )

        # Store metric in a container to share between callbacks
        metric_container = {"metric": None}

        def render_metric_selector():
            metric = tab1_view_public_results.display_metric_selector(self.variables)
            metric_container["metric"] = metric
            return metric

        def render_colorblind_selector():
            return tab1_view_public_results.display_colorblindmode_selector(self.variables)

        # Render plot options expander and capture return values
        results = self.render_plot_options_expander(
            filter_callbacks=[render_selectbox],
            selector_callbacks=[render_metric_selector, render_colorblind_selector],
            filter_cols_spec=1,
            selector_cols_spec=[1, 1],
        )

        # Extract returned values
        metric = results[1] if len(results) > 1 else "Upper FDP bound - Paired method"
        colorblind_mode = results[2] if len(results) > 2 else False

        tab1_view_public_results.display_existing_results(
            variables=self.variables,
            ionmodule=self.ionmodule,
            plot_params={
                "metric": metric,
                "colorblind_mode": colorblind_mode,
                "label": st.session_state.get(st.session_state.get(self.variables.selectbox_id_uuid, ""), "None"),
                "alpha_warning": getattr(self.variables, "alpha_warning", False),
                "beta_warning": getattr(self.variables, "beta_warning", False),
            },
        )

        self._render_fdp_ratio_plot(
            session_key=self.variables.all_datapoints,
            metric=metric,
            colorblind_mode=colorblind_mode,
            is_public_only=True,
        )

        self._render_forest_plot(session_key=self.variables.all_datapoints)
        self._render_fdp_id_scatter(session_key=self.variables.all_datapoints)
        self._render_category_strip(session_key=self.variables.all_datapoints)

    @st.fragment
    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")

        # Initialize plot options controls (same as tab 1)
        tab1_view_public_results.initialize_main_selectbox(
            selectbox_id_uuid=self.variables.selectbox_id_submitted_uuid,
            default_value="None",
        )

        # Define callbacks for plot options
        def render_selectbox():
            tab1_view_public_results.generate_main_selectbox(
                self.variables,
                selectbox_id_uuid=self.variables.selectbox_id_submitted_uuid,
            )

        # Store metric in a container to share between callbacks
        metric_container = {"metric": None}

        def render_metric_selector():
            key = self.variables.metric_selector_submitted_uuid
            if key not in st.session_state:
                st.session_state[key] = uuid.uuid4()
            metric_uuid = st.session_state[key]

            help_text = (
                getattr(self.variables.texts.Help, "radio_metric", None) if hasattr(self.variables, "texts") else None
            )
            metric = st.radio(
                "Select metric to show in x axis",
                ["Lower FDP bound", "Upper FDP bound - Combined method", "Upper FDP bound - Paired method"],
                help=help_text,
                horizontal=True,
                key=metric_uuid,
            )
            metric_container["metric"] = metric
            return metric

        def render_colorblind_selector():
            return tab1_view_public_results.display_colorblindmode_selector(self.variables, use_submitted=True)

        # Render plot options expander and capture return values
        results = self.render_plot_options_expander(
            filter_callbacks=[render_selectbox],
            selector_callbacks=[render_metric_selector, render_colorblind_selector],
            filter_cols_spec=1,
            selector_cols_spec=[1, 1],
        )

        # Extract returned values
        metric = results[1] if len(results) > 1 else "Upper FDP bound - Paired method"
        colorblind_mode = results[2] if len(results) > 2 else False

        # Get current selections from session state
        label = st.session_state.get(st.session_state.get(self.variables.selectbox_id_submitted_uuid, ""), "None")

        tab4_view_public_and_new_results.display_submitted_results(
            variables=self.variables,
            ionmodule=self.ionmodule,
            plot_params={
                "metric": metric,
                "colorblind_mode": colorblind_mode,
                "label": label,
                "alpha_warning": getattr(self.variables, "alpha_warning", False),
                "beta_warning": getattr(self.variables, "beta_warning", False),
            },
        )

        self._render_fdp_ratio_plot(
            session_key=self.variables.all_datapoints_submitted,
            metric=metric,
            colorblind_mode=colorblind_mode,
        )

        self._render_forest_plot(session_key=self.variables.all_datapoints_submitted)
        self._render_fdp_id_scatter(session_key=self.variables.all_datapoints_submitted)
        self._render_category_strip(session_key=self.variables.all_datapoints_submitted)
