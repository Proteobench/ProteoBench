"""Proteobench Streamlit-based web server."""

import streamlit as st
from _base import StreamlitPage
from WI_utils import (
    get_n_modules,
    get_n_submitted_points,
    get_n_supported_tools,
    stat_box,
)


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
        n_modules_reviewed = "Coming soon"  # Since we don't have a review system and banner in place yet
        n_tools_supported = get_n_supported_tools()
        n_of_points_submitted = get_n_submitted_points()  # This function should return the number of submitted points
        monthly_visitors = "Coming soon"  # TODO

        st.header("ProteoBench Overview")
        st.markdown(
            """
        <style>
        .row-container {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }

        .row-container > div {
            flex: 1;
            display: flex;
        }

        .stat-card-glass {
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.6);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: center;
        }
        .stat-card-glass h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .stat-card-glass .metric {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        .stat-card-glass .icon {
            font-size: 2rem;
            margin-bottom: 10px;
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
                    "Number of modules (total)",
                    n_modules_all,
                    "🧩",
                    "#37475E",
                    "https://proteobench.readthedocs.io/en/stable/available-modules/",
                ),
                unsafe_allow_html=True,
            )
        with row1_col2:
            st.markdown(
                stat_box(
                    "Number of modules (expert validated)",
                    n_modules_reviewed,
                    "✅",
                    "#37475E",
                    # TODO: link to expert validation docs
                ),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
        # Second row
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown(
                stat_box(
                    "Number of tools supported",
                    n_tools_supported,
                    "🔨",
                    "#37475E",
                    # TODO: parameter parsing docs url
                ),
                unsafe_allow_html=True,
            )
        with row2_col2:
            st.markdown(
                stat_box(
                    "Number of submitted points",
                    n_of_points_submitted,
                    "⭕",
                    "#37475E",
                    "https://proteobench.cubimed.rub.de/datasets/",
                ),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

        # Third row
        row3 = st.columns(1)
        with row3[0]:
            st.markdown(stat_box("Monthly visitors", monthly_visitors, "🌐", "#37475E"), unsafe_allow_html=True)


if __name__ == "__main__":
    StreamlitPageHome()
