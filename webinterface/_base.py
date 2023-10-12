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
        st.image("webinterface/logos/logo_participants/logos_all_20230926.png")

    @abstractmethod
    def _main_page(self):
        raise NotImplementedError()

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image("https://github.com/Proteobench/ProteoBench/raw/Add-logos/webinterface/logos/logo_proteobench/proteobench-logo-horizontal.svg",
                width=300)
        st.sidebar.image("https://raw.githubusercontent.com/Proteobench/ProteoBench/b6d40e853df10e486e0000aed9fe7b5ddc3f9286/webinterface/logos/logo_funding/DDSA_PrimaryLogo_Screen_Black.svg",
                width=300)
        mainlogo_list = [
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_funding/eubic_logo_transparent.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_funding/eupa-logo-transparent.png?raw=true"
        ]
        for i in range(0,len(mainlogo_list),3):
            st.sidebar.image(
                mainlogo_list[i:i+3],
                width=140,
            )
