import json
import tempfile

import streamlit as st

from . import inputs


def generate_input_fields(
    variables_quant,
    parsesettingsbuilder,
    user_input,
) -> None:
    """
    Create the input section of the form.
    """
    st.subheader("Input files")
    st.markdown(open(variables_quant.description_input_file_md, "r", encoding="utf-8").read())
    # ! Maybe user_input needs to be returned and assigned manually
    # ? Not the input form is made persistent?
    # It returns None or the selected options
    user_input["input_format"] = st.selectbox(
        "Software tool",
        parsesettingsbuilder.INPUT_FORMATS,
        help=variables_quant.texts.Help.input_format,
    )
    # Returns None or the selected file as UploadedFile (a file-like object)
    user_input["input_csv"] = st.file_uploader(
        "Software tool result file",
        help=variables_quant.texts.Help.input_file,
    )


# TODO: change additional_params_json for other modules, to capture relevant parameters
def generate_additional_parameters_fields(
    variables_quant,
    user_input,
) -> None:
    """
    Create the additional parameters section of the form and initializes the parameter fields.
    """
    with open(variables_quant.additional_params_json, encoding="utf-8") as file:
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
    variables_quant,
    ionmodule,
    user_input,
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
    execute_proteobench(
        variables_quant=variables_quant,
        ionmodule=ionmodule,
        user_input=user_input,
    )

    # Inform the user with a link to the next tab
    st.info(
        "Form submitted successfully! Please navigate to the 'Results In-Depth' "
        "or 'Results New Data' tab for the next step."
    )
    return True


########################################################################################
# function used in process_submission_form


def execute_proteobench(variables_quant, ionmodule, user_input) -> None:
    """
    Execute the ProteoBench benchmarking process.
    """
    if variables_quant.all_datapoints_submitted not in st.session_state:
        initialize_main_data_points(
            variables_quant=variables_quant,
            ionmodule=ionmodule,
        )

    result_performance, all_datapoints, input_df = run_benchmarking_process(
        variables_quant=variables_quant,
        ionmodule=ionmodule,
        user_input=user_input,
    )
    st.session_state[variables_quant.all_datapoints_submitted] = all_datapoints

    set_highlight_column_in_submitted_data(
        variables_quant=variables_quant,
    )

    st.session_state[variables_quant.result_perf] = result_performance

    st.session_state[variables_quant.input_df] = input_df


# function with same name exists in tab1_results.py, but is different
def initialize_main_data_points(variables_quant, ionmodule) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if variables_quant.all_datapoints not in st.session_state.keys():
        st.session_state[variables_quant.all_datapoints] = None
        st.session_state[variables_quant.all_datapoints] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables_quant.all_datapoints]
        )


def run_benchmarking_process(variables_quant, ionmodule, user_input):
    """
    Execute the benchmarking process and returns the results.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        The benchmarking results, all data points, and the input data frame.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(user_input["input_csv"].getbuffer())

    # reload buffer: https://stackoverflow.com/a/64478151/9684872
    user_input["input_csv"].seek(0)
    if st.session_state[variables_quant.slider_id_submitted_uuid] in st.session_state.keys():
        set_slider_val = st.session_state[st.session_state[variables_quant.slider_id_submitted_uuid]]
    else:
        set_slider_val = variables_quant.default_val_slider

    if variables_quant.all_datapoints_submitted in st.session_state.keys():
        all_datapoints = st.session_state[variables_quant.all_datapoints_submitted]
    else:
        all_datapoints = st.session_state[variables_quant.all_datapoints]

    return ionmodule.benchmarking(
        user_input["input_csv"],
        user_input["input_format"],
        user_input,
        all_datapoints,
        default_cutoff_min_prec=set_slider_val,
    )


def set_highlight_column_in_submitted_data(variables_quant) -> None:
    """
    Initialize the highlight column in the data points.
    """
    df = st.session_state[variables_quant.all_datapoints_submitted]
    if variables_quant.highlight_list_submitted not in st.session_state.keys() and "Highlight" not in df.columns:
        df.insert(0, "Highlight", [False] * len(df.index))
    elif "Highlight" not in df.columns:
        df.insert(0, "Highlight", st.session_state[variables_quant.highlight_list_submitted])
    elif "Highlight" in df.columns:
        # Not sure how 'Highlight' column became object dtype
        df["Highlight"] = df["Highlight"].astype(bool).fillna(False)
    # only needed for last elif, but to be sure apply always:
    st.session_state[variables_quant.all_datapoints_submitted] = df
