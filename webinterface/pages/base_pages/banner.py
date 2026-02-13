import streamlit as st


# We do not have an abstract data class for variables yet, but
# it is the one initialized in the pages_variables/Quant folder
def display_banner(variables):
    """Display a banner with warnings based on the variables provided on each tab
    of the Quant modules."""
    if variables.archived_warning:
        st.info(variables.texts.ShortMessages.warning_archived)
    else:
        if variables.alpha_warning:
            st.warning(
                variables.texts.ShortMessages.warning_alpha,
                icon="🚨",
            )
        elif variables.beta_warning:
            st.warning(variables.texts.ShortMessages.warning_beta)
