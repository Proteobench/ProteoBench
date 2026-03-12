from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st


def generate_input_widget(
    variables_quant: dataclass,
    input_format: str,
    content: dict,
    key: str = "",
    editable: bool = True,
) -> Any:
    """
    Generate input fields in the Streamlit UI based on the specified format and content.

    Parameters
    ----------
    input_format : str
        The input format.
    content : dict
        The content of the input fields.
    key : str
        The key of the input fields.
    editable : bool
        Whether the input fields are editable.

    Returns
    -------
    Any
        The input fields.
    """
    field_type = content.get("type")
    if field_type == "text_area":
        return _generate_text_area_widget(input_format, content, editable=editable)
    elif field_type == "text_input":
        return _generate_text_input(variables_quant, input_format, content, key, editable=editable)
    elif field_type == "number_input":
        return _generate_number_input(variables_quant, content, key, editable=editable)
    elif field_type == "selectbox":
        return _generate_selectbox(variables_quant, input_format, content, key, editable=editable)
    elif field_type == "checkbox":
        return _generate_checkbox(variables_quant, content=content, key=key, editable=editable)


# ToDo: make function accecpt a session state key if that is what is only needed
def update_parameters_submission_form(
    variables_quant,
    field,
    value,
) -> None:
    """
    Update the session state dictionary with the specified field and value.

    Parameters
    ----------
    variables_quant : dataclass
        The variables quantification dataclass containing the session state keys used.
    field : str
        The field to update.
    value : Any
        The value to update the field with.
    """
    session_state_key = variables_quant.params_file_dict
    try:
        st.session_state[session_state_key][field] = value
    except KeyError:
        st.session_state[session_state_key] = {}
        st.session_state[session_state_key][field] = value


def _generate_text_area_widget(
    input_format: str,
    content: dict,
    editable: bool = True,
) -> Optional[str]:
    """
    Generate a text area input field.

    Parameters
    ----------
    input_format : str
        The input format.
    content : dict
        The content of the text area.
    editable : bool
        Whether the text area is editable.

    Returns
    -------
    Any
        The text area input field.
    """
    placeholder = content.get("placeholder")
    value = content.get("value", {}).get(input_format)
    height = content.get("height", 200)
    ret = st.text_area(
        content["label"],
        placeholder=placeholder,
        value=value,
        height=height,
        disabled=not editable,
    )
    return ret


def _generate_text_input(
    variables_quant, input_format: str, content: dict, key: str = "", editable: bool = True
) -> Optional[str]:
    """
    Generate a text input field.

    Parameters
    ----------
    input_format : str
        The input format.
    content : dict
        The content of the text input field.
    key : str
        The key of the text input field.

    Returns
    -------
    Any
        The text input field: str or None
    """
    placeholder = content.get("placeholder")
    if key in st.session_state[variables_quant.params_file_dict].keys():
        value = st.session_state[variables_quant.params_file_dict].get(key)  # Get parsed value if available
    else:
        value = content.get("value", {}).get(input_format)

    return st.text_input(
        content["label"],
        placeholder=placeholder,
        key=variables_quant.prefix_params + key,
        value=value,
        on_change=update_parameters_submission_form(
            variables_quant, key, st.session_state.get(variables_quant.prefix_params + key, 0)
        ),
        disabled=not editable,
    )


def _generate_number_input(
    variables_quant,
    content: dict,
    key: str = "",
    editable: bool = True,
) -> Any:
    """
    Generate a number input field.

    Parameters
    ----------
    content : dict
        The content of the number input field.
    key : str
        The key of the number input field.
    editable : bool
        Whether the number input field is editable.

    Returns
    -------
    Any
        The number input field: int or float or None
    """
    if key in st.session_state[variables_quant.params_file_dict].keys():
        value = st.session_state[variables_quant.params_file_dict].get(key)  # Get parsed value if available
    else:
        value = content.get("value", {}).get("min_value")
    return st.number_input(
        content["label"],
        value=value,
        key=variables_quant.prefix_params + key,
        format=content["format"],
        min_value=content["min_value"],
        max_value=content["max_value"],
        on_change=update_parameters_submission_form(
            variables_quant, key, st.session_state.get(variables_quant.prefix_params + key, 0)
        ),
        disabled=not editable,
    )


def _generate_selectbox(
    variables_quant,
    input_format: str,
    content: dict,
    key: str = "",
    editable: bool = True,
) -> Any:
    """
    Generate a selectbox input field.

    Parameters
    ----------
    input_format : str
        The input format.
    content : dict
        The content of the selectbox.
    key : str
        The key of the selectbox.
    editable : bool
        Whether the selectbox is editable.

    Returns
    -------
    Any
        The selectbox input field or None.
    """
    options = content.get("options", [])
    if key in st.session_state[variables_quant.params_file_dict].keys():
        value = st.session_state[variables_quant.params_file_dict].get(key)  # Get parsed value if available
    else:
        value = content.get("value", {}).get(input_format)
    index = options.index(value) if value in options else 0

    return st.selectbox(
        content["label"],
        options,
        key=variables_quant.prefix_params + key,
        index=index,
        on_change=update_parameters_submission_form(
            variables_quant, key, st.session_state.get(variables_quant.prefix_params + key, 0)
        ),
        disabled=not editable,
    )


def _generate_checkbox(variables_quant, content: dict, key: str = "", editable: bool = True) -> bool:
    """
    Generate a checkbox input field.

    Parameters
    ----------
    content : dict
        The content of the checkbox.
    key : str
        The key of the checkbox.
    editable : bool
        Whether the checkbox is editable.

    Returns
    -------
    Any
        The checkbox input field.
    """
    value = content.get("value", {})
    if key in st.session_state[variables_quant.params_file_dict].keys():
        value = st.session_state[variables_quant.params_file_dict].get(key)
    return st.checkbox(
        content["label"],
        key=variables_quant.prefix_params + key,
        value=value,
        on_change=update_parameters_submission_form(
            variables_quant, key, st.session_state.get(variables_quant.prefix_params + key, 0)
        ),
        disabled=not editable,
    )
