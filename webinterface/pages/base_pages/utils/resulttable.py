import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# this file contains utility functions for rendering the result table in tab1_results and tab4_display_results_submitted

# === Table Color Constants ===
COLOR_IDENTIFIER = "#EEF2FF"  # soft indigo tint  – id / selected columns
COLOR_PARAMETER = "#FFFFFF"  # clean white         – search / quant parameters
COLOR_RESULT = "#F0FDF4"  # soft green tint     – performance metrics
COLOR_ADDITIONAL = "#FAFAFA"  # near-white gray     – extra / unknown columns

# Row-level highlight applied to every cell when the row is selected
COLOR_ROW_SELECTED = "#FFF3CD"


def _get_cell_style_js(bg_color_normal: str, align: str = "left") -> JsCode:
    """
    Returns a JsCode cellStyle function that applies a normal background colour
    per column category, and switches the entire row to a warm amber highlight
    whenever the 'selected' indicator column is non-empty.

    Parameters
    ----------
    bg_color_normal : str
        Background colour used for non-selected rows.
    align : str, optional
        CSS text-align value ('left', 'center', or 'right').
    """
    return JsCode(f"""
    function(params) {{
        var isSelected = params.data && params.data['selected'] && params.data['selected'] !== '';
        if (isSelected) {{
            return {{
                'backgroundColor': '{COLOR_ROW_SELECTED}',
                'color': '#1a1a1a',
                'fontWeight': '600',
                'textAlign': '{align}'
            }};
        }}
        return {{
            'backgroundColor': '{bg_color_normal}',
            'color': '#333333',
            'fontWeight': 'normal',
            'textAlign': '{align}'
        }};
    }}
    """)


def render_aggrid(df: pd.DataFrame, grid_options, key, enable_selection: bool = False):
    """
    Renders a DataFrame using AgGrid with specified grid options and a unique key.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to display in the grid.
    grid_options : dict
        Configuration options for AgGrid.
    key : Any
        Unique identifier for the grid instance (AgGrid does not work with UUID keys).
    enable_selection : bool, optional
        If True, configure the grid for single-row selection and return the grid response
        so callers can inspect selected rows.

    Returns
    -------
    AgGridReturn
        The AgGrid return object; callers can read `.selected_rows` when selection is enabled.
    """
    # Calculate dynamic height based on number of rows
    # Row height ~50px + header ~40px + padding
    row_height = 50
    header_height = 40
    padding = 10
    num_rows = len(df)
    calculated_height = (num_rows * row_height) + header_height + padding

    # Set min and max bounds for usability
    min_height = 150
    max_height = 800
    dynamic_height = max(min_height, min(calculated_height, max_height))

    update_mode = GridUpdateMode.SELECTION_CHANGED if enable_selection else GridUpdateMode.NO_UPDATE

    return AgGrid(
        df,
        gridOptions=grid_options,
        theme="alpine",
        fit_columns_on_grid_load=False,
        height=dynamic_height,
        allow_unsafe_jscode=True,
        update_mode=update_mode,
        key=f"aggrid::{str(key)}",  # AgGrid does not work with UUID keys
    )


def configure_aggrid(df: pd.DataFrame, enable_selection: bool = False):
    """
    Configures the styling and options for AgGrid based on column category.

    Parameters
    ----------
    df : pd.DataFrame
        The display-ready DataFrame.
    enable_selection : bool, optional
        If True, configure single-row selection without checkboxes.

    Returns
    -------
    dict
        AgGrid gridOptions dictionary.
    """
    gb = GridOptionsBuilder.from_dataframe(df)

    # Defaults: sortable, filterable, resizable, wrapped headers
    gb.configure_default_column(
        sortable=True,
        filterable=True,
        resizable=True,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        minWidth=80,
    )

    if enable_selection:
        gb.configure_selection(selection_mode="single", use_checkbox=False)

    parameter_cols = {
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
        "checkpoint",
        "n_beams",
        "n_peaks",
        "min_mz",
        "max_mz",
        "min_intensity",
        "max_intensity",
        "tokens",
        "remove_precursor_tol",
        "isotope_error_range",
        "decoding_strategy",
    }
    result_cols = {"median_abs_epsilon", "mean_abs_epsilon", "nr_prec", "results", "precision", "recall"}

    for col in df.columns:
        if col == "selected":
            # Narrow indicator column, pinned, no sort/filter, centred
            gb.configure_column(
                col,
                header_name="",
                width=40,
                minWidth=40,
                maxWidth=40,
                pinned="left",
                sortable=False,
                filterable=False,
                resizable=False,
                cellStyle=_get_cell_style_js(COLOR_IDENTIFIER, align="center"),
            )
        elif col == "id":
            gb.configure_column(
                col,
                header_name="ProteoBench ID",
                minWidth=160,
                pinned="left",
                cellStyle=_get_cell_style_js(COLOR_IDENTIFIER),
            )
        elif col in parameter_cols:
            gb.configure_column(col, cellStyle=_get_cell_style_js(COLOR_PARAMETER))
        elif col in result_cols:
            # Right-align metrics so decimal points line up
            gb.configure_column(col, cellStyle=_get_cell_style_js(COLOR_RESULT, align="right"), minWidth=130)
        else:
            gb.configure_column(col, cellStyle=_get_cell_style_js(COLOR_ADDITIONAL))

    return gb.build()


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

    if len(df) == 0:
        return df
    df["selected"] = df["id"].apply(lambda x: "➡️" if x == highlight_id else "")

    try:
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
            "checkpoint",
            "n_beams",
            "n_peaks",
            "min_mz",
            "max_mz",
            "min_intensity",
            "max_intensity",
            "tokens",
            "remove_precursor_tol",
            "isotope_error_range",
            "decoding_strategy",
        ]
        result_cols = ["median_abs_epsilon", "mean_abs_epsilon", "nr_prec", "results", "precision", "recall"]
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
            col
            for col in cols
            if col not in ["comments", "scatter_size", "old_new", "is_temporary", "color", "hover_text"]
        ]
        df = df[cols + additional_cols]

        # Clean up values
        df["results"] = df["results"].apply(str)
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
        df[numeric_cols] = df[numeric_cols].round(3)
        df.sort_values(by="id", inplace=True)

    except KeyError as e:
        print(f"KeyError during DataFrame preparation: {e}")

    return df
