"""Base classes for psm_utils online Streamlit web server."""

from abc import ABC, abstractmethod

import streamlit as st


class StreamlitPage(ABC):
    """Base class for psm_utils online Streamlit web server."""

    def __init__(self) -> None:
        self.state = st.session_state

        st.set_page_config(
            page_title="psm_utils online",
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
            # psm_utils online

            [![GitHub release](https://img.shields.io/github/v/release/compomics/psm_utils?include_prereleases&sort=semver&style=flat-square)](https://github.com/compomics/psm_utils/releases)
            [![GitHub](https://img.shields.io/github/license/compomics/psm_utils?style=flat-square)](https://github.com/compomics/psm_utils/blob/main/LICENSE)
            [![Twitter Follow](https://img.shields.io/twitter/follow/CompOmics?style=flat-square)](https://twitter.com/compomics)

            psm_utils is a Python package with utilities for parsing and handling
            peptide-spectrum matches (PSMs) and proteomics search engine results. It is
            mainly developed to be used in Python packages developed at CompOmics, such
            as [MS²PIP](https://github.com/compomics/ms2pip_c/),
            [DeepLC](https://github.com/compomics/deeplc/), and
            [MS²Rescore](https://github.com/compomics/ms2rescore/),
            but can be useful to anyone dealing with PSMs and PSM files.

            This web server is built on top of
            **[psm_utils](https://psm-utils.readthedocs.io/)** and allows you to easily
            get **PSM statistics** for any supported PSM file type, and to **convert
            search engine results** from one PSM file format into another.
            """
        )
