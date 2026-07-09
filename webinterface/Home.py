"""Proteobench Streamlit-based web server."""

from pathlib import Path

import streamlit as st
from _base import StreamlitPage
from pages.base_pages.tour_steps import get_homepage_tour_steps

# Optional guided-tour overlay; disable gracefully if streamlit_tour cannot be
# imported (e.g. version-incompatible with the installed streamlit). See base.py.
try:
    from streamlit_tour import Tour
except Exception:  # noqa: BLE001 - any import/component-registration failure
    Tour = None
from UI_utils import (
    build_submissions_figure,
    build_tool_pie_chart,
    get_monthly_visits,
    get_n_modules,
    get_n_modules_proposed,
    get_n_submitted_points,
    get_n_supported_tools,
    stat_box,
)


@st.dialog("Tool Breakdown", width="large")
def _show_tool_breakdown(module_title, tool_counts):
    pie_fig = build_tool_pie_chart(module_title, tool_counts)
    st.plotly_chart(pie_fig, use_container_width=True)


fig_path = Path(__file__).resolve().parent.parent / "img" / "icons" / "png"  # Adjusted to match the new structure


class StreamlitPageHome(StreamlitPage):
    """
    This class sets up the main page layout for the Streamlit application.
    """

    # overwrites _main_page from StreamlitPage
    # is called by initializer along sidebar and other setup
    def _main_page(self):
        """
        Set up the main page layout for the Streamlit application.
        """
        # Navigate to DIA Astral when the homepage tour ends (finish or dismiss).
        _home_tour_key = "onboarding_home"
        _home_tour_active = f"stTour--{_home_tour_key}-active"
        if st.session_state.get("_home_tour_in_progress", False) and not st.session_state.get(_home_tour_active, False):
            st.session_state.pop("_home_tour_in_progress", None)
            st.switch_page("pages/6_Quant_LFQ_DIA_ion_Astral.py")

        # Placeholders TODO: replace with actual data

        n_modules_all = get_n_modules()
        n_modules_proposed = get_n_modules_proposed()
        n_tools_supported = get_n_supported_tools()
        n_of_points_submitted = get_n_submitted_points()  # This function should return the number of submitted points

        if (
            "tracking" in st.secrets
            and "matomo_endpoint" in st.secrets["tracking"]
            and "matomo_idsite" in st.secrets["tracking"]
            and "matomo_token" in st.secrets["tracking"]
        ):
            monthly_visits = get_monthly_visits(
                st.secrets["tracking"]["matomo_endpoint"],
                st.secrets["tracking"]["matomo_token"],
                st.secrets["tracking"]["matomo_idsite"],
            )
        else:
            monthly_visits = "not configured"

        if st.sidebar.button("Take a Tour", key="home_tour_trigger"):
            st.session_state["start_home_tour"] = True

        st.header("ProteoBench Overview")

        if "_tour_opted_in" not in st.session_state:
            with st.container(border=True):
                col_text, col_yes, col_no = st.columns([7, 2, 1.5])
                with col_text:
                    st.markdown(
                        "**Want a quick guided tour?** We will walk you through a benchmark module step by step."
                    )
                with col_yes:
                    if st.button("Yes, show me!", type="primary", use_container_width=True, key="tour_opt_in_yes"):
                        st.session_state["_tour_opted_in"] = True
                        st.rerun()
                with col_no:
                    if st.button("No, thanks!", use_container_width=True, key="tour_opt_in_no"):
                        st.session_state["_tour_opted_in"] = False
                        st.rerun()

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

        with st.container(key="tour_stats_area"):
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
                        "Modules in discussion or in development",
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
                    stat_box("Monthly visits", monthly_visits, fig_path / "user.png"),
                    unsafe_allow_html=True,
                )

        with st.container(key="tour_submissions_chart"):
            # Submissions per module barplot
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Submissions per Module")
            bar_fig, tool_data = build_submissions_figure()
            if bar_fig is not None:
                event = st.plotly_chart(
                    bar_fig,
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="points",
                    key="submissions_chart",
                )

                # Show pie chart in a dialog popup when a bar is clicked
                selection = event.get("selection", {}) if event else {}
                points = selection.get("points", [])
                if points:
                    module_title = points[0].get("x")
                    if module_title and module_title in tool_data and tool_data[module_title]:
                        _show_tool_breakdown(module_title, tool_data[module_title])
            else:
                st.info("Submission data is currently unavailable.")

        if Tour is not None:
            tour = Tour(
                get_homepage_tour_steps(),
                key=_home_tour_key,
                show_progress=True,
                animate=True,
                overlay_opacity=0.75,
                one_time_tour=False,
            )
            if st.session_state.pop("start_home_tour", False):
                # Manual button: always start regardless of opt-in.
                st.session_state["_home_tour_in_progress"] = True
                tour.start()
            elif "_tour_opted_in" in st.session_state and "_tour_auto_home" not in st.session_state:
                # User has made a decision and auto-start has not been handled yet.
                st.session_state["_tour_auto_home"] = True
                if st.session_state["_tour_opted_in"] is True:
                    st.session_state["_home_tour_in_progress"] = True
                    tour.start()
                # Opted out: mark handled, do not start.

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
