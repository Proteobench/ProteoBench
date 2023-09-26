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
        logo_list = [
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/ADlab.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/CBMR.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/MetaproteomicsInitiative.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/ULaval.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/Viki_FH%20Logo%20international%20mit%20University_jpg.jpg?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/logo_UGent_EN_RGB_2400_color-on-white.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/netherlands-escience-center-logo-RGB.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/sdulogo_da.png?raw=true",
            "https://github.com/Proteobench/ProteoBench/blob/Add-logos/webinterface/logos/logo_participants/vib.png?raw=true"
        ]

        for i in range(0,len(logo_list),3):
            st.sidebar.image(
                logo_list[i:i+3],
                width=75,
            )
