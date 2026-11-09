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

from pages.utils.submission_source import get_submission_source, is_official_server

from proteobench.exceptions import DatasetAlreadyExistsOnServerError
from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.io.parsing.utils import add_maxquant_fixed_modifications
from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule as IonModule
from proteobench.utils.server_io import dataset_folder_exists

from proteobench.plotting.plot_generator_denovo import (
    SELECTION_PRESETS,
    classify_datapoint_columns,
    ordered_datapoint_columns,
    preset_selection,
)

from .base import BaseUIModule
from .tabs import tab1_view_public_results as tab1
from .utils.denovo_resulttable import (
    header_for,
    render_denovo_result_table,
    selection_summary,
)
from .utils.general import clean_dataframe_for_export
from .tabs import tab2_upload_results as tab2
from .tabs import tab2_upload_results as tab2_quant
from .tabs import tab4_view_public_and_new_results as tab4
from .tabs import tab5_compare_results
from .tabs import tab6_submit_results as tab5_quant

logger: logging.Logger = logging.getLogger(__name__)

#: What each of the two main views shows. Written for whoever is reading the figures rather
#: than, as it first was, about why the switcher is not ``st.tabs``.
FIGURE_VIEW_HELP = (
    "Scatter: one mark per run, its peptide-level score against its amino-acid-level score. "
    "Precision-Coverage Curves: the whole precision-against-coverage trade-off that each of "
    "those marks summarises down to a single point."
)

#: Shown under the Benchmark Results heading on both results tabs.
TABLE_CAPTION = (
    "One row per datapoint, grouped by tool and best first within each tool. Every datapoint is "
    "drawn by default; a star marks each tool's best \u2014 the same star the scatter draws that "
    "datapoint with \u2014 which is the one drawn at full strength while its tool's other runs are "
    "faded behind it. The Parameters column names what separates a tool's own runs; it is also "
    "the line under the name in every hover box. Untick a row to drop it from the figures, or "
    "use the buttons above the table. Click any column header to re-sort."
)

#: The ranking rule, stated wherever a rank, a star or a full-strength mark is on screen. It had
#: been a clause inside a long caption and a column tooltip, neither of which answers the
#: question the star raises. The "fixed" half matters as much as the formula: a reader who has
#: just switched the figure to Precision has every reason to expect the ranking to have followed.
RANKING_NOTE = (
    "**Rank and ★ are decided by mean AUC** — the average of a run's peptide-level and "
    "amino-acid-level AUC — compared only against other submissions of the same tool. That rule "
    "is fixed: it never follows the metric a figure happens to be showing, so switching between "
    "Precision and AUC does not move the star. Only the evaluation stringency (Exact / "
    "Mass-based) re-ranks."
)


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
        self.level_mapping = {"Precision": "precision", "AUC": "auc"}
        self.level_mapping_submitted = {"Precision": "precision", "AUC": "auc"}
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

        # Radio for level (Precision or AUC)
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_level_id_uuid, default_value=self.variables.default_level
        )

        # Radio for evaluation type (Exact or Mass-Based)
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_evaluation_id_uuid, default_value=self.variables.default_evaluation
        )

        def current_evaluation_type() -> str:
            evaluation_choice = st.session_state.get(
                st.session_state.get(self.variables.radio_evaluation_id_uuid, ""), self.variables.default_evaluation
            )
            return self.evaluation_type_mapping[evaluation_choice]

        # Define callbacks for plot options
        def render_selectbox():
            tab1.generate_main_selectbox(self.variables, selectbox_id_uuid=self.variables.selectbox_id_uuid)

        def render_level_radio():
            tab1.generate_main_radio(
                radio_id_uuid=self.variables.radio_level_id_uuid,
                description="Select the classification metric",
                options=["Precision", "AUC"],
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

        def render_il_toggle():
            is_mass_mode = current_evaluation_type() == "mass"
            return tab1.generate_forced_toggle(
                toggle_id_uuid=self.variables.il_toggle_id_uuid,
                label="Allow I/L mismatches",
                default=True,
                force_value=True if is_mass_mode else None,
                help=self.variables.texts.Help.toggle_il,
            )

        def render_deamidation_toggle():
            is_mass_mode = current_evaluation_type() == "mass"
            return tab1.generate_forced_toggle(
                toggle_id_uuid=self.variables.deamidation_toggle_id_uuid,
                label="Allow deamidation mismatches (Q↔E, N↔D)",
                default=False,
                force_value=True if is_mass_mode else None,
                help=self.variables.texts.Help.toggle_deamidation,
            )

        # Render plot options expander
        results = self.render_plot_options_expander(
            filter_callbacks=[render_selectbox],
            selector_callbacks=[
                render_level_radio,
                render_evaluation_radio,
                render_colorblind_selector,
                render_il_toggle,
                render_deamidation_toggle,
            ],
            filter_cols_spec=1,
            selector_cols_spec=[1, 1, 1, 1, 1],
        )

        # Extract toggle values from results (index 0 is the filter/selectbox callback,
        # which returns None; indices 1-5 are the selector callbacks in the order above).
        colorblind_mode = results[3] if len(results) > 3 else False
        allow_il = results[4] if len(results) > 4 else True
        allow_deamidation = results[5] if len(results) > 5 else False
        evaluation_type = self.evaluation_type_mapping[
            st.session_state.get(st.session_state.get(self.variables.radio_evaluation_id_uuid, ""), "Exact")
        ]

        filtered_data = tab1.load_and_filter_main_data(
            variables=self.variables, ionmodule=self.ionmodule, use_slider=False
        )

        if filtered_data.empty:
            st.info("No results available yet.", icon="ℹ️")
            return

        plot_params = {
            "label": st.session_state.get(st.session_state.get(self.variables.selectbox_id_uuid, ""), "None"),
            "level": self.level_mapping[
                st.session_state.get(st.session_state.get(self.variables.radio_level_id_uuid, ""), "Precision")
            ],
            "evaluation_type": evaluation_type,
            "allow_il": allow_il,
            "allow_deamidation": allow_deamidation,
            "colorblind_mode": colorblind_mode,
            "alpha_warning": getattr(self.variables, "alpha_warning", False),
            "beta_warning": getattr(self.variables, "beta_warning", False),
            "archived_warning": getattr(self.variables, "archived_warning", False),
        }

        # How datapoints are named and emphasised, shared by both figures and the table below so
        # the three always tell the same story about the same selection.
        prefix = self._denovo_state_prefix()
        display = self._render_denovo_display_controls(filtered_data, prefix)
        selection = self._denovo_selection(prefix, filtered_data)

        # A segmented control rather than st.tabs: it reads as a tab strip but builds only the
        # figure on screen. The results table below is shared and stays visible either way.
        view = st.segmented_control(
            "View",
            options=self.FIGURE_VIEWS,
            default=self.FIGURE_VIEWS[0],
            key=f"{prefix}_figure_view",
            label_visibility="collapsed",
            help=FIGURE_VIEW_HELP,
        )
        if view != self.FIGURE_VIEWS[1]:
            self._render_denovo_scatter(
                filtered_data=filtered_data,
                plot_params={**plot_params, **display, **selection},
                prefix=prefix,
                fig_key=self.variables.fig_metric,
            )
        else:
            self._display_precision_coverage_curves(
                filtered_data=filtered_data,
                evaluation_type=evaluation_type,
                allow_il=allow_il,
                allow_deamidation=allow_deamidation,
                fig_key_uuid=self.variables.fig_pc_curve,
                display=display,
                selection=selection,
            )

        st.subheader("Benchmark Results")
        st.info(RANKING_NOTE, icon=":material/trophy:")
        st.caption(TABLE_CAPTION)
        render_denovo_result_table(
            result_df=filtered_data,
            state_prefix=f"{prefix}_table",
            evaluation_type=evaluation_type,
            ambiguity_combo=self._ambiguity_combo(evaluation_type, allow_il, allow_deamidation),
            default_selection="all",
        )
        st.download_button(
            label="Download table",
            data=streamlit_utils.save_dataframe(clean_dataframe_for_export(filtered_data)),
            file_name="benchmark_results.csv",
            mime="text/csv",
            key=f"{prefix}_download_table",
            icon=":material/download:",
        )
        tab1.display_download_section(self.variables)

    #: The two main-figure views. A segmented control rather than ``st.tabs``: it reads like a
    #: tab strip, but Streamlit executes the body of every tab on every interaction, so real tabs
    #: would rebuild both figures on every click even though one of them is off screen.
    FIGURE_VIEWS = ("Scatter", "Precision-Coverage Curves")

    def _denovo_state_prefix(self, submitted: bool = False) -> str:
        """
        Session-state prefix for one view's display options.

        Parameters
        ----------
        submitted : bool
            Whether this is the submitted-results view, which keeps its own selection.

        Returns
        -------
        str
            A prefix unique to this module and view.
        """
        base = self.variables.fig_metric_submitted if submitted else self.variables.fig_metric
        return f"{base}_denovo_display"

    def _render_denovo_display_controls(self, filtered_data: pd.DataFrame, prefix: str) -> Dict[str, Any]:
        """
        Controls for how datapoints are identified and emphasised in the main-tab figures.

        Kept apart from the metric selectors in the plot-options expander: those choose *what* is
        measured, these choose how the measurements are labelled and which of them stand out.

        Parameters
        ----------
        filtered_data : pd.DataFrame
            The datapoints on display, used to populate the tool and column choices.
        prefix : str
            Session-state prefix for this view.

        Returns
        -------
        Dict[str, Any]
            Keyword arguments to forward to the de novo plot generator.
        """
        tools = sorted(filtered_data["software_name"].astype(str).unique())
        columns = ordered_datapoint_columns(classify_datapoint_columns(filtered_data))

        # A point click stages its tool here; apply it before the selectbox below is built, which
        # is the only moment its key may still be written.
        pending = st.session_state.pop(f"{prefix}_highlight_pending", None)
        if pending is not None and (pending == "None" or pending in tools):
            st.session_state[f"{prefix}_highlight_tool"] = pending

        with st.expander("Labels and emphasis", expanded=False):
            # No "name each datapoint by" control: a datapoint is always named by its tool and
            # rank, and what the run actually was is said separately -- under that name in the
            # hover box, and in the table's own Parameters column -- rather than being folded
            # into the name by a setting the reader had to find first.
            middle, right = st.columns(2)
            highlight_choice = middle.selectbox(
                "Highlight one tool",
                options=["None", *tools],
                key=f"{prefix}_highlight_tool",
                help="Brings every datapoint of that tool forward and dims the rest. Clicking a point does the same.",
            )
            muted_tools = right.multiselect(
                "Grey out tools",
                options=tools,
                key=f"{prefix}_muted_tools",
                help="Removes a tool's automatic colouring. Its datapoints stay on the plot in grey.",
            )

            hover_col, annot_col = st.columns(2)
            hover_columns = hover_col.multiselect(
                "Add to the hover box",
                options=columns,
                default=columns,
                format_func=header_for,
                key=f"{prefix}_hover_columns",
                help=(
                    "Every parameter is listed on hover to begin with. Remove the ones you are "
                    "not comparing to keep the box short enough to read at a glance."
                ),
            )
            annotation_columns = annot_col.multiselect(
                "Label on the plot",
                options=columns,
                format_func=header_for,
                key=f"{prefix}_annotation_columns",
                help="Drawn beside the coloured datapoints with leader lines. Gets crowded quickly.",
            )

            if st.button("Reset labels and emphasis", key=f"{prefix}_reset"):
                for suffix in (
                    "highlight_tool",
                    "muted_tools",
                    "hover_columns",
                    "annotation_columns",
                ):
                    st.session_state.pop(f"{prefix}_{suffix}", None)
                st.rerun()

        return {
            "highlight_tool": None if highlight_choice == "None" else highlight_choice,
            "muted_tools": muted_tools,
            "hover_columns": hover_columns,
            "annotation_columns": annotation_columns,
        }

    def _denovo_selection(self, prefix: str, filtered_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        The datapoint selection driving the figures, as kept by the result table.

        The figures are drawn above the table, so on the very first run the table has not written
        a selection yet. Seeding it here, with the same rule the table would have used, keeps the
        first paint agreeing with the ticks the reader can see; leaving it unseeded drew each
        tool's best above a table that said every row was shown.

        Parameters
        ----------
        prefix : str
            Session-state prefix for this view.
        filtered_data : pd.DataFrame, optional
            The datapoints on display, used to seed the selection on the first run.

        Returns
        -------
        Dict[str, Any]
            ``selected_ids`` and ``explicit_selection`` for the plot generator.
        """
        key = f"{prefix}_table_selected_ids"
        if key not in st.session_state:
            if filtered_data is None or "id" not in getattr(filtered_data, "columns", ()):
                return {"selected_ids": (), "explicit_selection": False}
            st.session_state[key] = {str(point_id) for point_id in filtered_data["id"]}
        return {"selected_ids": tuple(st.session_state[key]), "explicit_selection": True}

    def _render_denovo_scatter(
        self,
        filtered_data: pd.DataFrame,
        plot_params: Dict[str, Any],
        prefix: str,
        fig_key: str,
    ) -> None:
        """
        Render the main scatter and turn a click on a point into a highlighted tool.

        Streamlit exposes no hover event for Plotly, so the prototype's hover-to-highlight becomes
        click-to-highlight here: the clicked point's ProteoBench ID arrives through the selection
        payload as ``customdata``, and its tool is highlighted until clicked again.

        Parameters
        ----------
        filtered_data : pd.DataFrame
            The datapoints to plot.
        plot_params : Dict[str, Any]
            Parameters for the plot generator.
        prefix : str
            Session-state prefix for this view.
        fig_key : str
            Session-state key holding this figure's stable chart key.
        """
        if fig_key not in st.session_state:
            st.session_state[fig_key] = str(uuid.uuid4())

        try:
            fig = self.ionmodule.get_plot_generator().plot_main_metric(result_df=filtered_data, **plot_params)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user rather than crashing the tab
            st.error(f"Unable to plot the datapoints: {exc}", icon="🚨")
            return

        event = st.plotly_chart(
            fig,
            key=st.session_state[fig_key],
            on_select="rerun",
            selection_mode="points",
        )

        # A chart selection persists across reruns, so the same click is reported again on the
        # run this handler triggers. Acting on it unconditionally reruns forever; act only when
        # the selection actually changes.
        handled_key = f"{prefix}_handled_click"
        points = (getattr(event, "selection", None) or {}).get("points") or []

        if not points:
            # Plotly clears the selection when the selected point is clicked again. Only treat
            # that as "unhighlight" if the highlight came from a click, so a choice made in the
            # selectbox is left alone.
            if st.session_state.pop(handled_key, None) is not None:
                st.session_state[f"{prefix}_highlight_pending"] = "None"
                st.rerun()
            return

        custom = points[0].get("customdata")
        clicked_id = custom[0] if isinstance(custom, (list, tuple)) and custom else custom
        if clicked_id is None or st.session_state.get(handled_key) == str(clicked_id):
            return

        match = filtered_data[filtered_data["id"].astype(str) == str(clicked_id)]
        if match.empty:
            return

        # The "Highlight one tool" selectbox is built earlier in this same run, so its own key
        # can no longer be written. Stage the choice instead and let the control pick it up on
        # the next run, before it instantiates.
        st.session_state[handled_key] = str(clicked_id)
        st.session_state[f"{prefix}_highlight_pending"] = str(match.iloc[0]["software_name"])
        st.rerun()

    @staticmethod
    def _ambiguity_combo(evaluation_type: str, allow_il: bool, allow_deamidation: bool) -> Optional[str]:
        """
        The stored ambiguity key for the current toggle positions.

        Parameters
        ----------
        evaluation_type : str
            ``"mass"`` or ``"exact"``.
        allow_il : bool
            Whether I/L mismatches are allowed.
        allow_deamidation : bool
            Whether deamidation mismatches are allowed.

        Returns
        -------
        str or None
            The ambiguity key, or None for the baseline. Mass-mode metrics have no ambiguity
            variants, so the toggles are ignored there.
        """
        if evaluation_type != "exact":
            return None
        if allow_il and allow_deamidation:
            return "both"
        if allow_il:
            return "il"
        if allow_deamidation:
            return "deam"
        return None

    def _display_precision_coverage_curves(
        self,
        filtered_data: Optional[pd.DataFrame],
        evaluation_type: str,
        allow_il: bool,
        allow_deamidation: bool,
        fig_key_uuid: str,
        display: Optional[Dict[str, Any]] = None,
        selection: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Render the peptide-level/amino-acid-level precision-coverage curve view, sharing the
        same filtered dataset and evaluation/ambiguity selections as the scatter view in the
        adjacent tab.
        """
        if filtered_data is None or filtered_data.empty:
            st.info("No results available yet.", icon="ℹ️")
            return

        try:
            plot_generator = self.ionmodule.get_plot_generator()
            # The curve view takes the same colouring and labelling as the scatter, minus the
            # scatter-only options: there is no marker to annotate and no per-point hover box.
            curve_options = {
                key: value
                for key, value in (display or {}).items()
                if key in ("custom_labels", "highlight_tool", "muted_tools")
            }
            fig = plot_generator.plot_precision_coverage_curves(
                result_df=filtered_data,
                evaluation_type=evaluation_type,
                allow_il=allow_il,
                allow_deamidation=allow_deamidation,
                **curve_options,
                **(selection or {}),
            )
            if fig_key_uuid not in st.session_state:
                st.session_state[fig_key_uuid] = uuid.uuid4()
            st.plotly_chart(fig, key=st.session_state[fig_key_uuid])
        except Exception as e:
            st.error(f"Unable to plot the precision-coverage curves: {e}", icon="🚨")

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
            # Clear any previously uploaded parameter file and widget state so Tab 5
            # starts fresh for the new tool/file combination.
            st.session_state[self.variables.params_file_dict] = {}
            st.session_state.pop(self.variables.params_file_dict + "__seeded_for", None)
            # Erase the old file uploader's stored file before cycling the UUID,
            # so the uploader cannot resurrect the old file even if the key persists.
            _old_meta_uuid = st.session_state.get(self.variables.meta_file_uploader_uuid)
            if _old_meta_uuid is not None:
                st.session_state.pop(_old_meta_uuid, None)
            st.session_state[self.variables.meta_file_uploader_uuid] = uuid.uuid4()
            with open(self.variables.additional_params_json, encoding="utf-8") as f:
                _param_config = json.load(f)
            for _key in _param_config.keys():
                st.session_state.pop(self.variables.prefix_params + _key, None)

            st.info(
                "Calculating metrics for {}. This will take around two minutes. Please be patient.".format(
                    self.user_input["input_format"]
                )
            )
            self.first_point_plotted = tab2.process_submission_form(
                variables=self.variables,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )

    # Almost entirely unique to denovo module
    #: The in-depth views, as (key, menu label, sub-selection kind).
    INDEPTH_VIEWS = (
        ("ptm_overview", "PTM overview", None),
        ("ptm_specific", "PTM, one modification", "modification"),
        ("spectrum_feature", "Spectrum feature", "feature"),
        ("species_overview", "Species", None),
        ("in_fasta_overview", "In FASTA", None),
    )

    @st.fragment
    def display_indepth_plots(self) -> None:
        """
        Display one in-depth plot for a chosen set of datapoints (Tab 4, "Compare Results").

        A fragment, so ticking a datapoint re-runs only this tab rather than the whole page. One
        figure is drawn at a time: ``generate_in_depth_plots`` builds sixteen, of which only one
        is ever on screen, and Streamlit renders every tab's body on every run, so building them
        all cost roughly 250 ms and 700 KB per click for nothing.
        """
        if self.variables.all_datapoints_submitted not in st.session_state:
            tab2.initialize_main_data_points(variables=self.variables, ionmodule=self.ionmodule)
            st.session_state[self.variables.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables.all_datapoints]
            )

        all_datapoints_df = st.session_state.get(self.variables.all_datapoints_submitted)
        if all_datapoints_df is None or all_datapoints_df.empty:
            st.error("No data available for plotting.", icon="🚨")
            return

        prefix = f"{self.variables.fig_metric}_denovo_indepth"
        display = self._render_indepth_selection_controls(all_datapoints_df, prefix)

        preset_ids = display.pop("preset_ids", None)

        st.info(RANKING_NOTE, icon=":material/trophy:")

        # The table earns its space while a selection is being put together and costs several
        # hundred pixels between the controls and the figure they configure once it is settled,
        # so it folds away without giving up the selection it holds.
        show_table = st.toggle(
            "Show the datapoint table",
            value=True,
            key=f"{prefix}_show_table",
            help="Turn this off once your selection is set, to bring the figure up the page.",
        )
        if show_table:
            table = render_denovo_result_table(
                result_df=all_datapoints_df,
                state_prefix=f"{prefix}_table",
                evaluation_type=display["evaluation_type"],
                selected_ids=preset_ids,
            )
            selected_ids = table.selected_ids
        else:
            # The table owns the selection, so with it hidden a preset has to be written straight
            # to the key the table would have written it to.
            if preset_ids is not None:
                st.session_state[f"{prefix}_table_selected_ids"] = {str(point_id) for point_id in preset_ids}
            selected_ids = set(st.session_state.get(f"{prefix}_table_selected_ids", set()))
        st.caption(selection_summary(all_datapoints_df, selected_ids))

        selected = all_datapoints_df[all_datapoints_df["id"].astype(str).isin(selected_ids)]
        if selected.empty:
            st.info("No datapoints selected. Tick one in the table, or choose a preset above.")
            return

        st.divider()
        # Every view named on screen, rather than one name and a dropped arrow: there are five of
        # them, they are the whole point of this tab, and a reader should not have to open a menu
        # to discover what this tab can show.
        view_key = (
            st.segmented_control(
                "Plot",
                options=[key for key, _label, _sub in self.INDEPTH_VIEWS],
                format_func=lambda key: {k: label for k, label, _ in self.INDEPTH_VIEWS}[key],
                default=self.INDEPTH_VIEWS[0][0],
                key=f"{prefix}_view",
            )
            or self.INDEPTH_VIEWS[0][0]
        )
        sub_kind = {k: sub for k, _label, sub in self.INDEPTH_VIEWS}[view_key]
        sub_value = None
        if sub_kind is not None:
            sub_col = st.columns([1, 2])[0]
            if sub_kind == "modification":
                sub_value = sub_col.selectbox("Modification", options=self.PTM_LABELS, key=f"{prefix}_modification")
            else:
                sub_value = sub_col.selectbox("Feature", options=self.SPECTRUM_FEATURES, key=f"{prefix}_feature")

        self._render_indepth_figure(selected, display, view_key, sub_value)

    #: Where each in-depth view's full explanation lives on ``variables.texts.Description``.
    #: These are the several screens of method that the tabbed layout used to show beside each
    #: figure; the one-line entries in ``get_in_depth_plot_descriptions`` are a summary of them,
    #: not a replacement, so both are rendered.
    INDEPTH_DESCRIPTIONS = {
        "ptm_overview": "ptm_overview",
        "ptm_specific": "ptm_specific",
        "spectrum_feature": "spectrum_features_overview",
        "species_overview": "species",
        "in_fasta_overview": "in_fasta_overview",
    }

    #: Modifications scored by the de novo module, in display order.
    def _render_indepth_selection_controls(self, all_datapoints_df: pd.DataFrame, prefix: str) -> Dict[str, Any]:
        """
        Presets and labelling controls for the in-depth plots.

        Collapsed by default, with the current selection summarised beneath it, so the controls do
        not occupy the page once a selection is settled. The expander label is deliberately static:
        a label carrying a live count changes the element's props on every interaction and makes it
        collapse under the viewer.

        Parameters
        ----------
        all_datapoints_df : pd.DataFrame
            Every datapoint available to select from.
        prefix : str
            Session-state prefix for this view.

        Returns
        -------
        Dict[str, Any]
            The chosen evaluation type, label style, highlighted tool, and, when a preset was just
            applied, the ``preset_ids`` it resolved to.
        """
        tools = sorted(all_datapoints_df["software_name"].astype(str).unique())

        with st.expander("Selection and labels", expanded=False):
            st.caption(
                "Changing **Compare**, **Tool** or **How many** re-picks the selection "
                "immediately and replaces your ticks. Everything else here only changes how the "
                "figure is drawn and never touches which datapoints are in it."
            )
            preset_col, tool_col, topn_col = st.columns([1.1, 1, 1])
            preset = preset_col.radio(
                "Compare",
                options=SELECTION_PRESETS,
                format_func=lambda name: (
                    "Across tools (each tool's best)" if name == "cross_tool" else "Within one tool"
                ),
                key=f"{prefix}_preset",
                help=(
                    "Across tools is unbiased by how many times a tool was submitted. Within one "
                    "tool is the comparison that view deliberately hides."
                ),
            )
            tool_choice = tool_col.selectbox(
                "Tool",
                options=tools,
                key=f"{prefix}_preset_tool",
                disabled=preset != "tool_specific",
            )
            top_n = topn_col.selectbox(
                "How many",
                options=[10, 5, 0],
                format_func=lambda n: "All" if n == 0 else f"Top {n}",
                key=f"{prefix}_preset_topn",
                disabled=preset != "tool_specific",
            )

            eval_col, highlight_col = st.columns(2)
            evaluation_choice = eval_col.radio(
                "Evaluation",
                options=["Exact", "Mass-based"],
                index=1,
                key=f"{prefix}_evaluation",
                horizontal=True,
            )
            highlight_choice = highlight_col.selectbox(
                "Highlight",
                options=["None", *tools],
                key=f"{prefix}_highlight_tool",
                help=(
                    "Across tools this raises every datapoint of that software. Within one tool "
                    "every datapoint is that software, so raise one from the table instead."
                ),
            )

            if st.button(
                "Reset selection and labels",
                key=f"{prefix}_reset",
                icon=":material/restart_alt:",
                help="Clears your ticks and labels and goes back to the preset's own selection.",
            ):
                for suffix in (
                    "preset",
                    "preset_tool",
                    "preset_topn",
                    "preset_signature",
                    "highlight_tool",
                    "table_selected_ids",
                    "view",
                    "modification",
                    "feature",
                ):
                    st.session_state.pop(f"{prefix}_{suffix}", None)
                st.rerun()

        evaluation_type = self.evaluation_type_mapping[evaluation_choice]
        options: Dict[str, Any] = {
            "evaluation_type": evaluation_type,
            "highlight_tool": None if highlight_choice == "None" else highlight_choice,
        }

        # The preset applies the moment one of its own three controls moves, rather than on a
        # separate press: a block where some controls take effect immediately and others wait for
        # a button is what made this feel unpredictable. A hand-picked set is still never
        # replaced silently, because an unrelated rerun leaves the signature unchanged, and the
        # remaining controls here (evaluation, labels, emphasis) are not part of it.
        signature = (preset, tool_choice, int(top_n))
        signature_key = f"{prefix}_preset_signature"
        first_run = f"{prefix}_table_selected_ids" not in st.session_state
        if first_run or st.session_state.get(signature_key) != signature:
            st.session_state[signature_key] = signature
            options["preset_ids"] = preset_selection(
                all_datapoints_df,
                preset=preset,
                tool=tool_choice,
                top_n=int(top_n),
                evaluation_type=evaluation_type,
            )
        return options

    PTM_LABELS = (
        "M-Oxidation",
        "Q-Deamidation",
        "N-Deamidation",
        "N-term Acetylation",
        "N-term Carbamylation",
        "N-term Ammonia-loss",
    )

    #: Spectrum features scored by the de novo module.
    SPECTRUM_FEATURES = ("Missing Fragmentation Sites", "Peptide Length", "% Explained Intensity")

    def _render_indepth_description(self, plot_generator, view_key: str) -> None:
        """
        Render the one-line caption and the full explanation for an in-depth view.

        The caption summarises; the expander holds what each metric actually is and how to read
        the plot, which is the text the tabbed layout showed beside every figure and which the
        caption replaced rather than condensed.

        Parameters
        ----------
        plot_generator : object
            The module's plot generator, which supplies the short captions.
        view_key : str
            Which figure is on screen, a key of :data:`INDEPTH_VIEWS`.
        """
        descriptions = plot_generator.get_in_depth_plot_descriptions()
        if view_key in descriptions:
            st.caption(descriptions[view_key])

        attribute = self.INDEPTH_DESCRIPTIONS.get(view_key)
        detail = getattr(self.variables.texts.Description, attribute, None) if attribute else None
        if detail:
            with st.expander("What this plot shows, and how to read it", icon=":material/menu_book:"):
                st.markdown(detail)

    def _render_indepth_figure(
        self,
        selected: pd.DataFrame,
        display: Dict[str, Any],
        view_key: str,
        sub_value: Optional[str],
    ) -> None:
        """
        Build and draw the one in-depth figure currently chosen.

        Calls the individual plot method rather than ``generate_in_depth_plots``, which builds all
        sixteen figures. The orchestrator is still used by anything that wants the whole set, but
        a page that shows one figure should not pay for fifteen it will not display.

        Parameters
        ----------
        selected : pd.DataFrame
            The datapoints to plot.
        display : Dict[str, Any]
            Options from :meth:`_render_indepth_selection_controls`.
        view_key : str
            Which figure to build, a key of :data:`INDEPTH_VIEWS`.
        sub_value : str, optional
            The chosen modification or spectrum feature, where the view needs one.
        """
        plot_generator = self.ionmodule.get_plot_generator()
        evaluation_type = display["evaluation_type"]

        highlight_id = None
        highlight_tool = display.get("highlight_tool")
        if highlight_tool:
            matching = selected[selected["software_name"].astype(str) == str(highlight_tool)]
            if not matching.empty:
                highlight_id = str(matching.iloc[0]["id"])

        # Every datapoint is named by its tool and rank, here as everywhere else. What a run
        # was is carried by the table's Parameters column instead of by the name, so there is
        # nothing left for a naming control -- or for a hand-typed label -- to decide.
        identity = {
            "custom_labels": None,
            "highlight_id": highlight_id,
        }

        self._render_indepth_description(plot_generator, view_key)

        try:
            if view_key == "ptm_overview":
                fig = plot_generator.plot_ptm_overview(selected, mod_labels=list(self.PTM_LABELS), **identity)
            elif view_key == "ptm_specific":
                fig = plot_generator.plot_ptm_specific(selected, mod_label=sub_value, **identity)
            elif view_key == "spectrum_feature":
                fig = plot_generator.plot_spectrum_feature(
                    selected, feature=sub_value, evaluation_type=evaluation_type, **identity
                )
            elif view_key == "species_overview":
                fig = plot_generator.plot_species_overview(selected, evaluation_type=evaluation_type, **identity)
            else:
                fig = plot_generator.plot_infasta_overview(selected, **identity)
        except Exception as e:  # noqa: BLE001 - surfaced to the user rather than crashing the tab
            st.error(f"Error generating the in-depth plot: {e}", icon="🚨")
            import traceback

            with st.expander("Error details"):
                st.code(traceback.format_exc())
            return

        st.plotly_chart(fig, key=f"{self.variables.fig_metric}_indepth_{view_key}_{sub_value or 'none'}")

    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")

        # Initialize selectbox
        tab1.initialize_main_selectbox(
            selectbox_id_uuid=self.variables.selectbox_id_submitted_uuid,
            default_value="None",
        )

        # Radio one for precision or AUC
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_level_id_submitted_uuid, default_value=self.variables.default_level
        )

        # Radio two for evaluation stringency
        tab1.initialize_radio(
            radio_id_uuid=self.variables.radio_evaluation_id_submitted_uuid,
            default_value=self.variables.default_evaluation,
        )

        def current_evaluation_type() -> str:
            evaluation_choice = st.session_state.get(
                st.session_state.get(self.variables.radio_evaluation_id_submitted_uuid, ""),
                self.variables.default_evaluation,
            )
            return self.evaluation_type_mapping[evaluation_choice]

        # Define callbacks for plot options
        def render_selectbox():
            tab1.generate_main_selectbox(
                variables=self.variables, selectbox_id_uuid=self.variables.selectbox_id_submitted_uuid
            )

        def render_level_radio():
            tab1.generate_main_radio(
                radio_id_uuid=self.variables.radio_level_id_submitted_uuid,
                description="Select the classification metric",
                options=["Precision", "AUC"],
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

        def render_il_toggle():
            is_mass_mode = current_evaluation_type() == "mass"
            return tab1.generate_forced_toggle(
                toggle_id_uuid=self.variables.il_toggle_id_submitted_uuid,
                label="Allow I/L mismatches",
                default=True,
                force_value=True if is_mass_mode else None,
                help=self.variables.texts.Help.toggle_il,
            )

        def render_deamidation_toggle():
            is_mass_mode = current_evaluation_type() == "mass"
            return tab1.generate_forced_toggle(
                toggle_id_uuid=self.variables.deamidation_toggle_id_submitted_uuid,
                label="Allow deamidation mismatches (Q↔E, N↔D)",
                default=False,
                force_value=True if is_mass_mode else None,
                help=self.variables.texts.Help.toggle_deamidation,
            )

        # Render plot options expander
        results = self.render_plot_options_expander(
            filter_callbacks=[render_selectbox],
            selector_callbacks=[
                render_level_radio,
                render_evaluation_radio,
                render_colorblind_selector,
                render_il_toggle,
                render_deamidation_toggle,
            ],
            filter_cols_spec=1,
            selector_cols_spec=[1, 1, 1, 1, 1],
        )

        # Extract toggle values from results (index 0 is the filter/selectbox callback,
        # which returns None; indices 1-5 are the selector callbacks in the order above).
        colorblind_mode = results[3] if len(results) > 3 else False
        allow_il = results[4] if len(results) > 4 else True
        allow_deamidation = results[5] if len(results) > 5 else False

        # Get current selections from session state
        label = st.session_state.get(st.session_state.get(self.variables.selectbox_id_submitted_uuid, ""), "None")
        level = self.level_mapping[
            st.session_state.get(st.session_state.get(self.variables.radio_level_id_submitted_uuid, ""), "Precision")
        ]
        evaluation_type = self.evaluation_type_mapping[
            st.session_state.get(st.session_state.get(self.variables.radio_evaluation_id_submitted_uuid, ""), "Exact")
        ]

        # Load once, then only the figure switches between the two tabs below -- the
        # results table stays outside the switcher, visible regardless of which is selected.
        filtered_data = tab4.load_and_filter_submitted_data(variables=self.variables, ionmodule=self.ionmodule)

        plot_params = {
            "label": label,
            "level": level,
            "evaluation_type": evaluation_type,
            "allow_il": allow_il,
            "allow_deamidation": allow_deamidation,
            "colorblind_mode": colorblind_mode,
        }

        # Same labelling and emphasis controls as the public-results tab, with their own state so
        # the two views can be set up differently.
        prefix = self._denovo_state_prefix(submitted=True)
        display = self._render_denovo_display_controls(filtered_data, prefix)
        selection = self._denovo_selection(prefix, filtered_data)

        view = st.segmented_control(
            "View",
            options=self.FIGURE_VIEWS,
            default=self.FIGURE_VIEWS[0],
            key=f"{prefix}_figure_view",
            label_visibility="collapsed",
            help=FIGURE_VIEW_HELP,
        )
        if view != self.FIGURE_VIEWS[1]:
            self._render_denovo_scatter(
                filtered_data=filtered_data,
                plot_params={**plot_params, **display, **selection},
                prefix=prefix,
                fig_key=self.variables.fig_metric_submitted,
            )
        else:
            self._display_precision_coverage_curves(
                filtered_data=filtered_data,
                evaluation_type=evaluation_type,
                allow_il=allow_il,
                allow_deamidation=allow_deamidation,
                fig_key_uuid=self.variables.fig_pc_curve_submitted,
                display=display,
                selection=selection,
            )

        st.subheader("Benchmark Results")
        st.info(RANKING_NOTE, icon=":material/trophy:")
        st.caption(TABLE_CAPTION)
        render_denovo_result_table(
            result_df=filtered_data,
            state_prefix=f"{prefix}_table",
            evaluation_type=evaluation_type,
            ambiguity_combo=self._ambiguity_combo(evaluation_type, allow_il, allow_deamidation),
            default_selection="all",
        )

        # st.session_state[self.variables.table_id_uuid] = uuid.uuid4()
        # st.data_editor(
        #     st.session_state[self.variables.all_datapoints_submitted],
        #     key=st.session_state[self.variables.table_id_uuid],
        #     on_change=self._handle_submitted_table_edits,
        # )

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

        self.submission_ready = tab5_quant.generate_submission_ui_elements(
            variables=self.variables,
            user_input=self.user_input,
        )

        # Parse parameter file if uploaded so parsed values pre-populate the fields below.
        # If no file is provided the fields render with schema defaults for manual entry.
        #
        # The seeding below (both the parsed-file values and the schema-default fallback)
        # must run only once per uploaded file or tool switch, not on every rerun.
        # `display_public_submission_ui` is not an @st.fragment, so it reruns in full on
        # every widget interaction on the page, including the user editing one of the
        # parameter fields rendered below. Re-seeding unconditionally would overwrite that
        # edit with the originally parsed/default value before the widget is even redrawn,
        # since Streamlit ignores a widget's `value=` argument once its `key` already holds
        # a value in session state.
        uploaded_files = self.user_input[self.variables.meta_data]
        upload_fingerprint = tuple(sorted((f.name, f.size) for f in uploaded_files)) if uploaded_files else None
        seed_state_key = self.variables.params_file_dict + "__seeded_for"
        current_seed = (upload_fingerprint, self.user_input.get("input_format"))
        needs_seeding = st.session_state.get(seed_state_key) != current_seed

        if needs_seeding:
            if uploaded_files:
                params_from_file = tab5_quant.load_user_parameters(
                    variables=self.variables,
                    ionmodule=self.ionmodule,
                    user_input=self.user_input,
                )
            else:
                params_from_file = None

            if params_from_file is not None:
                st.session_state[self.variables.params_file_dict] = params_from_file.__dict__
                self.params_file_dict_copy = copy.deepcopy(params_from_file.__dict__)
                # Directly update widget session state keys so Streamlit uses the parsed values.
                # Without this, Streamlit ignores the `value` arg on widgets whose keys already exist
                # (registered from the pre-upload render of the always-visible fields).
                # Values must be sanitized: ProteoBenchParameters stores np.nan for missing fields,
                # which Streamlit cannot assign to a protobuf string field.
                for key, val in params_from_file.__dict__.items():
                    try:
                        is_missing = pd.isna(val)
                    except (TypeError, ValueError):
                        is_missing = False
                    if is_missing:
                        sanitized = None
                    elif not isinstance(val, str):
                        sanitized = str(val)
                    else:
                        sanitized = val
                    st.session_state[self.variables.prefix_params + key] = sanitized
            else:
                st.session_state[self.variables.params_file_dict] = {}
                self.params_file_dict_copy = {}

            # Write every parameter widget's session state to the desired starting value
            # (parsed value if available, otherwise the JSON schema default for the current
            # tool), for fields not covered above. Only runs as part of this seeding pass,
            # so it never clobbers a value the user has since typed into a field.
            with open(self.variables.additional_params_json, encoding="utf-8") as _schema_f:
                _param_schema = json.load(_schema_f)
            _file_dict = st.session_state.get(self.variables.params_file_dict, {})
            for _field_key, _field_schema in _param_schema.items():
                _is_checkbox = _field_schema.get("type") == "checkbox"
                if _field_key in _file_dict:
                    _val = _file_dict[_field_key]
                    if _is_checkbox:
                        # Checkbox fields (e.g. postprocessing_performed) carry a scalar bool
                        # default, not a dict — keep them as real bool, not a stringified one.
                        _val = bool(_val) if pd.notna(_val) else bool(_field_schema.get("value", False))
                    else:
                        # Sanitize: params_from_file.__dict__ may contain np.nan for missing fields.
                        # np.nan is a float and cannot be serialized by Streamlit's protobuf for
                        # text_input; convert to "" (empty). Non-string non-missing values are
                        # stringified to match what st.text_input expects.
                        try:
                            _is_missing = pd.isna(_val)
                        except (TypeError, ValueError):
                            _is_missing = False
                        if _is_missing:
                            _val = ""
                        elif not isinstance(_val, str):
                            _val = str(_val)
                    st.session_state[self.variables.prefix_params + _field_key] = _val
                else:
                    _schema_value = _field_schema.get("value")
                    if _is_checkbox:
                        _default = bool(_schema_value) if _schema_value is not None else False
                    else:
                        # Text-like fields store their per-tool default under "value" as a
                        # dict keyed by input_format (tool name); fall back to the schema
                        # value itself if it isn't a dict.
                        _default = (
                            _schema_value.get(self.user_input.get("input_format", ""), None)
                            if isinstance(_schema_value, dict)
                            else _schema_value
                        )
                        _default = _default if _default is not None else ""
                    st.session_state[self.variables.prefix_params + _field_key] = _default

            st.session_state[seed_state_key] = current_seed
        elif self.variables.params_file_dict not in st.session_state:
            st.session_state[self.variables.params_file_dict] = {}
            self.params_file_dict_copy = {}
        else:
            self.params_file_dict_copy = copy.deepcopy(st.session_state[self.variables.params_file_dict])

        # Always override software_name with the active input_format. This must come after
        # the parameter file re-application above, which does a full dict replacement and
        # would otherwise overwrite this value.
        st.session_state[self.variables.params_file_dict]["software_name"] = self.user_input["input_format"]

        # Always show parameter fields, comments, and confirmation checkbox.
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

        params = None
        pr_url = None
        if st.session_state[self.variables.check_submission]:
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

            # Get colorblind mode and ambiguity toggle states from session state
            colorblind_key = self.variables.colorblind_mode_selector_uuid
            if colorblind_key in st.session_state:
                colorblind_mode_id = st.session_state[colorblind_key]
                colorblind_mode = st.session_state.get(colorblind_mode_id, False)
            else:
                colorblind_mode = False

            il_key = self.variables.il_toggle_id_uuid
            allow_il = (
                st.session_state.get(st.session_state.get(il_key, ""), True) if il_key in st.session_state else True
            )

            deamidation_key = self.variables.deamidation_toggle_id_uuid
            allow_deamidation = (
                st.session_state.get(st.session_state.get(deamidation_key, ""), False)
                if deamidation_key in st.session_state
                else False
            )

            fig_metric = plot_generator.plot_main_metric(
                result_df=st.session_state[self.variables.all_datapoints],
                hide_annot=False,
                label=st.session_state[st.session_state[self.variables.selectbox_id_uuid]],
                level=self.level_mapping[st.session_state[st.session_state[self.variables.radio_level_id_uuid]]],
                evaluation_type=self.evaluation_type_mapping[
                    st.session_state[st.session_state[self.variables.radio_evaluation_id_uuid]]
                ],
                allow_il=allow_il,
                allow_deamidation=allow_deamidation,
                colorblind_mode=colorblind_mode,
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables.fig_metric] = fig_metric
