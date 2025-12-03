import streamlit as st


# We do not have an abstract data class for variables yet, but
# it is the one initialized in the pages_variables/Quant folder
def display_banner(variables):
    if variables.archived_warning:
        st.info(variables.texts.ShortMessages.warning_archived)
    else:
        if variables.alpha_warning:
            st.warning(
                variables.texts.ShortMessages.warning_alpha,
                icon="🚨",
            )
        if variables.beta_warning:
            st.warning(variables.texts.ShortMessages.warning_beta)
