"""Base classes for psm_utils online Streamlit web server."""

from abc import ABC, abstractmethod

import streamlit as st
from st_pages import show_pages_from_config


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
            [proteobench.readthedocs.io](https://proteobench.readthedocs.io/en/latest/)**<br>
            **💻 Find the source code on
            [github.com](https://github.com/Proteobench/Proteobench)**<br>

            **ProteoBench is a project initiated and maintained by [EuBIC-MS](https://eubic-ms.org/). Please [join us](https://eubic-ms.org/become-a-member/) and contribute!**<br>

            **If you still have questions, you can email us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query)**

            
            """,
            unsafe_allow_html=True,
        )
        st.image("logos/logo_participants/logos_all.png")
        st.markdown(
            """
            This site is hosted by the BMBF-funded de.NBI Cloud within the German Network for Bioinformatics Infrastructure (de.NBI)
            """
        )

    @abstractmethod
    def _main_page(self):
        raise NotImplementedError()

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image("logos/logo_funding/main_logos_sidebar.png", width=300)
