import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st
from streamlit_extras.let_it_rain import rain

from proteobench.io.parsing.utils import add_maxquant_fixed_modifications

from .inputs import generate_input_widget


def generate_submission_ui_elements(variables_quant, user_input) -> bool:
    """
    Create the UI elements necessary for data submission,
    including metadata uploader and comments section.
    """
    submission_ready = False
    try:
        copy_dataframes_for_submission(variables_quant)
        submission_ready = True
    except Exception:
        st.error(":x: Please provide a result file", icon="🚨")
    generate_metadata_uploader(variables_quant, user_input)
    return submission_ready


logger: logging.Logger = logging.getLogger(__name__)


def load_user_parameters(variables_quant, ionmodule, user_input) -> Any:
    """
    Read and process the parameter files provided by the user.

    Returns
    -------
    Any
        The parsed parameters.
    """
    params = None

    try:
        params = ionmodule.load_params_file(
            user_input[variables_quant.meta_data],
            user_input["input_format"],
            json_file=variables_quant.additional_params_json,
        )
        st.session_state[variables_quant.params_json_dict] = params.__dict__ if hasattr(params, "__dict__") else params

    except KeyError:
        st.error(
            "Parsing of meta parameters file for this software is not supported yet.",
            icon="🚨",
        )
    except Exception as e:
        input_f = user_input["input_format"]
        st.error(
            "Unexpected error while parsing file. Make sure you provided a meta "
            f"parameters file produced by {input_f}: {e}",
            icon="🚨",
        )
    return params


def generate_additional_parameters_fields_submission(
    variables_quant,
    user_input,
) -> None:
    """
    Create the additional parameters section of the form and initializes the parameter fields.
    """
    st.markdown(variables_quant.texts.ShortMessages.initial_parameters)

    # Load JSON config
    with open(variables_quant.additional_params_json, encoding="utf-8") as file:
        config = json.load(file)

    # Check if parsed values exist in session state
    _ = st.session_state.get(variables_quant.params_json_dict, {})

    st_col1, st_col2, st_col3 = st.columns(3)
    input_param_len = int(len(config.items()) / 3)

    for idx, (key, value) in enumerate(config.items()):
        if key.lower() == "software_name":
            editable = False
        else:
            editable = True

        if idx < input_param_len:
            with st_col1:
                user_input[key] = generate_input_widget(
                    variables_quant, user_input["input_format"], value, key, editable=editable
                )
        elif idx < input_param_len * 2:
            with st_col2:
                user_input[key] = generate_input_widget(
                    variables_quant, user_input["input_format"], value, key, editable=editable
                )
        else:
            with st_col3:
                user_input[key] = generate_input_widget(
                    variables_quant, user_input["input_format"], value, key, editable=editable
                )


def generate_comments_section(variables_quant, user_input) -> None:
    """
    Create the text area for submission comments.
    """
    user_input["comments_for_submission"] = st.text_area(
        "Comments for submission",
        placeholder=variables_quant.texts.ShortMessages.parameters_additional,
        height=200,
    )
    st.session_state[variables_quant.meta_data_text] = user_input["comments_for_submission"]


def generate_confirmation_checkbox(check_submission: str) -> None:
    """
    Create the confirmation checkbox for metadata correctness.
    """
    st.session_state[check_submission] = st.checkbox(
        "I confirm that the metadata is correct",
    )
    return True


def get_form_values(variables_quant) -> dict[str, Any]:
    """
    Retrieve all user inputs from Streamlit session state and returns them as a dictionary.

    Returns
    -------
    dict[str, Any]
        A dictionary containing all user inputs.
    """
    form_values = {}

    # Load JSON config (same file used to create fields)
    with open(variables_quant.additional_params_json, "r", encoding="utf-8") as file:
        config = json.load(file)

    # Extract values from session state
    for key in config.keys():
        form_key = variables_quant.prefix_params + key  # Ensure correct session key
        form_values[key] = st.session_state.get(form_key, None)  # Retrieve value, default to None if missing

    return form_values


def submit_to_repository(
    variables_quant,
    ionmodule,
    user_input,
    params_from_file,
    params,
) -> Optional[str]:
    """
    Handle the submission process of the benchmark results to the ProteoBench repository.

    Parameters
    ----------
    params : ProteoBenchParameters
        The parameters for the submission.

    Returns
    -------
    str, optional
        The URL of the pull request if the submission was successful.
    """
    st.session_state[variables_quant.submit] = True
    button_pressed = generate_submission_button(
        button_submission_uuid=variables_quant.button_submission_uuid
    )  # None or 'button_pressed'

    if not button_pressed:  # if button_pressed is None
        return None

    # MaxQuant fixed modification handling
    if user_input["input_format"] == "MaxQuant":
        st.session_state[variables_quant.result_perf] = add_maxquant_fixed_modifications(
            params, st.session_state[variables_quant.result_perf]
        )
        # Overwrite the dataframes for submission
        # ? done a second time?
        copy_dataframes_for_submission(
            variables_quant=variables_quant,
        )

    clear_highlight_column(all_datapoints_submission=variables_quant.all_datapoints_submission)

    pr_url = create_pull_request(
        variables_quant=variables_quant,
        ionmodule=ionmodule,
        user_input=user_input,
        params_from_file=params_from_file,
        params=params,
    )

    if pr_url:
        save_intermediate_submission_data(
            variables_quant=variables_quant,
            ionmodule=ionmodule,
            user_input=user_input,
        )

    return pr_url


def show_submission_success_message(variables_quant, pr_url) -> None:
    """
    Handle the UI updates and notifications after a successful submission.

    Parameters
    ----------
    pr_url : str
        The URL of the pull request.
    """
    if st.session_state[variables_quant.submit]:
        st.subheader("SUCCESS")
        st.markdown(variables_quant.texts.ShortMessages.submission_processing_warning)
        try:
            st.write(f"Follow your submission approval here: [{pr_url}]({pr_url})")
        except UnboundLocalError:
            pass

        st.session_state[variables_quant.submit] = False
        rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)


########################################################################################
# helper functions for:

# generate_submission_ui_elements


def copy_dataframes_for_submission(variables_quant) -> None:
    """
    Create copies of the dataframes before submission.
    """
    if st.session_state[variables_quant.all_datapoints_submitted] is not None:
        st.session_state[variables_quant.all_datapoints_submission] = st.session_state[
            variables_quant.all_datapoints_submitted
        ].copy()
    if st.session_state[variables_quant.input_df] is not None:
        st.session_state[variables_quant.input_df_submission] = st.session_state[variables_quant.input_df].copy()
    if st.session_state[variables_quant.result_perf] is not None:
        st.session_state[variables_quant.result_performance_submission] = st.session_state[
            variables_quant.result_perf
        ].copy()


def generate_metadata_uploader(variables_quant, user_input) -> None:
    """
    Create the file uploader for meta data.
    """
    user_input[variables_quant.meta_data] = st.file_uploader(
        "Meta data for searches",
        help=variables_quant.texts.Help.meta_data_file,
        accept_multiple_files=True,
    )


# submit_to_repository


def generate_submission_button(button_submission_uuid) -> Optional[str]:
    """
    Create a button for public submission and returns the PR URL if the button is pressed.

    Returns
    -------
    Optional[str]
        The URL of the pull request.
    """
    if button_submission_uuid not in st.session_state.keys():
        _button_submission_uuid = uuid.uuid4()
        st.session_state[button_submission_uuid] = _button_submission_uuid

    submit_pr = st.button(
        "I really want to upload it",
        key=st.session_state[button_submission_uuid],
    )
    if not submit_pr:
        return None

    return "button_pressed"


def clear_highlight_column(all_datapoints_submission: str) -> None:
    """
    Remove the highlight column from the submission data if it exists.
    """
    if "Highlight" in st.session_state[all_datapoints_submission].columns:
        st.session_state[all_datapoints_submission].drop("Highlight", inplace=True, axis=1)


def compare_dictionaries(old_dict, new_dict):
    """
    Generate a human-readable string describing differences between two dictionaries.

    Parameters
    ----------
    old_dict : dict
        The old dictionary.
    new_dict : dict
        The new dictionary.

    Returns
    -------
    str
        The human-readable string describing the differences between the two dictionaries.
    """
    changes = []

    # Get all unique keys across both dictionaries
    all_keys = set(old_dict.keys()).union(set(new_dict.keys()))

    for key in all_keys:
        old_value = old_dict.get(key, "[MISSING]")
        new_value = new_dict.get(key, "[MISSING]")
        if str(old_value) != str(new_value) and not (old_value is None and new_value == "[MISSING]"):
            changes.append(f"- **{key}**: `{old_value}` → `{new_value}`")

    if changes:
        return "\n ### Parameter changes detected:\n" + "\n".join(changes)
    else:
        return "\n ### No parameter changes detected. \n"


def create_pull_request(
    variables_quant,
    ionmodule,
    user_input,
    params_from_file: dict[str, Any],
    params: dataclass,
) -> Optional[str]:
    """
    Submit the pull request with the benchmark results and returns the PR URL.

    Parameters
    ----------
    params : Any
        The parameters object.

    Returns
    -------
    Optional[str]
        The URL of the pull request.
    """
    user_comments = user_input["comments_for_submission"]

    changed_params_str = compare_dictionaries(params_from_file, params.__dict__)

    try:
        pr_url = ionmodule.clone_pr(
            st.session_state[variables_quant.all_datapoints_submission],
            params,
            remote_git=variables_quant.github_link_pr,
            submission_comments=user_comments + "\n" + changed_params_str,
        )
    except Exception as e:
        st.error(f"Unable to create the pull request: {e}", icon="🚨")
        pr_url = None

    if not pr_url:
        del st.session_state[variables_quant.submit]

    return pr_url


def save_intermediate_submission_data(variables_quant, ionmodule, user_input) -> None:
    """
    Store intermediate and input data to the storage directory if available.
    """
    _id = str(
        st.session_state[variables_quant.all_datapoints_submission][
            st.session_state[variables_quant.all_datapoints_submission]["old_new"] == "new"
        ].iloc[-1, :]["intermediate_hash"]
    )

    user_input["input_csv"].getbuffer()

    if "storage" in st.secrets.keys():
        extension_input_file = os.path.splitext(user_input["input_csv"].name)[1]
        extension_input_parameter_file = os.path.splitext(
            user_input[variables_quant.meta_data][0].name,
        )[1]
        logger.info("Save intermediate raw")
        df_result_performance_submission = st.session_state[variables_quant.result_performance_submission]
        ionmodule.write_intermediate_raw(
            directory=st.secrets["storage"]["dir"],
            ident=_id,
            input_file_obj=user_input["input_csv"],
            result_performance=df_result_performance_submission,
            param_loc=user_input[variables_quant.meta_data],
            comment=st.session_state[variables_quant.meta_data_text],
            extension_input_file=extension_input_file,
            extension_input_parameter_file=extension_input_parameter_file,
        )
