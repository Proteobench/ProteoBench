import json

import streamlit as st

from . import inputs


def generate_input_fields(variables_quant, parsesettingsbuilder, user_input) -> None:
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
def generate_additional_parameters_fields(variables_quant, user_input) -> None:
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
