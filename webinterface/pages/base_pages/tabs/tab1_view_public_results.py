"""
Generic Tab 1 / Tab 4: Results Display (All Data, and Public + New Data)

This module provides a unified interface for displaying benchmark results
across all ProteoBench module types (Quant, De Novo, etc.). Tab 1 shows the
public datapoints; Tab 4 (``submitted=True``) shows the public datapoints plus
the user's new one, pinned through the parameter filters.
"""

import contextlib
import os
import traceback
import uuid
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st
import streamlit_utils

from ..utils.general import clean_dataframe_for_export
from ..utils.metricplot import render_metric_plot
from ..utils.parameter_filters import generate_parameter_filters
from ..utils.resulttable import add_open_source_column, configure_aggrid, prepare_display_dataframe, render_aggrid


def initialize_uuid_state(key: str, default_value: Any = None) -> None:
    """
    Initialize a UUID-based state key with an optional default value.

    Parameters
    ----------
    key : str
        The session state key to initialize.
    default_value : Any, optional
        The default value to associate with the generated UUID.
    """
    if key not in st.session_state:
        st.session_state[key] = uuid.uuid4()

    if default_value is not None:
        uuid_key = st.session_state[key]
        if uuid_key not in st.session_state:
            st.session_state[uuid_key] = default_value


def _data_key(variables, submitted: bool) -> str:
    """Session-state key holding the Tab 1 (public) or Tab 4 (public + new) datapoints."""
    return variables.all_datapoints_submitted if submitted else variables.all_datapoints


def initialize_main_data_points(variables, ionmodule, submitted: bool = False) -> None:
    """
    Load the datapoints into the session state if they are not there yet.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    ionmodule : object
        The module instance with obtain_all_data_points method.
    submitted : bool, optional
        If True, use the Tab 4 (public + new) key instead of the Tab 1 key.
    """
    key = _data_key(variables, submitted)
    if key not in st.session_state:
        st.session_state[key] = None
        st.session_state[key] = ionmodule.obtain_all_data_points(all_datapoints=st.session_state[key])


# UI Control Functions


def initialize_main_slider(slider_id_uuid: str, default_val_slider: int) -> None:
    """Initialize the slider state with UUID and default value."""
    initialize_uuid_state(slider_id_uuid, default_val_slider)


def generate_main_slider(
    slider_id_uuid: str, description_slider_md: str, default_val_slider: float, max_nr_observed: int = 6
) -> None:
    """
    Create a slider input.

    Parameters
    ----------
    slider_id_uuid : str
        UUID for the slider state key
    description_slider_md : str
        Path to markdown file with slider description
    default_val_slider : float
        Default value for the slider
    max_nr_observed : int, optional
        Maximum value for the slider range (default 6)
    """
    if slider_id_uuid not in st.session_state:
        st.session_state[slider_id_uuid] = uuid.uuid4()
    slider_key = st.session_state[slider_id_uuid]

    default_value = st.session_state.get(slider_key, default_val_slider)

    # Generate slider options based on max_nr_observed
    slider_options = list(range(1, max_nr_observed + 1))

    st.select_slider(
        label="Minimal precursor quantifications (# samples)",
        options=slider_options,
        value=default_value,
        key=slider_key,
        help="Use the slider to set the minimum number of raw files in which a precursor must be quantified (e.g., 3 = ≥3 files).",
    )


def initialize_radio(radio_id_uuid: str, default_value: str) -> None:
    """Initialize radio button state with UUID and default value."""
    initialize_uuid_state(radio_id_uuid, default_value)


def generate_main_radio(radio_id_uuid: str, description: str, options: list, help: str = None) -> None:
    """Generate a radio button selector."""
    radio_uuid = st.session_state[radio_id_uuid]
    st.radio(description, options, key=radio_uuid, help=help)


def initialize_main_selectbox(selectbox_id_uuid: str, default_value: str = "None") -> None:
    """Initialize the selectbox state with UUID and default value."""
    initialize_uuid_state(selectbox_id_uuid, default_value)


def generate_main_selectbox(variables, selectbox_id_uuid: str) -> None:
    """Generate the main selectbox for label selection."""
    st.selectbox("Select label", variables.metric_plot_labels, key=st.session_state[selectbox_id_uuid])


def display_metric_selector(variables, options: Optional[list] = None, label: str = "Select metric") -> str:
    """Display metric selector and return selected metric.

    Parameters
    ----------
    variables : object
        Variables object (used for help text).
    options : list, optional
        The metric options to show. Defaults to ``["Median", "Mean"]`` (quant modules).
        Other module types (e.g. entrapment) pass their own option list.
    label : str, optional
        The radio widget label. Defaults to ``"Select metric"``.
    """
    if options is None:
        options = ["Median", "Mean"]
    return st.radio(label, options, horizontal=True)


def display_colorblindmode_selector(variables, use_submitted: bool = False) -> str:
    """Display colorblind mode selector toggle.

    Parameters
    ----------
    variables : VariablesClass
        Variables object containing selector UUIDs
    use_submitted : bool, optional
        If True, use the submitted selector UUID, by default False

    Returns
    -------
    bool
        Current state of the colorblind mode toggle
    """
    key = variables.colorblind_mode_selector_submitted_uuid if use_submitted else variables.colorblind_mode_selector_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]

    return st.toggle(
        "Colorblind Mode",
        help="Toggle colorblind mode on or off.",
        key=_id_of_key,
    )


def generate_forced_toggle(
    toggle_id_uuid: str,
    label: str,
    default: bool,
    force_value: Optional[bool] = None,
    help: Optional[str] = None,
) -> bool:
    """Render a toggle widget that can be forced to a fixed value and disabled.

    Parameters
    ----------
    toggle_id_uuid : str
        Session-state key holding this widget's UUID (created on first use).
    label : str
        Widget label.
    default : bool
        Default (first-render) checked state.
    force_value : Optional[bool], optional
        If not None, the widget is shown at this value and disabled, overriding whatever
        the user previously set -- used when the toggle is meaningless under the current
        mode (e.g. an ambiguity toggle while Mass-based evaluation is selected).
    help : str, optional
        Widget help/tooltip text.

    Returns
    -------
    bool
        The toggle's current (possibly forced) value.
    """
    if toggle_id_uuid not in st.session_state.keys():
        st.session_state[toggle_id_uuid] = uuid.uuid4()
    widget_key = st.session_state[toggle_id_uuid]

    if force_value is not None:
        st.session_state[widget_key] = force_value

    return st.toggle(
        label,
        value=default,
        help=help,
        key=widget_key,
        disabled=force_value is not None,
    )


def filter_data_if_applicable(variables, ionmodule, use_slider: bool = True, submitted: bool = False) -> pd.DataFrame:
    """
    Filter data using module-specific filtering logic.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    ionmodule : object
        The module instance with filter_data_point method.
    use_slider : bool, optional
        Whether to use slider-based filtering (Quant) or return all data (De Novo).
    submitted : bool, optional
        If True, use the Tab 4 data and slider keys.

    Returns
    -------
    pd.DataFrame
        Filtered or unfiltered data points.
    """
    data = st.session_state[_data_key(variables, submitted)]
    slider_attr = "slider_id_submitted_uuid" if submitted else "slider_id_uuid"
    if use_slider and hasattr(ionmodule, "filter_data_point") and hasattr(variables, slider_attr):
        slider_key = st.session_state.get(getattr(variables, slider_attr))
        return ionmodule.filter_data_point(data, st.session_state.get(slider_key, 3))
    return data


def display_download_section(variables, sort_by: str = "id") -> None:
    """
    Render the download section for raw datasets.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    sort_by : str, optional
        Column to sort the download options by.
    """
    if len(st.session_state[variables.all_datapoints]) == 0:
        st.error("No data available for download.", icon="🚨")
        return

    downloads_df = st.session_state[variables.all_datapoints][["id", "intermediate_hash"]].copy()
    downloads_df = downloads_df.sort_values(sort_by, ascending=False)
    downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

    if (
        not hasattr(variables, "placeholder_downloads_container")
        or variables.placeholder_downloads_container not in st.session_state
    ):
        if hasattr(variables, "placeholder_downloads_container"):
            st.session_state[variables.placeholder_downloads_container] = st.empty()

    if not hasattr(variables, "download_selector_id_uuid") or variables.download_selector_id_uuid not in st.session_state:
        if hasattr(variables, "download_selector_id_uuid"):
            st.session_state[variables.download_selector_id_uuid] = uuid.uuid4()

    st.subheader("Download all data from a submitted workflow")

    selector_key = st.session_state.get(
        getattr(variables, "download_selector_id_uuid", "download_selector"), "download_selector"
    )

    selected_hash = st.selectbox(
        "Select dataset (sorted by most recent)",
        downloads_df["intermediate_hash"],
        index=None,
        key=selector_key,
        format_func=lambda x: downloads_df["id"][x] if x in downloads_df.index else x,
    )

    if selected_hash is not None and "storage" in st.secrets and st.secrets["storage"]["dir"] is not None:
        dataset_path = os.path.join(st.secrets["storage"]["dir"], selected_hash)
        if os.path.isdir(dataset_path):
            files = os.listdir(dataset_path)
            if files:
                st.write(f"Available files for dataset `{downloads_df['id'][selected_hash]}`:")
                for file_name in sorted(files):
                    path_to_file = os.path.join(dataset_path, file_name)
                    with open(path_to_file, "rb") as file:
                        st.download_button(
                            label=f"📥 {file_name}",
                            data=file,
                            file_name=file_name,
                            key=f"download_{selected_hash}_{file_name}",
                        )
            else:
                st.info("No files available in this dataset directory.", icon="ℹ️")
        else:
            st.warning(
                f"Directory for dataset `{downloads_df['id'][selected_hash]}` does not exist. "
                "This may indicate the data has not been uploaded or archived.",
                icon="⚠️",
            )
    elif selected_hash is not None:
        st.info("Storage directory is not configured. Set `storage.dir` in secrets.toml to enable downloads.", icon="ℹ️")


def load_and_filter_main_data(variables, ionmodule, use_slider: bool = True, submitted: bool = False) -> pd.DataFrame:
    """
    Load, slider/parameter-filter, and open-source-annotate the datapoints table -- the
    data-loading half of `display_existing_results`, exposed separately so a caller can
    render more than one view (e.g. a plot *and* an alternative plot behind a tab switcher)
    off the same filtered selection without loading it twice.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        The module instance (Quant, De Novo, etc.).
    use_slider : bool, optional
        Whether to use slider-based filtering (default True for Quant).
    submitted : bool, optional
        If True, load the Tab 4 (public + new) data and pin the newly submitted row so it
        survives all parameter filters.

    Returns
    -------
    pd.DataFrame
        The filtered dataframe (empty if there's nothing to show yet).
    """
    initialize_main_data_points(variables, ionmodule, submitted)
    filtered_data = add_open_source_column(filter_data_if_applicable(variables, ionmodule, use_slider, submitted))
    pinned = None
    if submitted and "old_new" in filtered_data.columns:
        pinned = filtered_data.index[filtered_data["old_new"] == "new"]
    # key_prefix must be unique per module page
    return generate_parameter_filters(
        filtered_data,
        key_prefix=f"param_filter_{_data_key(variables, submitted)}",
        pinned_indices=pinned,
    )


def _render_submitted_plot(variables, ionmodule, plot_params: Dict[str, Any], filtered_data: pd.DataFrame) -> None:
    """Render Tab 4's plain metric plot (no click-to-highlight, no Alpha/Beta annotation)."""
    plot_generator = ionmodule.get_plot_generator(y_axis_title=getattr(variables, "y_axis_title", None))
    fig_key = getattr(variables, "fig_metric_submitted", "submitted_plot")
    if fig_key not in st.session_state:
        st.session_state[fig_key] = uuid.uuid4()

    with st.container(key="tour_submitted_plot"):
        try:
            fig = plot_generator.plot_main_metric(
                result_df=filtered_data,
                hide_annot=plot_params.get("hide_annot", False),
                **plot_params,
            )
            st.plotly_chart(fig, key=st.session_state[fig_key])
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
            with st.expander("Error details"):
                st.code(traceback.format_exc())


def render_main_plot(
    variables,
    ionmodule,
    plot_params: Dict[str, Any],
    filtered_data: pd.DataFrame,
    render_forest_plot=None,
    submitted: bool = False,
) -> None:
    """
    Render the main scatter/metric plot. On Tab 1 it has click-to-highlight against the
    table rendered separately by `render_results_table` (both read/write the same highlight
    session-state key, so they stay in sync even when rendered in different containers,
    e.g. one inside a tab switcher and the other outside it).

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        The module instance (Quant, De Novo, etc.).
    plot_params : Dict[str, Any]
        Module-specific plotting parameters passed straight through to render_metric_plot
        (and on to plot_main_metric). alpha_warning and beta_warning are consumed here.
    filtered_data : pd.DataFrame
        The dataframe to plot, as returned by `load_and_filter_main_data`.
    render_forest_plot : callable, optional
        Optional callable that renders an additional plot (e.g. a forest plot)
        directly below the main plot.
    submitted : bool, optional
        If True, render Tab 4's plain plot (no highlight, no Alpha/Beta annotation).
    """
    if submitted:
        _render_submitted_plot(variables, ionmodule, plot_params, filtered_data)
    else:
        _render_highlight_plot(variables, ionmodule, plot_params, filtered_data)
    if render_forest_plot is not None:
        render_forest_plot()


def _render_highlight_plot(variables, ionmodule, plot_params: Dict[str, Any], filtered_data: pd.DataFrame) -> None:
    """Render Tab 1's metric plot with click-to-highlight and the Alpha/Beta/Archived annotation."""
    plot_generator = ionmodule.get_plot_generator(y_axis_title=getattr(variables, "y_axis_title", None))

    # --- Session state keys for bidirectional selection ---
    # highlight_key : ProteoBench ID currently highlighted in both widgets
    # plot_key_id   : key -> UUID used for the Plotly chart; regenerating clears Plotly selection
    # agrid_key_id  : key -> UUID used for the AgGrid;       regenerating clears row selection
    highlight_key = f"{variables.fig_metric}_tab1_highlight_id"
    plot_key_id = variables.fig_metric
    agrid_key_id = f"{variables.fig_metric}_tab1_aggrid_key"

    if plot_key_id not in st.session_state:
        st.session_state[plot_key_id] = uuid.uuid4()
    if agrid_key_id not in st.session_state:
        st.session_state[agrid_key_id] = uuid.uuid4()

    highlight_id = st.session_state.get(highlight_key, None)

    # Stamp the Highlight column so plot_main_metric renders the highlighted point
    # with a distinct colour and larger marker (both HYE and de novo generators respect this).
    data_for_plot = filtered_data.copy()
    if "id" in data_for_plot.columns:
        data_for_plot["Highlight"] = data_for_plot["id"] == highlight_id
    else:
        data_for_plot["Highlight"] = False

    # Build annotation and strip meta-keys before forwarding to render_metric_plot.
    annotation = ""
    if plot_params.get("archived_warning"):
        annotation = "-Archived-"
    elif plot_params.get("beta_warning"):
        annotation = "-Beta-"
    elif plot_params.get("alpha_warning"):
        annotation = "-Alpha-"

    consumed_keys = {"alpha_warning", "beta_warning", "metric", "mode", "label", "colorblind_mode"}
    extra_plot_kwargs = {k: v for k, v in plot_params.items() if k not in consumed_keys}

    # --- Render plot via the shared utility; get the clicked point ID ---
    plot_clicked_id = render_metric_plot(
        data=data_for_plot,
        key=st.session_state[plot_key_id],
        plot_generator=plot_generator,
        metric=plot_params.get("metric"),
        mode=plot_params.get("mode"),
        label=plot_params.get("label", "None"),
        colorblind_mode=plot_params.get("colorblind_mode", False),
        annotation=annotation,
        **extra_plot_kwargs,
    )

    if plot_clicked_id is not None and plot_clicked_id != highlight_id:
        st.session_state[highlight_key] = plot_clicked_id
        st.session_state[agrid_key_id] = uuid.uuid4()
        st.rerun(scope="fragment")


def render_results_table(variables, filtered_data: pd.DataFrame, submitted: bool = False) -> None:
    """
    Render the results table. On Tab 1 it is selectable, shows the ID currently
    highlighted (set by `render_main_plot`), and is followed by the raw-data download
    section; on Tab 4 it is read-only with no download section. Kept as its own function
    so it can be rendered once regardless of how many alternative plots a page switches
    between (see `render_main_plot`'s docstring).

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    filtered_data : pd.DataFrame
        The dataframe to display, as returned by `load_and_filter_main_data`.
    submitted : bool, optional
        If True, render Tab 4's read-only table.
    """
    if submitted:
        if len(filtered_data) == 0:
            st.info("No submitted datapoints available to display.", icon="ℹ️")
            return
        highlight_id = None
        suffix = getattr(variables, "fig_metric_submitted", "submitted")
        table_key = f"tab4_table_{suffix}"
        download_key = f"tab4_download_table_{suffix}"
        subheader, file_name = "Submitted Benchmark Results", "submitted_benchmark_results.csv"
        container = contextlib.nullcontext()
    else:
        agrid_key_id = f"{variables.fig_metric}_tab1_aggrid_key"
        if agrid_key_id not in st.session_state:
            st.session_state[agrid_key_id] = uuid.uuid4()
        highlight_id = st.session_state.get(f"{variables.fig_metric}_tab1_highlight_id", None)
        table_key = st.session_state[agrid_key_id]
        download_key = f"tab1_download_table_{variables.fig_metric}"
        subheader, file_name = "Benchmark Results", "benchmark_results.csv"
        container = st.container(key="tour_results_table")

    with container:
        st.subheader(subheader)
        df_display = prepare_display_dataframe(filtered_data, highlight_id)
        enable_selection = not submitted
        grid_options = configure_aggrid(df_display, enable_selection=enable_selection)
        render_aggrid(df_display, grid_options, key=table_key, enable_selection=enable_selection)

        st.download_button(
            label="Download table",
            data=streamlit_utils.save_dataframe(clean_dataframe_for_export(df_display)),
            file_name=file_name,
            mime="text/csv",
            key=download_key,
            icon=":material/download:",
        )

    if not submitted:
        with st.container(key="tour_download_section"):
            display_download_section(variables)


def display_existing_results(
    variables,
    ionmodule,
    plot_params: Dict[str, Any],
    use_slider: bool = True,
    render_forest_plot=None,
    submitted: bool = False,
) -> Optional[pd.DataFrame]:
    """
    Main orchestration function for Tab 1 (and Tab 4 with ``submitted=True``): plot + table.

    On Tab 1, clicking a point in the scatter plot highlights the matching row in the table.

    A thin wrapper around `load_and_filter_main_data` + `render_main_plot` +
    `render_results_table` -- callers that need the plot and table in separate containers
    (e.g. de novo's Scatter/Precision-Coverage-Curves tab switcher, where only the plot
    should swap and the table should stay put) can call those three directly instead.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        The module instance (Quant, De Novo, etc.).
    plot_params : Dict[str, Any]
        Module-specific plotting parameters passed straight through to render_metric_plot
        (and on to plot_main_metric). alpha_warning and beta_warning are consumed here.
    use_slider : bool, optional
        Whether to use slider-based filtering (default True for Quant).
    render_forest_plot : callable, optional
        Optional callable that renders an additional plot (e.g. a forest plot)
        between the scatter plot and the results table.
    submitted : bool, optional
        If True, show the Tab 4 (public + new) view.

    Returns
    -------
    Optional[pd.DataFrame]
        The filtered dataframe used to render the plot and table (after slider/parameter
        filtering), so a caller can reuse it for an alternative view of the same selection.
    """
    filtered_data = load_and_filter_main_data(variables, ionmodule, use_slider, submitted)

    if not submitted and filtered_data.empty:
        st.info("No results available yet.", icon="ℹ️")
        return filtered_data

    render_main_plot(variables, ionmodule, plot_params, filtered_data, render_forest_plot, submitted)
    render_results_table(variables, filtered_data, submitted)

    return filtered_data
