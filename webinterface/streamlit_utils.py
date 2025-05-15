"""Streamlit utils."""

import logging

import streamlit as st
from typing_extensions import get_origin


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
