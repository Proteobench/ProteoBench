from st_aggrid import GridOptionsBuilder, AgGrid, JsCode
import pandas as pd


# this file contains utility functions for rendering the result table in tab1_results and tab4_display_results_submitted

# === Table Color Constants ===
COLOR_IDENTIFIER = "#F0F2F6"
COLOR_PARAMETER = "#FFFFFF"
COLOR_RESULT = "#F0F2F6"
COLOR_TECHNICAL = "#FFFFFF"
COLOR_ADDITIONAL = "#F0F2F6"


def _get_style_js(bg_color: str) -> JsCode:
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


def render_aggrid(df: pd.DataFrame, grid_options, key):
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

    Returns
    -------
    None
        This function renders the grid in the Streamlit interface and does not return a value.
    """
    AgGrid(
        df,
        gridOptions=grid_options,
        theme="alpine",
        fit_columns_on_grid_load=False,
        height=600,
        allow_unsafe_jscode=True,
        key=f"aggrid::{str(key)}",  # AgGrid does not work with UUID keys
    )


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
            gb.configure_column(col, cellStyle=_get_style_js(COLOR_IDENTIFIER))
        elif col in parameter_cols:
            gb.configure_column(col, cellStyle=_get_style_js(COLOR_PARAMETER))
        elif col in result_cols:
            gb.configure_column(col, cellStyle=_get_style_js(COLOR_RESULT))
        elif col in technical_cols:
            gb.configure_column(col, cellStyle=_get_style_js(COLOR_TECHNICAL))
        else:
            gb.configure_column(col, cellStyle=_get_style_js(COLOR_ADDITIONAL))

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
