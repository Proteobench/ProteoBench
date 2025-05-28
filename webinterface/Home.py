"""Proteobench Streamlit-based web server."""

import streamlit as st
from _base import StreamlitPage
from WI_utils import get_n_modules, get_n_submitted_points, get_n_supported_tools


class StreamlitPageHome(StreamlitPage):
    """
    This class sets up the main page layout for the Streamlit application.
    """

    @staticmethod
    def stat_box(title, value, icon, color):
        return f"""
            <div style="
                background-color: #ffffff;
                border-radius: 12px;
                padding: 16px 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                display: flex;
                align-items: center;
                height: 100px;
            ">
                <div style="
                    font-size: 28px;
                    margin-right: 16px;
                    color: {color};
                ">{icon}</div>
                <div>
                    <div style='font-size: 14px; color: #666;'>{title}</div>
                    <div style='font-size: 24px; font-weight: 600; color: #222;'>{value}</div>
                </div>
            </div>
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

        # First row
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown(
                self.stat_box("Number of modules (total)", n_modules_all, "🧩", "#37475E"), unsafe_allow_html=True
            )
        with row1_col2:
            st.markdown(
                self.stat_box("Number of modules (expert validated)", n_modules_reviewed, "✅", "#37475E"),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
        # Second row
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown(
                self.stat_box("Number of tools supported", n_tools_supported, "🔨", "#37475E"), unsafe_allow_html=True
            )
        with row2_col2:
            st.markdown(
                self.stat_box("Number of submitted points", n_of_points_submitted, "⭕", "#37475E"),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

        # Third row
        row3 = st.columns(1)
        with row3[0]:
            st.markdown(self.stat_box("Monthly visitors", monthly_visitors, "🌐", "#37475E"), unsafe_allow_html=True)


if __name__ == "__main__":
    StreamlitPageHome()
