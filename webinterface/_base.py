"""Base classes for psm_utils online Streamlit web server."""

from abc import ABC, abstractmethod

import streamlit as st


class StreamlitPage(ABC):
    """Base class for Proteobench online Streamlit web server."""

    def __init__(self) -> None:
        self.state = st.session_state

        st.set_page_config(
            page_title="Proteobench",
            page_icon=":rocket:",
            layout="centered",
            initial_sidebar_state="expanded",
        )

        self._preface()
        self._main_page()
        self._sidebar()

    def _preface(self):
        st.markdown(
            """
            # Proteobench

            **👈 Select a page from the sidebar to get started!**<br>
            **📖 Learn more about Proteobench on
            [Proteobench.io](https://github.com/Proteobench/Proteobench)**<br>
            **💻 Find the source code on
            [github.com](https://github.com/Proteobench/Proteobench)**<br>
            """,
            unsafe_allow_html=True,
        )

    @abstractmethod
    def _main_page(self):
        raise NotImplementedError()

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.markdown(
            """
            # Proteobench
            """
        )
