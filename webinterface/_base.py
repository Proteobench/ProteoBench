"""Base classes for ProteoBench online Streamlit web server."""

import os
from abc import ABC, abstractmethod

import pages.texts.proteobench_builder as pbb
import streamlit as st

import proteobench

# 8-byte PNG file signature.
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _resolve_asset(path: str) -> str:
    """Resolve an asset path, materializing git symlinks checked out as text.

    On Windows checkouts without symlink support (``core.symlinks=false``), git
    writes a symlink as a small text file containing the link target instead of
    a real symlink. Streamlit/PIL then fail to read it as an image. Detect that
    case and return the resolved target path; otherwise return ``path``
    unchanged.

    Parameters
    ----------
    path : str
        Path to the asset, relative to the current working directory.

    Returns
    -------
    str
        The original path, or the resolved symlink-target path when the file is
        a text pointer to an existing target.
    """
    try:
        with open(path, "rb") as handle:
            head = handle.read(len(_PNG_SIGNATURE))
    except OSError:
        return path
    # A real PNG (the symlink correctly followed) starts with the signature.
    if head.startswith(_PNG_SIGNATURE):
        return path
    # Otherwise treat the file content as a (relative) symlink target.
    try:
        with open(path, "r", encoding="utf-8") as handle:
            target = handle.read().strip()
    except (OSError, UnicodeDecodeError):
        return path
    if not target:
        return path
    candidate = os.path.normpath(os.path.join(os.path.dirname(path), target))
    return candidate if os.path.isfile(candidate) else path


# Why does it exist? We only have one Page defined
class StreamlitPage(ABC):
    """
    Base class for Proteobench online Streamlit web server.
    """

    # Subclasses (currently only the homepage) may widen this for a dashboard-style layout.
    PAGE_LAYOUT = "centered"

    def __init__(self) -> None:
        """
        Initialize the Proteobench online Streamlit web server.
        """
        self.state = st.session_state

        pbb.proteobench_page_config(page_layout=self.PAGE_LAYOUT)
        pbb.proteobench_sidebar(current_page="/")

        self._preface()
        self._main_page()
        self._logos()

    def _preface(self):
        """
        Set up the preface (hero section) of the Streamlit application.
        """
        version = getattr(proteobench, "__version__", "unknown")

        st.markdown(
            """
            <style>
            .st-key-hero_section {
                background: linear-gradient(135deg, rgba(97,165,194,0.16), rgba(244,165,130,0.12));
                border-radius: 16px;
                padding: 2.5rem 1.5rem 1.75rem 1.5rem;
                margin-bottom: 0.5rem;
            }
            /* Scoped to the tagline only, so it doesn't mute button/link labels
               that also render through stMarkdownContainer. */
            .st-key-hero_section .st-key-hero_tagline [data-testid="stMarkdownContainer"] p {
                color: #5b6b82;
            }
            /* Keep the hero CTA row buttons/links the same height regardless of label length. */
            .st-key-hero_cta_row [data-testid="stButton"] button,
            .st-key-hero_cta_row [data-testid="stLinkButton"] a {
                height: 2.5rem;
                white-space: nowrap;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="hero_section", horizontal_alignment="center"):
            st.caption(
                "THE OPEN PLATFORM FOR BENCHMARKING PROTEOMICS DATA ANALYSIS WORKFLOWS",
                text_alignment="center",
                width=700,
            )
            st.image("../img/proteobench-logo-horizontal.svg", width=480)
            with st.container(key="hero_tagline", horizontal_alignment="center"):
                st.markdown(
                    "Browse public benchmarks to see how workflows compare, "
                    "or submit your own workflow results and see how it stacks up.",
                    text_alignment="center",
                    width=700,
                )
            st.markdown(
                ":violet-badge[:material/lock_open: Open source] "
                ":blue-badge[:material/diversity_3: Community-curated] "
                ":green-badge[:material/eco: FAIR & AI-ready]",
                text_alignment="center",
            )
            st.space("small")

            with st.container(horizontal=True, horizontal_alignment="center", key="hero_cta_row"):
                if st.button(
                    "Take a guided tour",
                    icon=":material/explore:",
                    type="primary",
                    key="hero_tour_button",
                ):
                    # Manually requesting the tour implies opting in, so the follow-on
                    # module tour also auto-starts after the post-tour redirect.
                    st.session_state["start_home_tour"] = True
                    st.session_state["_tour_opted_in"] = True
                st.link_button(
                    "Browse modules",
                    "#jump-into-a-module",
                    icon=":material/dashboard:",
                )
                st.link_button(
                    "Documentation",
                    "https://proteobench.readthedocs.io/",
                    icon=":material/menu_book:",
                )
                st.link_button(
                    "GitHub",
                    "https://github.com/Proteobench/Proteobench",
                    icon=":material/code:",
                )

            st.caption(
                "[Read the manuscript on bioRxiv](https://doi.org/10.64898/2025.12.09.692895) · "
                "ProteoBench is initiated and maintained by [EuBIC-MS](https://eubic-ms.org/) — "
                "[join us](https://eubic-ms.org/become-a-member/) · "
                "[Contact us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) · "
                f"v{version}",
                text_alignment="center",
                width=700,
            )

        # add hosting information if provided
        try:
            if "hosting" in st.secrets.keys():
                st.markdown(st.secrets["hosting"]["information"])
        except FileNotFoundError:
            # Would be preffered if we can keep this information elsewhere or
            # provide a default config file
            pass

    @abstractmethod
    def _main_page(self):
        """
        Set up the main page layout for the Streamlit application.
        """
        raise NotImplementedError()

    def _logos(self):
        """
        Set up the logos for the Streamlit application.
        """
        st.space("large")
        with st.container(horizontal_alignment="center"):
            st.caption("Supported by")
            st.image(
                _resolve_asset("logos/logo_participants/proteobench-contributing-institutes.png"),
                width=700,
            )
            st.caption(
                "[Privacy notice](https://www.ruhr-uni-bochum.de/en/privacy-notice) · "
                "[Legal notice](https://www.ruhr-uni-bochum.de/en/legal-notice)",
                text_alignment="center",
            )
