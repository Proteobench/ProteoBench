"""Tour step definitions for ProteoBench guided tours."""

from __future__ import annotations


def _tab_step(n: int, title: str, desc: str):
    """Create a tour step that targets the Nth tab button (1-indexed)."""
    from streamlit_tour import Step

    return Step(
        f'[data-baseweb="tab-list"] button:nth-child({n})',
        {"title": title, "description": desc, "side": "bottom", "align": "start"},
    )


def get_homepage_tour_steps() -> list:
    """Return step list for the ProteoBench homepage tour."""
    from streamlit_tour import Tour

    return [
        Tour.info(
            title="Welcome to ProteoBench!",
            desc=(
                "This platform lets you benchmark proteomics data analysis pipelines "
                "across tools, instruments, datasets and tasks."
            ),
        ),
        Tour.bind(
            "tour_stats_area",
            title="Statistics Overview",
            desc=(
                "These boxes show the current state of the ProteoBench ecosystem: "
                "active modules, supported tools, and submitted datapoints."
            ),
        ),
        Tour.bind(
            "tour_submissions_chart",
            title="Submissions per Module",
            desc=("This chart shows how many benchmark results have been submitted per module. "),
        ),
        Tour.info(
            title="Let's explore a module!",
            desc=(
                "Next, we will take you to the Quant LFQ DIA Astral module "
                "to show you how you can benchmark your data analysis."
            ),
        ),
    ]


def get_quant_tour_steps(module_name: str = "this module") -> list:
    """Return step list for a quantification module tour."""
    from streamlit_tour import Tour

    return [
        Tour.info(
            title=f"Welcome to {module_name}",
            desc=(
                "This module benchmarks the depth and quantitative accuracy of DIA data. Here is a quick overview of the tabs. "
                "These tabs will be similar across all modules, but the exact metrics and plots may differ based on the task."
            ),
        ),
        _tab_step(
            1,
            "View Public Results",
            "Browse all community-submitted benchmark results. Click this tab to explore them.",
        ),
        _tab_step(
            2,
            "Upload New Results (Private)",
            "Upload your tool's output file to run a private benchmark. Results stay private until you (optionally) submit.",
        ),
        _tab_step(
            3,
            "View Single Result",
            "Select any submission to see in-depth metrics: in the case of this module, fold change distribution, CVs, and MA plot.",
        ),
        _tab_step(4, "View Public + New Results", "See your uploaded results plotted alongside all public benchmarks."),
        _tab_step(
            5, "Compare Two Results", "Pick two workflows to compare their performance and parameter differences."
        ),
        _tab_step(6, "Submit New Results", "Submit your benchmark to the public repository via a GitHub pull request."),
        Tour.info(
            title="That's it!",
            desc=(
                "Start by browsing public results in the first tab, or upload your own data. Don't forget to submit your results to contribute to the community benchmarks!",
                "Happy benchmarking!",
            ),
        ),
    ]
