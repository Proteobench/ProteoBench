"""Base classes for psm_utils online Streamlit web server."""

from abc import ABC, abstractmethod

import streamlit as st
from st_pages import show_pages_from_config

import proteobench


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
        show_pages_from_config()

    def _preface(self):
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
        st.image("logos/logo_participants/logos_all.png")

        # add hosting information if provided
        if "hosting" in st.secrets.keys():
            st.markdown(st.secrets["hosting"]["information"])

    @abstractmethod
    def _main_page(self):
        raise NotImplementedError()

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image("logos/logo_funding/main_logos_sidebar.png", width=300)

        # add gdpr links if provided
        if "gdpr_links" in st.secrets.keys():
            st.sidebar.page_link(st.secrets["gdpr_links"]["privacy_notice_link"], label="-> privacy notice")
            st.sidebar.page_link(st.secrets["gdpr_links"]["legal_notice_link"], label="-> legal notice")
