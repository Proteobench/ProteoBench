"""Streamlit utils."""

import logging

import streamlit as st


class StreamlitLogger:
    """
    Pickup logger and write to Streamlit front end.

    Parameters
    ----------
        placeholder : streamlit.empty
            Streamlit placeholder object on which to write logs.
        logger_name : str, optional
            Module name of logger to pick up. Leave to None to pick up root logger.
        accumulate : bool, optional
            Whether to accumulate log messages or to overwrite with each new
            message, keeping only the last line (default: True).
        persist : bool, optional
            Wheter to keep the log when finished, or empty the placeholder element.
    """

    def __init__(self, placeholder, logger_name=None, accumulate=True, persist=True):
        """
        Pickup logger and write to Streamlit front end.

        Parameters
        ----------
            placeholder : streamlit.empty
                Streamlit placeholder object on which to write logs.
            logger_name : str, optional
                Module name of logger to pick up. Leave to None to pick up root logger.
            accumulate : bool, optional
                Whether to accumulate log messages or to overwrite with each new
                message, keeping only the last line (default: True).
            persist : bool, optional
                Wheter to keep the log when finished, or empty the placeholder element.
        """
        self.placeholder = placeholder
        self.persist = persist

        self.logging_stream = _StreamlitLoggingStream(placeholder, accumulate)
        self.handler = logging.StreamHandler(self.logging_stream)
        self.logger = logging.getLogger(logger_name)

    def __enter__(self):
        """
        Add handler to logger.

        Returns
        -------
            StreamlitLogger
                The StreamlitLogger object.
        """
        self.logger.addHandler(self.handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Remove handler from logger and empty placeholder.

        Parameters
        ----------
            exc_type : type
                Exception type.
            exc_val : Exception
                Exception value.
            exc_tb : traceback
                Traceback.
        """
        self.logger.removeHandler(self.handler)
        if not self.persist:
            self.placeholder.empty()


class _StreamlitLoggingStream:
    """
    Logging stream that writes logs to Streamlit front end.

    Parameters
    ----------
        placeholder : streamlit.empty
            Streamlit placeholder object on which to write logs.
        accumulate : bool, optional
            Whether to accumulate log messages or to overwrite with each new
            message, keeping only the last line (default: True).
    """

    def __init__(self, placeholder, accumulate=True):
        """
        Logging stream that writes logs to Streamlit front end.

        Parameters
        ----------
            placeholder : streamlit.empty
                Streamlit placeholder object on which to write logs.
            accumulate : bool, optional
                Whether to accumulate log messages or to overwrite with each new
                message, keeping only the last line (default: True).
        """
        self.placeholder = placeholder
        self.accumulate = accumulate
        self.message_list = []

    def write(self, message):
        """
        Write message to Streamlit front end.

        Parameters
        ----------
            message : str
                Message to write to Streamlit front end.

        Returns
        -------
            None
        """

        if self.accumulate:
            self.message_list.append(message)
        else:
            self.message_list = [message]
        self.placeholder.markdown("```\n" + "".join(self.message_list) + "\n```")


def hide_streamlit_menu():
    """
    Hide Streamlit menu.
    """
    hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


@st.cache_data
def save_dataframe(df):
    """
    Save dataframe to file object, with streamlit cache.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to save.

    Returns
    -------
    bytes
        The CSV representation of the dataframe encoded in UTF-8.
    """
    return df.to_csv().encode("utf-8")


def display_error(
    friendly_message: str,
    exception: Exception = None,
    suggestions: list = None,
    technical_details: str = None,
):
    """
    Display user-friendly error with expandable technical details.

    Parameters
    ----------
    friendly_message : str
        A user-friendly error message to display prominently.
    exception : Exception, optional
        The exception object to show with Streamlit's nice traceback formatting.
    suggestions : list, optional
        List of suggestions to help the user resolve the error.
    technical_details : str, optional
        Technical error details as string (used if exception is not provided).
    """
    st.error(f":x: {friendly_message}", icon="🚨")

    if suggestions:
        suggestions_text = "\n".join(f"- {s}" for s in suggestions)
        st.info(f"**Suggestions:**\n{suggestions_text}")

    if exception is not None:
        with st.expander("Technical details"):
            st.exception(exception)
    elif technical_details:
        with st.expander("Technical details"):
            st.code(technical_details)


def get_error_suggestions(exception: Exception, context: dict) -> tuple:
    """
    Analyze exception and return user-friendly message with suggestions.

    Parameters
    ----------
    exception : Exception
        The exception that was raised.
    context : dict
        Context about the operation, including 'input_format' for the selected software tool.

    Returns
    -------
    tuple
        A tuple of (friendly_message, suggestions_list).
    """
    error_str = str(exception)
    error_type = type(exception).__name__
    suggestions = []

    # Missing raw files / wrong dataset - this is a specific, identifiable error
    if "Not all runs are present" in error_str:
        friendly = "The uploaded file doesn't contain all expected sample names"
        suggestions.append("Ensure you processed the correct benchmark dataset for this module")
        suggestions.append("Check the module documentation for the expected raw file names")
        suggestions.append("Verify you are using the correct module for your instrument type")

    # Invalid input format - user selected a tool but uploaded a file from a different tool
    elif "Invalid input format" in error_str:
        friendly = "The uploaded file format doesn't match the selected software tool"
        suggestions.append("Verify you selected the correct software tool from the dropdown")
        suggestions.append("Ensure the uploaded file was generated by the selected tool")

    # File format / parsing errors - broad category for many issues
    elif any(
        pattern in error_str
        for pattern in [
            "Error tokenizing data",
            "Expected 1 fields",
            "ParserError",
            "could not convert",
            "Unable to parse",
        ]
    ) or error_type in ["ParserError", "ValueError", "TypeError"]:
        friendly = "The file format doesn't match the selected software tool"
        suggestions.append("Check that you selected the correct software tool for your file")
        suggestions.append("Verify the file is a complete, unmodified output from the software")
        suggestions.append("Refer to the module documentation for supported file formats")

    # Missing required columns
    elif "KeyError" in error_str or "not in index" in error_str.lower() or error_type == "KeyError":
        friendly = "The file is missing required columns"
        suggestions.append("Verify the file is a complete output from the selected software tool")
        suggestions.append("Check that the file was not modified after export")
        suggestions.append("Ensure you selected the correct software tool")

    # Generic fallback - assume file format issue as most common cause
    else:
        friendly = "The file format doesn't match the selected software tool"
        suggestions.append("Check that you selected the correct software tool for your file")
        suggestions.append("Verify the file is a complete, unmodified output from the software")
        suggestions.append("Refer to the module documentation for supported file formats")

    return friendly, suggestions
