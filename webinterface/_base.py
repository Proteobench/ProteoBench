"""Base classes for ProteoBench online Streamlit web server."""

from abc import ABC, abstractmethod

import pages.texts.proteobench_builder as pbb
import streamlit as st

import proteobench


class StreamlitPage(ABC):
    """
    Base class for Proteobench online Streamlit web server.
    """

    def __init__(self) -> None:
        """
        Initialize the Proteobench online Streamlit web server.
        """
        self.state = st.session_state

        pbb.proteobench_page_config(page_layout="centered")
        # Hide the default page navigation
        st.markdown(
            """
            <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        pbb.proteobench_sidebar(current_page="/")

        self._preface()
        self._main_page()
        self._logos()

    def _preface(self):
        """
        Set up the preface of the Streamlit application.
        """
        st.markdown(
            """
            # Welcome to ProteoBench

            **👈 Select a page from the sidebar to get started!**<br>
            **📖 Learn more about Proteobench on
            [proteobench.readthedocs.io](https://proteobench.readthedocs.io/)**<br>
            **💻 Find the source code on
            [github.com](https://github.com/Proteobench/Proteobench)**<br>

            **ProteoBench is a project initiated and maintained by [EuBIC-MS](https://eubic-ms.org/). Please [join us](https://eubic-ms.org/become-a-member/) and contribute!**<br>

            **If you still have questions, you can email us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query)**

            Using proteobench version: {}
            """.format(
                proteobench.__version__
            ),
            unsafe_allow_html=True,
        )

        # add hosting information if provided
        try:
            if "hosting" in st.secrets.keys():
                st.markdown(st.secrets["hosting"]["information"])
        except FileNotFoundError:
            # Would be preffered if we can keep this information elsewhere or
            # provide a default config file
            pass

    @abstractmethod
    def _main_page(self):
        """
        Set up the main page layout for the Streamlit application.
        """
        raise NotImplementedError()

    def _logos(self):
        """
        Set up the logos for the Streamlit application.
        """
        # Add newline
        st.markdown("<br>", unsafe_allow_html=True)
        st.image("logos/logo_participants/proteobench-contributing-institutes.png")
