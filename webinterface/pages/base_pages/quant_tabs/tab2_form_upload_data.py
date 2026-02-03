import json
import tempfile

import streamlit as st
from streamlit_utils import display_error, get_error_suggestions

from proteobench.exceptions import ProteoBenchError

from . import inputs


def show_software_selector_and_alphadia_info(variables, parsesettingsbuilder, user_input) -> None:
    """
    Display software selector outside the form and show AlphaDIA-specific information.
    This allows immediate feedback when AlphaDIA is selected.
    """
    st.subheader("Input files")
    st.markdown(open(variables.description_input_file_md, "r", encoding="utf-8").read())

    # Software tool selector - outside form to enable reactive updates
    selected_format = st.selectbox(
        "Software tool",
        parsesettingsbuilder.INPUT_FORMATS,
        help=variables.texts.Help.input_format,
        key="software_tool_selector",
    )

    # Store selection in user_input for use in form
    user_input["input_format"] = selected_format

    # Display AlphaDIA-specific information text only (file uploader will be shown after main uploader)
    if selected_format == "AlphaDIA":
        st.info(
            "ℹ️**If submitting AlphaDIA output from versions >= 2.0, please submit the precursors.parquet or precursors.tsv file only and ignore the secondary file uploader.**\n"
            "**If not, you have the following options:**\n\n"
            "**Two-file upload (recommended):** Upload both **precursor.matrix.tsv** and **precursors.tsv** files below for automatic merging. "
            "You can upload them in any order - the system will automatically detect which is which.\n\n"
            "**Single-file upload (legacy):** Alternatively, upload a single pre-merged file in the main uploader above."
        )


def generate_input_fields(
    user_input,
) -> None:
    """
    Create the file upload section of the form.
    Software tool selection is now handled outside the form.
    """
    # Returns None or the selected file as UploadedFile (a file-like object)
    user_input["input_csv"] = st.file_uploader(
        "Software tool result file",
        help="Upload the result file from your selected software tool",
    )

    # For AlphaDIA, show secondary file uploader after main uploader
    if user_input.get("input_format") == "AlphaDIA":
        user_input["input_csv_secondary"] = st.file_uploader(
            "Upload second AlphaDIA file (optional)",
            type=["tsv", "csv"],
            key="alphadia_secondary_file",
        )
    else:
        user_input["input_csv_secondary"] = None


# TODO: change additional_params_json for other modules, to capture relevant parameters
def generate_additional_parameters_fields(
    variables,
    user_input,
) -> None:
    """
    Create the additional parameters section of the form and initializes the parameter fields.
    """
    with open(variables.additional_params_json, encoding="utf-8") as file:
        config = json.load(file)
    for key, value in config.items():
        if key.lower() == "software_name":
            editable = False
        else:
            editable = True

        if key == "comments_for_plotting":
            user_input[key] = inputs.generate_input_widget(
                user_input["input_format"],
                value,
                editable,
            )
        else:
            user_input[key] = None


def process_submission_form(
    variables,
    ionmodule,
    user_input,
    **kwargs
) -> bool:
    """
    Handle the form submission logic.

    Returns
    -------
    bool
        Whether the submission was handled unsuccessfully.
    """
    if not user_input["input_csv"]:
        st.error(":x: Please provide a result file", icon="🚨")
        return False

    # For AlphaDIA, inform about the two-file option but allow single merged file
    if user_input["input_format"] == "AlphaDIA" and not user_input.get("input_csv_secondary"):
        # TODO: change the way two-file upload is handled so that it doesn't cause an error message when only one of the two is provided
        st.info(
            "Only for AlphaDIA v1: You can upload both AlphaDIA files (precursor.matrix.tsv and precursors.tsv) for automatic merging, "
            "or upload a single pre-merged file. Currently uploading a single file. If you intended to upload both files, "
            "please use the secondary file uploader below and disregard the error message that may follow.",
            icon="ℹ️",
        )

    success = execute_proteobench(
        variables=variables,
        ionmodule=ionmodule,
        user_input=user_input,
        **kwargs
    )

    if success:
        # Inform the user with a link to the next tab
        st.info(
            "Form submitted successfully! Please navigate to the 'Results In-Depth' "
            "or 'Results New Data' tab for the next step."
        )
    return success


########################################################################################
# function used in process_submission_form


def execute_proteobench(variables, ionmodule, user_input, **kwargs) -> bool:
    """
    Execute the ProteoBench benchmarking process.

    Returns
    -------
    bool
        True if benchmarking succeeded, False if an error occurred.
    """
    try:
        if variables.all_datapoints_submitted not in st.session_state:
            initialize_main_data_points(
                variables=variables,
                ionmodule=ionmodule,
            )

        result_performance, all_datapoints, input_df = run_benchmarking_process(
            variables=variables,
            ionmodule=ionmodule,
            user_input=user_input,
        )
        st.session_state[variables.all_datapoints_submitted] = all_datapoints

        set_highlight_column_in_submitted_data(
            variables=variables,
        )

        st.session_state[variables.result_perf] = result_performance

        st.session_state[variables.input_df] = input_df
        return True

    except (ProteoBenchError, Exception) as e:
        friendly_msg, suggestions = get_error_suggestions(e, user_input)
        display_error(friendly_msg, exception=e, suggestions=suggestions)
        return False


# function with same name exists in tab1_results.py, but is different
def initialize_main_data_points(variables, ionmodule) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if variables.all_datapoints not in st.session_state.keys():
        st.session_state[variables.all_datapoints] = None
        st.session_state[variables.all_datapoints] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables.all_datapoints]
        )


def run_benchmarking_process(variables, ionmodule, user_input):
    """
    Execute the benchmarking process and returns the results.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        The benchmarking results, all data points, and the input data frame.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(user_input["input_csv"].getbuffer())

    # For AlphaDIA, also create temporary file for secondary input
    tmp_file_secondary = None
    if user_input.get("input_csv_secondary"):
        tmp_file_secondary = tempfile.NamedTemporaryFile(delete=False)
        tmp_file_secondary.write(user_input["input_csv_secondary"].getbuffer())
        tmp_file_secondary.flush()
        user_input["input_csv_secondary"].seek(0)

    # reload buffer: https://stackoverflow.com/a/64478151/9684872
    user_input["input_csv"].seek(0)
    if st.session_state[variables.slider_id_submitted_uuid] in st.session_state.keys():
        set_slider_val = st.session_state[st.session_state[variables.slider_id_submitted_uuid]]
    else:
        set_slider_val = variables.default_val_slider

    if variables.all_datapoints_submitted in st.session_state.keys():
        all_datapoints = st.session_state[variables.all_datapoints_submitted]
    else:
        all_datapoints = st.session_state[variables.all_datapoints]

    return ionmodule.benchmarking(
        user_input["input_csv"],
        user_input["input_format"],
        user_input,
        all_datapoints,
        default_cutoff_min_prec=set_slider_val,
        input_file_secondary=tmp_file_secondary.name if tmp_file_secondary else None,
    )


def set_highlight_column_in_submitted_data(variables) -> None:
    """
    Initialize the highlight column in the data points.
    """
    df = st.session_state[variables.all_datapoints_submitted]
    if variables.highlight_list_submitted not in st.session_state.keys() and "Highlight" not in df.columns:
        df.insert(0, "Highlight", [False] * len(df.index))
    elif "Highlight" not in df.columns:
        df.insert(0, "Highlight", st.session_state[variables.highlight_list_submitted])
    elif "Highlight" in df.columns:
        # Not sure how 'Highlight' column became object dtype
        df["Highlight"] = df["Highlight"].astype(bool).fillna(False)
    # only needed for last elif, but to be sure apply always:
    st.session_state[variables.all_datapoints_submitted] = df
