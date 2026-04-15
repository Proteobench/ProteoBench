"""Proteobench Streamlit-based web server."""

from pathlib import Path

import streamlit as st
from _base import StreamlitPage
from UI_utils import (
    get_monthly_visitors,
    get_n_modules,
    get_n_modules_proposed,
    get_n_submitted_points,
    get_n_supported_tools,
    stat_box,
)

# Path to the index.rst file
file_path = Path(__file__).resolve().parent.parent / "docs" / "index.rst"
fig_path = Path(__file__).resolve().parent.parent / "img" / "icons" / "png"  # Adjusted to match the new structure


class StreamlitPageHome(StreamlitPage):
    """
    This class sets up the main page layout for the Streamlit application.
    """

    def _main_page(self):
        """
        Set up the main page layout for the Streamlit application.
        """
        n_modules_all = get_n_modules()
        n_modules_proposed = get_n_modules_proposed(file_path.read_text(encoding="utf-8"))
        n_tools_supported = get_n_supported_tools()
        n_of_points_submitted = get_n_submitted_points()  # This function should return the number of submitted points

        if (
            "tracking" in st.secrets
            and "matomo_endpoint" in st.secrets["tracking"]
            and "matomo_idsite" in st.secrets["tracking"]
            and "matomo_token" in st.secrets["tracking"]
        ):
            monthly_uniq_visitors = get_monthly_visitors(
                st.secrets["tracking"]["matomo_endpoint"],
                st.secrets["tracking"]["matomo_token"],
                st.secrets["tracking"]["matomo_idsite"],
            )
        else:
            monthly_uniq_visitors = "not configured"

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
                    url="https://proteobench.readthedocs.io/en/stable/available-modules/",
                ),
                unsafe_allow_html=True,
            )
        with row1_col2:
            st.markdown(
                stat_box(
                    "Proposed and in-development modules",
                    n_modules_proposed,
                    fig_path / "module-construction.png",
                    url="https://github.com/orgs/Proteobench/discussions",
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
                    url="https://proteobench.readthedocs.io/en/stable/available-modules/12-parsed-parameters-for-public-submission/",
                ),
                unsafe_allow_html=True,
            )
        with row2_col2:
            st.markdown(
                stat_box(
                    "Submitted points",
                    n_of_points_submitted,
                    fig_path / "scatter-plot.png",
                    url="https://proteobench.cubimed.rub.de/datasets/",
                ),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

        # Third row
        row3 = st.columns(1)
        with row3[0]:
            st.markdown(
                stat_box("Monthly unique visitors", monthly_uniq_visitors, fig_path / "user.png"),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Sign-in banner + leaderboard section
        from pages.base_pages.utils.auth import render_signin_banner

        render_signin_banner()
        _render_leaderboard()


def _render_leaderboard():
    """Render the top submitters leaderboard section."""
    import pandas as pd

    # TODO: Remove mock data once real submissions exist
    # from pages.base_pages.utils.leaderboard import get_leaderboard_data
    # leaderboard = get_leaderboard_data()
    leaderboard = pd.DataFrame(
        {
            "submitter_id": [
                "rodvrees",
                "0000-0002-1825-0097",
                "jdoe42",
                "0000-0001-5678-1234",
                "labuser",
                "asmith",
                "0000-0003-9876-5432",
                "mbrown",
                "0000-0004-1111-2222",
                "ljohnson",
            ],
            "submitter_name": [
                "Robbin Bouwmeester",
                "Jane Doe",
                "John Doe",
                "Maria Garcia",
                "Lab Account",
                "Alice Smith",
                "Bob Johnson",
                "Charlie Brown",
                "David Wilson",
                "Eva Davis",
            ],
            "submitter_provider": [
                "github",
                "orcid",
                "github",
                "orcid",
                "github",
                "orcid",
                "github",
                "orcid",
                "github",
                "orcid",
            ],
            "submissions": [23, 17, 12, 8, 3, 2, 1, 1, 1, 1],
        }
    )

    if leaderboard.empty:
        return

    st.header("Top Submitters")
    st.caption("Users who have submitted benchmark runs while signed in with GitHub or ORCID.")

    # Pagination
    page_size = 7
    total = len(leaderboard)
    total_pages = max(1, (total + page_size - 1) // page_size)

    if "leaderboard_page" not in st.session_state:
        st.session_state["leaderboard_page"] = 0

    page = st.session_state["leaderboard_page"]
    start = page * page_size
    end = min(start + page_size, total)
    page_data = leaderboard.iloc[start:end]

    max_subs = leaderboard["submissions"].max()
    medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}
    bar_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}

    for i, row in zip(range(start + 1, end + 1), page_data.itertuples()):
        medal = medals.get(i, f"#{i}")
        color = bar_colors.get(i, "#89A2EE")
        bar_pct = max(int((row.submissions / max_subs) * 100), 15) if max_subs else 15
        provider_icon = "GitHub" if row.submitter_provider == "github" else "ORCID"

        st.markdown(
            f'<div style="background:linear-gradient(90deg, {color} {bar_pct}%, #f0f0f0 {bar_pct}%);'
            f"border-radius:10px;padding:12px 18px;margin-bottom:6px;"
            f'display:flex;align-items:center;justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;gap:12px;">'
            f'<span style="font-size:1.6rem;">{medal}</span>'
            f'<div><span style="font-weight:700;font-size:1.05rem;">{row.submitter_name}</span>'
            f'<br><span style="font-size:0.75rem;color:#555;">{provider_icon}</span></div>'
            f"</div>"
            f'<span style="font-weight:700;font-size:1.1rem;color:#222;">{row.submissions}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # Navigation buttons
    if total_pages > 1:
        nav_left, nav_center, nav_right = st.columns([1, 2, 1])
        with nav_left:
            if st.button("\u25c0 Previous", disabled=(page == 0), key="lb_prev"):
                st.session_state["leaderboard_page"] = page - 1
                st.rerun()
        with nav_center:
            st.markdown(
                f'<div style="text-align:center;padding-top:6px;color:#666;">Page {page + 1} of {total_pages}</div>',
                unsafe_allow_html=True,
            )
        with nav_right:
            if st.button("Next \u25b6", disabled=(page >= total_pages - 1), key="lb_next"):
                st.session_state["leaderboard_page"] = page + 1
                st.rerun()


if __name__ == "__main__":
    StreamlitPageHome()
