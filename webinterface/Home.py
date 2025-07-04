"""Proteobench Streamlit-based web server."""

from pathlib import Path

import streamlit as st
from _base import StreamlitPage
from UI_utils import (
    get_n_modules,
    get_n_modules_proposed,
    get_n_submitted_points,
    get_n_supported_tools,
    stat_box,
)

# Path to the index.rst file
file_path = Path(__file__).parent.parent / "docs" / "index.rst"
fig_path = Path(__file__).parent.parent / "img" / "icons" / "png"  # Adjusted to match the new structure


class StreamlitPageHome(StreamlitPage):
    """
    This class sets up the main page layout for the Streamlit application.
    """

    def _main_page(self):
        """
        Set up the main page layout for the Streamlit application.
        """
        # Placeholders TODO: replace with actual data

        n_modules_all = get_n_modules()
        n_modules_proposed = get_n_modules_proposed(file_path.read_text(encoding="utf-8"))
        n_tools_supported = get_n_supported_tools()
        n_of_points_submitted = get_n_submitted_points()  # This function should return the number of submitted points
        monthly_visitors = "Coming soon"  # TODO

        st.header("ProteoBench Overview")
        st.markdown(
            """
    <style>
    .stat-card-glass {
        backdrop-filter: blur(10px);
        background: rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 12px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
    }
    .stat-card-glass h3 {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .stat-card-glass .metric {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    .stat-card-glass .icon {
        font-size: 1.8rem;
        margin-bottom: 8px;
    }
    </style>
    """,
            unsafe_allow_html=True,
        )

        # First row
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown(
                stat_box(
                    "Active modules",
                    n_modules_all,
                    fig_path / "module.png",
                    "https://proteobench.readthedocs.io/en/stable/available-modules/",
                ),
                unsafe_allow_html=True,
            )
        with row1_col2:
            st.markdown(
                stat_box(
                    "Proposed and in-development modules",
                    n_modules_proposed,
                    fig_path / "module-construction.png",
                    "https://github.com/orgs/Proteobench/discussions",
                ),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
        # Second row
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown(
                stat_box(
                    "Supported workflows and tools",
                    n_tools_supported,
                    fig_path / "workflow-run.png",
                    # TODO: parameter parsing docs url
                ),
                unsafe_allow_html=True,
            )
        with row2_col2:
            st.markdown(
                stat_box(
                    "Submitted points",
                    n_of_points_submitted,
                    fig_path / "scatter-plot.png",
                    "https://proteobench.cubimed.rub.de/datasets/",
                ),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

        # Third row
        row3 = st.columns(1)
        with row3[0]:
            st.markdown(stat_box("Monthly visitors", monthly_visitors, fig_path / "user.png"), unsafe_allow_html=True)


if __name__ == "__main__":
    StreamlitPageHome()
