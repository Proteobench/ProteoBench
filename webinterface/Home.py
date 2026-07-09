"""Proteobench Streamlit-based web server."""

import streamlit as st
from _base import StreamlitPage
from pages.base_pages.tour_steps import get_homepage_tour_steps
from pages.utils.module_registry import MODULE_CATEGORIES, get_all_modules

# Optional guided-tour overlay; disable gracefully if streamlit_tour cannot be
# imported (e.g. version-incompatible with the installed streamlit). See base.py.
try:
    from streamlit_tour import Tour
except Exception:  # noqa: BLE001 - any import/component-registration failure
    Tour = None
from UI_utils import (
    build_submissions_figure,
    build_tool_pie_chart,
    get_module_submission_data,
    get_monthly_visits,
    get_n_modules,
    get_n_modules_proposed,
    get_n_submitted_points,
    get_n_supported_tools,
)

_MODULE_CARD_ICON = "../img/icons/module.svg"
_MODULE_CARD_FALLBACK_DESCRIPTION = "Benchmark this workflow and compare your results with the community."

# Friendlier, human-readable phrasing of each module's raw sidebar label, keyed by
# the module's path. Falls back to the raw label for any module not listed here.
_MODULE_FRIENDLY_TITLES = {
    "/denovo_DDA_HCD": "De Novo Sequencing on DDA-HCD",
    "/Quant_LFQ_DDA_ion_Astral": "LFQ Quantification on an Astral",
    "/Quant_LFQ_DDA_ion_QExactive": "LFQ Quantification on a QExactive",
    "/Quant_LFQ_DDA_peptidoform": "LFQ Quantification at the Peptidoform Level",
    "/Entrapment_DIA_ion_Astral": "FDR Validation on an Astral",
    "/Quant_LFQ_DIA_ion_Astral": "LFQ Quantification on an Astral",
    "/Quant_LFQ_DIA_ion_Plasma": "LFQ Quantification on Human Plasma",
    "/Quant_LFQ_DIA_ion_ZenoTOF": "LFQ Quantification on a ZenoTOF",
    "/Quant_LFQ_DIA_ion_diaPASEF": "LFQ Quantification on a timsTOF (diaPASEF)",
    "/Quant_LFQ_DIA_ion_lowinput": "LFQ Quantification for Low-Input & Single-Cell",
}


def _chunked(items, size):
    """Yield successive `size`-sized chunks from `items`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


_HOME_TOUR_KEY = "onboarding_home"

_BADGE_COLOR_BY_STAGE = {"alpha": "orange", "beta": "blue", "live": "green"}

# Instrument keywords in priority order (most specific model first, generic
# platform terms last) — the first one found in a module's keywords is shown.
_INSTRUMENT_KEYWORDS = ["QExactive", "Astral", "ZenoTOF", "timsTOF", "orbitrap", "SCIEX"]


def _module_type_tag(keywords):
    """Derive a coarse benchmark-type tag ("Quantification", "FDR validation",
    "Identification") from a module's keyword list."""
    if "entrapment" in keywords:
        return "FDR validation"
    if "de novo" in keywords or "identification" in keywords:
        return "Identification"
    if "quantification" in keywords:
        return "Quantification"
    return None


def _module_instrument(keywords):
    """Return the first known instrument keyword found, or None if the module
    isn't tied to a specific instrument."""
    for instrument in _INSTRUMENT_KEYWORDS:
        if instrument in keywords:
            return instrument
    return None


_ICON_DIR = "../img/icons"

_FEATURE_HIGHLIGHTS = [
    (
        f"{_ICON_DIR}/validate.svg",
        "Developed by experts",
        "Every module is designed and reviewed by proteomics experts, scoring tool outputs based on a "
        "standardised dataset or ground truth.",
    ),
    (
        f"{_ICON_DIR}/collaborate.svg",
        "Community-curated",
        "Data points are contributed, reviewed, and reproduced by the proteomics community.",
    ),
    (
        f"{_ICON_DIR}/contribute.svg",
        "Open & FAIR",
        "Open-source tools, standardized formats, and results ready for AI and reuse.",
    ),
    (
        f"{_ICON_DIR}/scatter-plot.svg",
        "Track progress",
        "Follow how search engines and pipelines improve from one release to the next.",
    ),
]


@st.dialog("Tool Breakdown", width="large")
def _show_tool_breakdown(module_title, tool_counts):
    pie_fig = build_tool_pie_chart(module_title, tool_counts)
    st.plotly_chart(pie_fig, use_container_width=True)


class StreamlitPageHome(StreamlitPage):
    """
    This class sets up the main page layout for the Streamlit application.
    """

    PAGE_LAYOUT = "wide"

    # overwrites _main_page from StreamlitPage
    # is called by initializer along sidebar and other setup
    def _main_page(self):
        """
        Set up the main page layout for the Streamlit application.
        """
        self._handle_tour_redirect()

        if st.sidebar.button("Take a Tour", key="home_tour_trigger"):
            # Manually requesting the tour implies opting in, so the follow-on
            # module tour also auto-starts after the post-tour redirect.
            st.session_state["start_home_tour"] = True
            st.session_state["_tour_opted_in"] = True

        self._render_tour_opt_in()

        st.space("large")
        self._render_feature_highlights()

        st.space("large")
        self._render_module_quicklinks()

        st.space("large")
        self._render_stats()

        st.space("large")
        self._render_submissions_chart()

        self._handle_tour_start()

    @staticmethod
    def _handle_tour_redirect():
        """Navigate to DIA Astral when the homepage tour ends (finish or dismiss)."""
        home_tour_active = f"stTour--{_HOME_TOUR_KEY}-active"
        if st.session_state.get("_home_tour_in_progress", False) and not st.session_state.get(home_tour_active, False):
            st.session_state.pop("_home_tour_in_progress", None)
            st.switch_page("pages/6_Quant_LFQ_DIA_ion_Astral.py")

    @staticmethod
    def _render_tour_opt_in():
        if "_tour_opted_in" in st.session_state:
            return
        with st.container(border=True):
            col_text, col_yes, col_no = st.columns([7, 2, 1.5], vertical_alignment="center")
            with col_text:
                st.markdown(
                    ":material/explore: **Want a quick guided tour?** "
                    "We will walk you through a benchmark module step by step."
                )
            with col_yes:
                if st.button("Yes, show me!", type="primary", width="content", key="tour_opt_in_yes"):
                    st.session_state["_tour_opted_in"] = True
                    st.rerun()
            with col_no:
                if st.button("No, thanks!", width="content", key="tour_opt_in_no"):
                    st.session_state["_tour_opted_in"] = False
                    st.rerun()

    @staticmethod
    def _render_feature_highlights():
        with st.container(horizontal_alignment="center"):
            st.subheader("Why ProteoBench?", text_alignment="center")
        for col, (icon, heading, body) in zip(st.columns(4, border=True), _FEATURE_HIGHLIGHTS):
            with col:
                st.image(icon, width=48)
                st.markdown(f"**{heading}**")
                st.caption(body)

    @staticmethod
    def _render_module_quicklinks():
        # The page_link label is truncated with an ellipsis by default (single-line,
        # no-wrap); let it wrap onto multiple lines instead so the full module
        # title is always visible.
        st.markdown(
            """
            <style>
            .st-key-tour_module_grid [data-testid="stPageLink"] span {
                white-space: normal;
                overflow: visible;
                text-overflow: unset;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="tour_module_grid"):
            st.subheader("Jump into a module", anchor="jump-into-a-module")
            st.caption("Pick a benchmark to explore public results or submit a run of your own.")

            submission_data = get_module_submission_data()
            modules_by_category = get_all_modules()
            for category in MODULE_CATEGORIES:
                modules = [m for m in modules_by_category.get(category, []) if m.release_stage != "archived"]
                if not modules:
                    continue
                st.subheader(f"{category} modules", divider="gray", anchor=False)
                for pair in _chunked(modules, 2):
                    cols = st.columns(2, border=True)
                    for col, module in zip(cols, pair):
                        with col, st.container(key=f"module_card_{module.path}"):
                            with st.container(horizontal=True, gap="small"):
                                badge_color = _BADGE_COLOR_BY_STAGE.get(module.release_stage)
                                if badge_color:
                                    st.badge(module.release_stage.upper(), color=badge_color)
                                type_tag = _module_type_tag(module.keywords)
                                if type_tag:
                                    st.badge(type_tag, color="violet")
                                instrument = _module_instrument(module.keywords)
                                if instrument:
                                    st.badge(instrument, icon=":material/precision_manufacturing:", color="gray")

                            st.image(_MODULE_CARD_ICON, width=40)
                            friendly_title = _MODULE_FRIENDLY_TITLES.get(module.path, module.label)
                            st.page_link(
                                module.file_path,
                                label=f"**{friendly_title}**",
                                icon=":material/arrow_forward:",
                            )
                            st.caption(module.documentation_description or _MODULE_CARD_FALLBACK_DESCRIPTION)

                            tool_counts = submission_data.get(module.results_repo, {})
                            with st.container(horizontal=True, gap="medium"):
                                st.caption(f":material/build: {len(tool_counts)} workflows supported")
                                st.caption(f":material/scatter_plot: {sum(tool_counts.values())} datapoints submitted")

    @staticmethod
    def _get_monthly_visits():
        secrets = st.secrets
        has_tracking_config = (
            "tracking" in secrets
            and "matomo_endpoint" in secrets["tracking"]
            and "matomo_idsite" in secrets["tracking"]
            and "matomo_token" in secrets["tracking"]
        )
        if not has_tracking_config:
            return "not configured"
        return get_monthly_visits(
            secrets["tracking"]["matomo_endpoint"],
            secrets["tracking"]["matomo_token"],
            secrets["tracking"]["matomo_idsite"],
        )

    def _render_stats(self):
        stats = [
            (
                ":material/dashboard: Active modules",
                get_n_modules(),
                "Modules with a public benchmark you can explore or submit to today.",
            ),
            (
                ":material/construction: In development",
                get_n_modules_proposed(),
                "Modules currently in discussion or under active development.",
            ),
            (
                ":material/build: Supported workflows",
                get_n_supported_tools(),
                "Software tools with parameter parsing support in ProteoBench.",
            ),
            (
                ":material/scatter_plot: Submitted points",
                get_n_submitted_points(),
                "Public benchmark runs submitted by the community so far.",
            ),
            (
                ":material/trending_up: Monthly visits",
                self._get_monthly_visits(),
                "Visits to the ProteoBench web server over the last 30 days.",
            ),
        ]
        with st.container(key="tour_stats_area"):
            st.subheader("Platform at a glance", anchor=False)
            with st.container(horizontal=True):
                for label, value, help_text in stats:
                    st.metric(label, value, border=True, help=help_text)

    @staticmethod
    def _render_submissions_chart():
        with st.container(key="tour_submissions_chart", border=True):
            st.subheader("Submissions per module", anchor=False)
            st.caption("Click a bar to see the breakdown of tools used for that module.")
            bar_fig, tool_data = build_submissions_figure()
            if bar_fig is None:
                st.info("Submission data is currently unavailable.")
                return

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

    @staticmethod
    def _handle_tour_start():
        if Tour is None:
            return
        tour = Tour(
            get_homepage_tour_steps(),
            key=_HOME_TOUR_KEY,
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


if __name__ == "__main__":
    StreamlitPageHome()
