import uuid

import streamlit as st


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
