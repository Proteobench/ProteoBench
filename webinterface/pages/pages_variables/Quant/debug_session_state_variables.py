"""
Variables for debugging page.
"""

from dataclasses import dataclass, field


@dataclass
class Variables:
    title: str = "Debug Session State"

    doc_url: str = "https://proteobench.readthedocs.io/en/latest/"
    # Sidebar metadata
    sidebar_label: str = "Debug session state"
    sidebar_path: str = "/debug_session_state"
    sidebar_category: str = "Debug"
    # Not a module page: rendered from this file instead of run_page().
    page_file = "pages/0_debug_session_state.py"

    keywords: list[str] = field(
        default_factory=lambda: [
            "Debug",
            "session_state",
        ]
    )
