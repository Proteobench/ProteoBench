
import streamlit as st
import tempfile
from streamlit_utils import display_error, get_error_suggestions
from proteobench.exceptions import ProteoBenchError

def process_submission_form(variables, ionmodule, user_input, level_mapping, evaluation_type_mapping):
    """
    Handle the form submission logic.

    Returns
    -------
    bool, optional
        Whether the submission was handled unsuccessfully.
    """
    if not user_input["input_csv"]:
        st.error(":x: Please provide a result file", icon="🚨")
        return False
    
    success = _execute_proteobench(variables, ionmodule, user_input, level_mapping, evaluation_type_mapping)

    if success:
        # Inform the user with a link to the next tab
        st.info(
            "Form submitted successfully! Please navigate to the 'Results In-Depth' "
            "or 'Results New Data' tab for the next step."
        )
    return success

def _execute_proteobench(variables, ionmodule, user_input, level_mapping, evaluation_type_mapping):
    """
    Execute the benchmarking process and returns the results.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        The benchmarking results, all data points, and the input data frame.
    """
    try:
        if variables.all_datapoints_submitted not in st.session_state:
            initialize_main_data_points(variables, ionmodule)
        
        result_performance, all_datapoints, input_df = _run_benchmarking_process(
            variables, ionmodule, user_input, level_mapping, evaluation_type_mapping
        )

        # Mark the uploaded dataset
        st.session_state[variables.uploaded_id] = all_datapoints.loc[len(all_datapoints)-1, 'id']
        all_datapoints.loc[len(all_datapoints)-1, 'id'] = 'Uploaded dataset'

        st.session_state[variables.all_datapoints_submitted] = all_datapoints

        _set_highlight_column_in_submitted_data(
            variables=variables,
        )

        # These are not used
        st.session_state[variables.result_perf] = result_performance
        st.session_state[variables.input_df] = input_df

        return True
    
    except (ProteoBenchError, Exception) as e:
        friendly_msg, suggestions = get_error_suggestions(e, user_input)
        display_error(friendly_msg, exception=e, suggestions=suggestions)
        return False

# Only this function is different between quant and denovo
def _run_benchmarking_process(variables, ionmodule, user_input, level_mapping, evaluation_type_mapping):
    """
    Execute the benchmarking process and returns the results.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        The benchmarking results, all data points, and the input data frame.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
        tmp_file.write(user_input["input_csv"].getvalue().decode("utf-8"))
        temp_file_path = tmp_file.name

    # reload buffer: https://stackoverflow.com/a/64478151/9684872
    user_input["input_csv"].seek(0)

    if st.session_state[variables.radio_level_id_submitted_uuid] in st.session_state.keys():
        set_level_val = st.session_state[st.session_state[variables.radio_level_id_submitted_uuid]]
    else:
        set_level_val = variables.default_level

    if st.session_state[variables.radio_evaluation_id_submitted_uuid] in st.session_state.keys():
        set_evaluation_val = st.session_state[
            st.session_state[variables.radio_evaluation_id_submitted_uuid]
        ]
    else:
        set_evaluation_val = variables.default_evaluation

    if variables.all_datapoints_submitted in st.session_state.keys():
        all_datapoints = st.session_state[variables.all_datapoints_submitted]
    else:
        all_datapoints = st.session_state[variables.all_datapoints]

    return ionmodule.benchmarking(
        input_file_loc=temp_file_path,
        input_format=user_input["input_format"],
        user_input=user_input,
        all_datapoints=all_datapoints,
        level=level_mapping[set_level_val],
        evaluation_type=evaluation_type_mapping[set_evaluation_val],
    )

def _set_highlight_column_in_submitted_data(variables):
    """
    Initialize the highlight column in the data points.
    """
    df = st.session_state[variables.all_datapoints_submitted]
    if (
        variables.highlight_list_submitted not in st.session_state.keys()
        and "Highlight" not in df.columns
    ):
        df.insert(0, "Highlight", [False] * len(df.index))
    elif "Highlight" not in df.columns:
        df.insert(0, "Highlight", st.session_state[variables.highlight_list_submitted])
    elif "Highlight" in df.columns:
        df["Highlight"] = df["Highlight"].astype(bool).fillna(False)
    st.session_state[variables.all_datapoints_submitted] = df


def initialize_main_data_points(variables, ionmodule) -> None:
    """
    Initialize the all_datapoints variable in the session state.
    """
    if variables.all_datapoints not in st.session_state.keys():
        st.session_state[variables.all_datapoints] = None
        st.session_state[variables.all_datapoints] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables.all_datapoints]
        )