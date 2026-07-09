"""Base classes for ProteoBench online Streamlit web server."""

import os
from abc import ABC, abstractmethod

import pages.texts.proteobench_builder as pbb
import streamlit as st

import proteobench

# 8-byte PNG file signature.
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _resolve_asset(path: str) -> str:
    """Resolve an asset path, materializing git symlinks checked out as text.

    On Windows checkouts without symlink support (``core.symlinks=false``), git
    writes a symlink as a small text file containing the link target instead of
    a real symlink. Streamlit/PIL then fail to read it as an image. Detect that
    case and return the resolved target path; otherwise return ``path``
    unchanged.

    Parameters
    ----------
    path : str
        Path to the asset, relative to the current working directory.

    Returns
    -------
    str
        The original path, or the resolved symlink-target path when the file is
        a text pointer to an existing target.
    """
    try:
        with open(path, "rb") as handle:
            head = handle.read(len(_PNG_SIGNATURE))
    except OSError:
        return path
    # A real PNG (the symlink correctly followed) starts with the signature.
    if head.startswith(_PNG_SIGNATURE):
        return path
    # Otherwise treat the file content as a (relative) symlink target.
    try:
        with open(path, "r", encoding="utf-8") as handle:
            target = handle.read().strip()
    except (OSError, UnicodeDecodeError):
        return path
    if not target:
        return path
    candidate = os.path.normpath(os.path.join(os.path.dirname(path), target))
    return candidate if os.path.isfile(candidate) else path


# Why does it exist? We only have one Page defined
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
        pbb.proteobench_sidebar(current_page="/")

        # Auth: handle callback, show user badge in header
        from pages.base_pages.utils.auth import render_auth_home, render_oauth_success_banner

        render_auth_home()

        # If this tab was opened solely to complete an OAuth sign-in, show a banner
        # telling the user they can close it. We intentionally keep rendering the
        # full Home page below (rather than replacing it): the full render is what
        # reliably lets the sign-in cookie reach the browser so the user's other
        # tab picks it up. A minimal replacement page broke that.
        render_oauth_success_banner()

        self._preface()

        self._main_page()
        self._logos()

    def _preface(self):
        """
        Set up the preface of the Streamlit application.
        """
        st.markdown(
            f"""
            # Welcome to ProteoBench

            **👈 Select a page from the sidebar to get started!**<br>
            **📖 Learn more about Proteobench on
            [proteobench.readthedocs.io](https://proteobench.readthedocs.io/)**<br>
            **💻 Find the source code on
            [github.com](https://github.com/Proteobench/Proteobench)**<br>
            **📄 Find the manuscript on [biorXiv](https://doi.org/10.64898/2025.12.09.692895)**<br>

            **ProteoBench is a project initiated and maintained by [EuBIC-MS](https://eubic-ms.org/). Please [join us](https://eubic-ms.org/become-a-member/) and contribute!**<br>

            **If you still have questions, you can email us [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query)**

            Using proteobench version: {getattr(proteobench, "__version__", "unknown")}
            """,
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
        st.image(_resolve_asset("logos/logo_participants/proteobench-contributing-institutes.png"))
