"""Submission-source helpers for the ProteoBench web interface.

These functions live in the interface layer rather than the core library because
they depend on Streamlit secrets to detect whether the app is running on the
official ProteoBench server. See issue #992 (decoupling Streamlit from the
benchmark logic).
"""

import streamlit as st


def is_official_server() -> bool:
    """Check if running on the official ProteoBench server.

    Uses the presence of storage configuration in Streamlit secrets as the
    signal; only the production server has this configured.

    Returns
    -------
    bool
        True if running on the official server, False otherwise.
    """
    try:
        return "storage" in st.secrets.keys()
    except FileNotFoundError:
        return False


def get_submission_source() -> str:
    """Return the submission source based on where the app is running.

    Returns
    -------
    str
        ``"web-server"`` when running on the official server, otherwise ``"local"``.
    """
    return "web-server" if is_official_server() else "local"
