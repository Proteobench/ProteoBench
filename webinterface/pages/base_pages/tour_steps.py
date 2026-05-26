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
        # Intro
        Tour.info(
            title=f"Welcome to {module_name}",
            desc=(
                "This module benchmarks quantification depth and accuracy. "
                "Here is a detailed walkthrough of all six tabs. "
                "Click each highlighted tab to navigate, then press Next."
            ),
        ),
        # Tab 1 — content is always visible as the default active tab
        _tab_step(
            1,
            "Tab 1: View Public Results",
            "This tab shows all community-submitted benchmark results. It is the default view.",
        ),
        Tour.bind(
            "tour_plot_options",
            title="Filter and Display Options",
            desc=(
                "Use these controls to set the minimum number of quantified precursors (slider), "
                "select the metric to display (Median, Mean, or ROC-AUC), "
                "and toggle between Global and Species-weighted calculation modes."
            ),
            side="bottom",
        ),
        Tour.bind(
            "tour_metric_plot",
            title="Benchmark Overview Plot",
            desc=(
                "Each point is one workflow submission. "
                "The X-axis shows the accuracy or precision score; "
                "the Y-axis shows the number of quantified precursor ions. "
                "Hover over points for tool and parameter details."
            ),
            side="top",
        ),
        # Tab 2
        _tab_step(
            2,
            "Tab 2: Upload New Results",
            "Click this tab to upload your own tool output and run a private benchmark. Press Next after clicking.",
        ),
        Tour.info(
            title="Select Your Software Tool",
            desc=(
                "Use the 'Software tool' dropdown to select the tool you used. "
                "Select one now — the file uploader below adapts to the expected output format."
            ),
        ),
        Tour.bind(
            "tour_upload_form",
            title="Upload File and Run Benchmark",
            desc=(
                "Upload your tool output file here. "
                "Add an optional keyword to help identify this run, "
                "then click 'Parse and bench' to compute benchmark metrics locally — "
                "no data leaves your browser at this step."
            ),
            side="bottom",
        ),
        # Tab 3
        _tab_step(
            3,
            "Tab 3: View Single Result",
            "Click this tab to explore in-depth plots for any individual submission. Press Next after clicking.",
        ),
        Tour.bind(
            "tour_dataset_selector",
            title="Select a Dataset",
            desc=(
                "Use the dropdown to choose any entry — your uploaded result or any public submission. "
                "Select one now, then press Next to see what the plots look like."
            ),
            side="bottom",
        ),
        Tour.bind(
            "tour_indepth_plots",
            title="In-Depth Plots",
            desc=(
                "After selecting a dataset, three plots appear here: "
                "a log2 fold-change distribution per species with expected ratio lines, "
                "a coefficient of variation (CV) violin plot for both conditions, "
                "and an MA plot coloured by species."
            ),
            side="top",
        ),
        # Tab 4
        _tab_step(
            4,
            "Tab 4: View Public + New Results",
            "Click this tab to see your uploaded result alongside all public submissions. Press Next after clicking.",
        ),
        Tour.bind(
            "tour_submitted_plot",
            title="Your Result in Context",
            desc=(
                "After uploading a result in Tab 2, it appears highlighted in this scatter plot "
                "alongside all public benchmark submissions, so you can immediately see how your workflow compares."
            ),
            side="top",
        ),
        # Tab 5
        _tab_step(
            5,
            "Tab 5: Compare Two Results",
            "Click this tab to compare any two workflows side by side. Press Next after clicking.",
        ),
        Tour.bind(
            "tour_compare_plot",
            title="Select Two Workflows",
            desc=(
                "Click on any two points in this scatter plot to select workflows for comparison. "
                "Selected IDs are shown below the plot. "
                "Click 'Clear' to reset the selection."
            ),
            side="top",
        ),
        Tour.bind(
            "tour_compare_results",
            title="Comparison Results",
            desc=(
                "Once two workflows are selected, two views appear here: "
                "a precursor overlap bar chart showing shared and unique identifications, "
                "and a parameter difference table highlighting what differs between the two workflows."
            ),
            side="top",
        ),
        # Tab 6
        _tab_step(
            6,
            "Tab 6: Submit New Results",
            "Click this tab to submit your benchmark result to the public repository. Press Next after clicking.",
        ),
        Tour.bind(
            "tour_meta_uploader",
            title="Upload Parameter File",
            desc=(
                "Upload the native parameter or log file from your software tool "
                "(for example: MaxQuant mqpar.xml, DIA-NN report.log.txt, Spectronaut .txt export). "
                "ProteoBench extracts analysis settings automatically."
            ),
            side="bottom",
        ),
        Tour.bind(
            "tour_param_fields",
            title="Review Extracted Parameters",
            desc=(
                "These fields are auto-populated from your parameter file. "
                "Review each value and correct any that were not parsed correctly "
                "before submitting to the public repository."
            ),
            side="top",
        ),
        # Outro
        Tour.info(
            title="Tour Complete!",
            desc=(
                "You have seen all six tabs. "
                "Start by exploring public results in Tab 1, or upload your own data in Tab 2. "
                "Submit your results to contribute to the community benchmarks!"
            ),
        ),
    ]
