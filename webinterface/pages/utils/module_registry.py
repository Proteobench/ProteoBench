"""
Module registry for discovering and loading ProteoBench module metadata.

This module dynamically imports all pages_variables files to extract
module metadata for the sidebar navigation system and documentation main page.
"""

import importlib
import inspect
import os
from dataclasses import dataclass, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

MODULE_CATEGORIES = ["DDA", "DIA", "Archived", "Debug"]

# url_path of the home page in Home.py's st.navigation. Callable pages are identified by
# a hash of their url_path, so any st.Page built with this path links to the home page.
HOME_URL_PATH = "home"


def home_page_link():
    """Return an ``st.Page`` that ``st.page_link`` / ``st.switch_page`` resolve to the home page.

    Returns
    -------
    streamlit.navigation.page.StreamlitPage
        A page with the home page's url_path; its callable is never run.
    """
    return st.Page(lambda: None, title="ProteoBench", url_path=HOME_URL_PATH, default=True)


def _module_page(variables_class) -> Any:
    """Build the ``st.Page`` for one module from its Variables class.

    Parameters
    ----------
    variables_class : type
        The module's Variables dataclass.

    Returns
    -------
    streamlit.navigation.page.StreamlitPage
        A page at the module's ``sidebar_path``.
    """
    title, url_path = variables_class.sidebar_label, variables_class.sidebar_path
    page_file = getattr(variables_class, "page_file", None)
    if page_file:
        return st.Page(page_file, title=title, url_path=url_path)

    def render_module_page():
        from pages.base import run_page  # deferred: pages.base imports the sidebar, which imports this module

        run_page(variables_class())  # fresh instance per run, as a page script would create

    return st.Page(render_module_page, title=title, url_path=url_path)


def is_debug_enabled() -> bool:
    """Return whether local debug pages should be shown.

    Debug pages (category ``"Debug"``) are intended only for local development
    and must never appear on the public server. They are enabled by setting the
    environment variable ``PROTEOBENCH_DEBUG=1`` before launching Streamlit,
    which the production server does not set.

    Returns
    -------
    bool
        True if ``PROTEOBENCH_DEBUG`` equals ``"1"``, otherwise False.
    """
    return os.environ.get("PROTEOBENCH_DEBUG") == "1"


@dataclass
class ModuleMetadata:
    """Metadata for a ProteoBench module."""

    label: str
    path: str
    page: Any  # st.Page for st.navigation / st.page_link
    category: str
    release_stage: str
    keywords: List[str]
    title: str
    doc_url: str
    documentation_description: str = ""  # One-liner description for the docs homepage card
    results_repo: Optional[str] = None  # e.g. "Results_quant_ion_DDA"
    homepage_title: str = ""  # Friendlier phrase shown on the homepage module cards; falls back to `label`
    graphical_abstract: str = ""  # Filename in img/module_graphical_abstracts/; falls back to the generic module icon


@st.cache_resource
def get_all_modules() -> Dict[str, List[ModuleMetadata]]:
    """
    Discover and load all module metadata from pages_variables.

    Automatically discovers all *_variables.py files in the pages directory
    and loads their dataclass definitions without requiring manual mapping.

    Returns
    -------
    Dict[str, List[ModuleMetadata]]
        Dictionary mapping categories ("DDA", "DIA", "Archived", "Debug") to lists of ModuleMetadata.
    """
    modules_by_category = {c: [] for c in MODULE_CATEGORIES}

    # Get the path to the pages_variables directory
    # Assuming this file is in webinterface/pages/utils/
    current_file = Path(__file__)
    pages_variables_dir = current_file.parent.parent / "pages_variables"

    # Find all *_variables.py files in all subdirectories
    variable_files = sorted(pages_variables_dir.rglob("*_variables.py"))

    for variable_file in variable_files:
        # Skip __init__.py and other special files
        if variable_file.name.startswith("_"):
            continue

        # Get the relative path from pages_variables to construct import path
        relative_path = variable_file.relative_to(pages_variables_dir)
        # Convert path to module notation: Quant/lfq_DDA_ion_QExactive_variables.py -> Quant.lfq_DDA_ion_QExactive_variables
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        module_path = ".".join(module_parts)

        try:
            # Import the module
            module = importlib.import_module(f"pages.pages_variables.{module_path}")

            # Find the dataclass in the module
            # Look for classes that are dataclasses and have the required sidebar attributes
            variables_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if is_dataclass(obj) and hasattr(obj, "__annotations__") and "sidebar_label" in obj.__annotations__:
                    variables_class = obj
                    break

            if not variables_class:
                print(f"Warning: No suitable dataclass found in {module_path}")
                continue

            # Instantiate the class
            variables = variables_class()

            # Determine release stage from warning flags
            if hasattr(variables, "archived_warning") and variables.archived_warning:
                release_stage = "archived"
            elif hasattr(variables, "alpha_warning") and variables.alpha_warning:
                release_stage = "alpha"
            elif hasattr(variables, "beta_warning") and variables.beta_warning:
                release_stage = "beta"
            else:
                release_stage = "live"

            # Extract results repo name from github_link_pr
            # e.g. "github.com/Proteobot/Results_quant_ion_DDA.git" -> "Results_quant_ion_DDA"
            results_repo = None
            if hasattr(variables, "github_link_pr") and variables.github_link_pr:
                results_repo = variables.github_link_pr.removesuffix(".git").split("/")[-1]

            # Create metadata object
            metadata = ModuleMetadata(
                label=variables.sidebar_label,
                path=variables.sidebar_path,
                page=_module_page(variables_class),
                category=variables.sidebar_category,
                release_stage=release_stage,
                keywords=variables.keywords,
                title=variables.title,
                doc_url=variables.doc_url,
                documentation_description=getattr(variables, "documentation_description", ""),
                results_repo=results_repo,
                homepage_title=getattr(variables, "homepage_title", ""),
                graphical_abstract=getattr(variables, "graphical_abstract", ""),
            )

            # Add to appropriate category
            if metadata.category in modules_by_category:
                modules_by_category[metadata.category].append(metadata)

        except Exception as e:
            # Silently skip modules that fail to load
            # In production, you might want to log this
            print(f"Warning: Failed to load module {module_path}: {e}")
            continue

    # Debug-only modules are hidden unless explicitly enabled for a local run.
    if not is_debug_enabled():
        modules_by_category["Debug"] = []

    return modules_by_category


def all_module_pages() -> List[Any]:
    """Return the ``st.Page`` of every registered module (debug pages only when enabled).

    Returns
    -------
    list
        One ``st.Page`` per module, in category order.
    """
    return [m.page for modules in get_all_modules().values() for m in modules]


def module_page(sidebar_path: str) -> Any:
    """Return the ``st.Page`` of the module at ``sidebar_path`` (e.g. ``"/Quant_LFQ_DIA_ion_Astral"``).

    Parameters
    ----------
    sidebar_path : str
        The module's ``sidebar_path``.

    Returns
    -------
    streamlit.navigation.page.StreamlitPage
        The module's page.
    """
    return next(m.page for modules in get_all_modules().values() for m in modules if m.path == sidebar_path)


def filter_modules(modules_by_category: Dict[str, List[ModuleMetadata]], search_query: str) -> Dict[str, List[ModuleMetadata]]:
    """
    Filter modules based on search query matching keywords or title.

    Parameters
    ----------
    modules_by_category : Dict[str, List[ModuleMetadata]]
        Dictionary of modules organized by category.
    search_query : str
        Search query string (case-insensitive).

    Returns
    -------
    Dict[str, List[ModuleMetadata]]
        Filtered dictionary of modules matching the search query.
    """
    if not search_query:
        return modules_by_category

    query_lower = search_query.lower()
    filtered = {category: [] for category in MODULE_CATEGORIES}

    for category, modules in modules_by_category.items():
        for module in modules:
            # Check if query matches label, title, or any keyword
            if (
                query_lower in module.label.lower()
                or query_lower in module.title.lower()
                or any(query_lower in keyword.lower() for keyword in module.keywords)
            ):
                filtered[category].append(module)

    return filtered
