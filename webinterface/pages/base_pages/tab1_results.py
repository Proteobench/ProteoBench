import os
import uuid
from typing import Callable

import streamlit as st
import pandas as pd
import re

from proteobench.plotting.plot_quant import PlotDataPoint
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode

from .filter import filter_data_using_slider

# === Table Color Constants ===
COLOR_IDENTIFIER = "#F0F2F6"
COLOR_PARAMETER = "#FFFFFF"
COLOR_RESULT = "#F0F2F6"
COLOR_TECHNICAL = "#FFFFFF"
COLOR_ADDITIONAL = "#F0F2F6"


def initialize_main_slider(slider_id_uuid: str, default_val_slider: float) -> None:
    """
    Initialize the slider for the main data.

    We use a slider uuid and associate a defalut value with it.
    - self.variables_quant.slider_id_uuid
    - self.variables_quant.default_val_slider
    """
    key = slider_id_uuid
    if key not in st.session_state.keys():
        st.session_state[key] = uuid.uuid4()
    _id_of_key = st.session_state[key]
    if _id_of_key not in st.session_state.keys():
        st.session_state[_id_of_key] = default_val_slider


def generate_main_slider(slider_id_uuid: str, description_slider_md: str, default_val_slider: float) -> None:
    """
    Create a slider input.
    """
    # key for slider_uuid in session state
    if slider_id_uuid not in st.session_state:
        st.session_state[slider_id_uuid] = uuid.uuid4()
    slider_key = st.session_state[slider_id_uuid]

    fpath = description_slider_md
    st.markdown(open(fpath, "r").read())

    default_value = st.session_state.get(slider_key, default_val_slider)
    st.select_slider(
        label="Minimal precursor quantifications (# samples)",
        options=[1, 2, 3, 4, 5, 6],
        value=default_value,
        key=slider_key,
    )


def generate_main_selectbox(selectbox_id_uuid) -> None:
    """
    Create the selectbox for the Streamlit UI.
    """
    if selectbox_id_uuid not in st.session_state.keys():
        st.session_state[selectbox_id_uuid] = uuid.uuid4()

    try:
        # TODO: Other labels based on different modules, e.g. mass tolerances are less relevant for DIA
        st.selectbox(
            "Select label to plot",
            ["None", "precursor_mass_tolerance", "fragment_mass_tolerance", "enable_match_between_runs"],
            key=st.session_state[selectbox_id_uuid],
        )
    except Exception as e:
        st.error(f"Unable to create the selectbox: {e}", icon="🚨")


def display_download_section(variables_quant, reset_uuid=False) -> None:
    """
    Render the selector and area for raw data download.

    Parameters
    ----------
    reset_uuid : bool, optional
        Whether to reset the UUID, by default False.
    """
    if len(st.session_state[variables_quant.all_datapoints]) == 0:
        st.error("No data available for download.", icon="🚨")
        return

    downloads_df = st.session_state[variables_quant.all_datapoints][["id", "intermediate_hash"]]
    downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

    if variables_quant.placeholder_downloads_container not in st.session_state.keys() or reset_uuid:
        st.session_state[variables_quant.placeholder_downloads_container] = st.empty()
        st.session_state[variables_quant.download_selector_id_uuid] = uuid.uuid4()

    # with st.session_state[variables_quant.placeholder_downloads_container].container(border=True):
    st.subheader("Download raw datasets")

    # Sort the intermediate_hash values and get the corresponding ids
    sorted_indices = sorted(range(len(downloads_df["id"])), key=lambda i: downloads_df["id"].iloc[i])
    sorted_intermediate_hash = [downloads_df["intermediate_hash"].iloc[i] for i in sorted_indices]
    sorted_ids = [downloads_df["id"].iloc[i] for i in sorted_indices]

    st.selectbox(
        "Select dataset",
        sorted_intermediate_hash,
        index=None,
        key=st.session_state[variables_quant.download_selector_id_uuid],
        format_func=lambda x: sorted_ids[sorted_intermediate_hash.index(x)],
    )

    if (
        st.session_state[st.session_state[variables_quant.download_selector_id_uuid]] is not None
        and st.secrets["storage"]["dir"] is not None
    ):
        dataset_path = (
            st.secrets["storage"]["dir"]
            + "/"
            + st.session_state[st.session_state[variables_quant.download_selector_id_uuid]]
        )
        if os.path.isdir(dataset_path):
            files = os.listdir(dataset_path)
            for file_name in files:
                path_to_file = dataset_path + "/" + file_name
                with open(path_to_file, "rb") as file:
                    st.download_button(file_name, file, file_name=file_name)
        else:
            st.write(
                "Directory for this dataset does not exist, this should not happen"
                " on the server, but is expected in the local development environment."
            )


def display_existing_results(variables_quant, ionmodule) -> None:
    """
    Orchestrates the full display of quantification results in Streamlit,
    including plotting and interactive tabular output with styling.

    Parameters
    ----------
    variables_quant : object
        Object containing quantification variables including data points,
        slider/selectbox UUIDs, and configuration flags.

    ionmodule : object
        Module responsible for filtering and transforming ion data.
    """
    initialize_and_filter_data(variables_quant, ionmodule)
    data_points_filtered = variables_quant.filtered_data

    metric = display_metric_selector()
    highlight_point_id = render_metric_plot(data_points_filtered, variables_quant, metric)

    df_display = prepare_display_dataframe(data_points_filtered, highlight_point_id)
    grid_options = configure_aggrid(df_display)

    render_aggrid(df_display, grid_options)
    offer_download(df_display)
    display_download_section(variables_quant=variables_quant)


# === Modular Functions ===


def initialize_and_filter_data(variables_quant, ionmodule):
    initialize_main_data_points(
        all_datapoints=variables_quant.all_datapoints,
        obtain_all_data_points=ionmodule.obtain_all_data_points,
    )
    variables_quant.filtered_data = filter_data_using_slider(
        slider_id_uuid=variables_quant.slider_id_uuid,
        all_datapoints=variables_quant.all_datapoints,
        filter_data_point=ionmodule.filter_data_point,
    )


def display_metric_selector() -> str:
    return st.radio(
        "Select metric to plot",
        options=["Median", "Mean"],
        help="Toggle between median and mean absolute difference metrics.",
    )


def render_metric_plot(data: pd.DataFrame, variables_quant, metric: str) -> str | None:
    """
    Displays the metric plot and returns the ProteoBench ID of the selected point (if any).

    Parameters
    ----------
    data : pd.DataFrame
        The filtered dataset to plot.

    variables_quant : object
        Contains session state and selectbox identifier.

    metric : str
        Metric to plot ("Median" or "Mean").

    Returns
    -------
    str or None
        ProteoBench ID of the selected data point, if any.
    """

    if len(data) == 0:
        st.error("No datapoints available for plotting", icon="🚨")
        return None

    highlight_point_id = None
    try:
        fig_metric = PlotDataPoint.plot_metric(
            data,
            label=st.session_state[st.session_state[variables_quant.selectbox_id_uuid]],
            metric=metric,
        )
        event_dict = st.plotly_chart(
            fig_metric,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
        )
        selected_point = (
            event_dict["selection"]["points"][0]
            if "selection" in event_dict and "points" in event_dict["selection"] and event_dict["selection"]["points"]
            else None
        )
        if selected_point:
            hover = selected_point.get("hovertext", "")
            match = re.search(r"ProteoBench ID: ([^\s<]+)", hover)
            if match:
                highlight_point_id = match.group(1)

    except Exception as e:
        st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

    return highlight_point_id


def prepare_display_dataframe(df: pd.DataFrame, highlight_id: str | None) -> pd.DataFrame:
    """
    Prepares the DataFrame for display, including column filtering, ordering,
    row highlighting, and numeric formatting.

    Parameters
    ----------
    df : pd.DataFrame
        The filtered dataset for display.

    highlight_id : str or None
        The ProteoBench ID to highlight (adds a marker in the 'selected' column).

    Returns
    -------
    pd.DataFrame
        A formatted and sorted DataFrame ready for rendering.
    """
    df = df.copy()
    df["selected"] = df["id"].apply(lambda x: "➡️" if x == highlight_id else "")

    identifier_cols = ["selected", "id"]
    parameter_cols = [
        "software_name",
        "software_version",
        "search_engine",
        "search_engine_version",
        "ident_fdr_psm",
        "ident_fdr_protein",
        "ident_fdr_peptide",
        "enable_match_between_runs",
        "precursor_mass_tolerance",
        "fragment_mass_tolerance",
        "enzyme",
        "allowed_miscleavages",
        "min_peptide_length",
        "max_peptide_length",
        "fixed_mods",
        "variable_mods",
        "max_mods",
        "min_precursor_charge",
        "max_precursor_charge",
        "quantification_method",
        "protein_inference",
        "abundance_normalization_ions",
        "submission_comments",
    ]
    result_cols = ["median_abs_epsilon", "mean_abs_epsilon", "nr_prec", "results"]
    technical_cols = [
        "proteobench_version",
        "intermediate_hash",
        "hover_text",
        "color",
        "old_new",
        "is_temporary",
        "comments",
        "scatter_size",
    ]

    # Define display column order
    cols = identifier_cols + parameter_cols + result_cols + technical_cols
    cols = [col for col in cols if col in df.columns]
    additional_cols = [col for col in df.columns if col not in cols]
    # remove boring columns
    cols = [
        col for col in cols if col not in ["comments", "scatter_size", "old_new", "is_temporary", "color", "hover_text"]
    ]
    df = df[cols + additional_cols]

    # Clean up values
    df["results"] = df["results"].apply(str)
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_cols] = df[numeric_cols].round(3)
    df.sort_values(by="id", inplace=True)

    return df


def configure_aggrid(df: pd.DataFrame):
    """
    Configures the styling and options for AgGrid based on column category.

    Parameters
    ----------
    df : pd.DataFrame
        The display-ready DataFrame.

    Returns
    -------
    dict
        AgGrid gridOptions dictionary.
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    identifier_cols = ["selected", "id"]
    parameter_cols = [
        "software_name",
        "software_version",
        "search_engine",
        "search_engine_version",
        "ident_fdr_psm",
        "ident_fdr_protein",
        "ident_fdr_peptide",
        "enable_match_between_runs",
        "precursor_mass_tolerance",
        "fragment_mass_tolerance",
        "enzyme",
        "allowed_miscleavages",
        "min_peptide_length",
        "max_peptide_length",
        "fixed_mods",
        "variable_mods",
        "max_mods",
        "min_precursor_charge",
        "max_precursor_charge",
        "quantification_method",
        "protein_inference",
        "abundance_normalization_ions",
        "submission_comments",
    ]
    result_cols = ["median_abs_epsilon", "mean_abs_epsilon", "nr_prec", "results"]
    technical_cols = [
        "proteobench_version",
        "intermediate_hash",
        "hover_text",
        "color",
        "old_new",
        "is_temporary",
        "comments",
        "scatter_size",
    ]

    for col in df.columns:
        if col in identifier_cols:
            gb.configure_column(col, cellStyle=get_style_js(COLOR_IDENTIFIER))
        elif col in parameter_cols:
            gb.configure_column(col, cellStyle=get_style_js(COLOR_PARAMETER))
        elif col in result_cols:
            gb.configure_column(col, cellStyle=get_style_js(COLOR_RESULT))
        elif col in technical_cols:
            gb.configure_column(col, cellStyle=get_style_js(COLOR_TECHNICAL))
        else:
            gb.configure_column(col, cellStyle=get_style_js(COLOR_ADDITIONAL))

    return gb.build()


def render_aggrid(df: pd.DataFrame, grid_options):
    AgGrid(
        df,
        gridOptions=grid_options,
        theme="alpine",
        fit_columns_on_grid_load=False,
        height=600,
        allow_unsafe_jscode=True,
    )


def offer_download(df: pd.DataFrame, filename: str = "quantification_results.csv") -> None:
    """
    Adds a download button to export the displayed DataFrame as a CSV file.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to be downloaded.

    filename : str, optional
        The name of the file to download, by default "quantification_results.csv".
    """
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Download table as CSV", data=csv_data, file_name=filename, mime="text/csv")


def get_style_js(bg_color: str) -> JsCode:
    """
    Generates JavaScript for styling cells with a background color.

    Parameters
    ----------
    bg_color : str
        Hex color string to use as the background.

    Returns
    -------
    JsCode
        A JavaScript code block that defines the style.
    """
    return JsCode(
        f"""
    function(params) {{
        return {{
            'backgroundColor': '{bg_color}',
            'color': 'black',
            'fontWeight': 'normal'
        }}
    }}
    """
    )


def initialize_main_data_points(all_datapoints: str, obtain_all_data_points: Callable) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if all_datapoints not in st.session_state.keys():
        st.session_state[all_datapoints] = None
        st.session_state[all_datapoints] = obtain_all_data_points(all_datapoints=st.session_state[all_datapoints])
