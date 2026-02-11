"""
Module registry for discovering and loading ProteoBench module metadata.

This module dynamically imports all pages_variables files to extract
module metadata for the sidebar navigation system.
"""

import importlib
import inspect
from dataclasses import dataclass, is_dataclass
from pathlib import Path
from typing import Dict, List

import streamlit as st


@dataclass
class ModuleMetadata:
    """Metadata for a ProteoBench module."""

    label: str
    path: str
    category: str
    release_stage: str
    keywords: List[str]
    title: str
    doc_url: str


@st.cache_resource
def get_all_modules() -> Dict[str, List[ModuleMetadata]]:
    """
    Discover and load all module metadata from pages_variables.

    Automatically discovers all *_variables.py files in the pages directory
    and loads their dataclass definitions without requiring manual mapping.

    Returns
    -------
    Dict[str, List[ModuleMetadata]]
        Dictionary mapping categories ("DDA", "DIA", "Archived") to lists of ModuleMetadata.
    """
    modules_by_category = {"DDA": [], "DIA": [], "Archived": []}

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
            if variables.sidebar_category == "Archived":
                release_stage = "archived"
            elif hasattr(variables, "alpha_warning") and variables.alpha_warning:
                release_stage = "alpha"
            elif hasattr(variables, "beta_warning") and variables.beta_warning:
                release_stage = "beta"
            else:
                release_stage = "stable"

            # Create metadata object
            metadata = ModuleMetadata(
                label=variables.sidebar_label,
                path=variables.sidebar_path,
                category=variables.sidebar_category,
                release_stage=release_stage,
                keywords=variables.keywords,
                title=variables.title,
                doc_url=variables.doc_url,
            )

            # Add to appropriate category
            if metadata.category in modules_by_category:
                modules_by_category[metadata.category].append(metadata)

        except Exception as e:
            # Silently skip modules that fail to load
            # In production, you might want to log this
            print(f"Warning: Failed to load module {module_path}: {e}")
            continue

    return modules_by_category


def filter_modules(
    modules_by_category: Dict[str, List[ModuleMetadata]], search_query: str
) -> Dict[str, List[ModuleMetadata]]:
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
    filtered = {"DDA": [], "DIA": [], "Archived": []}

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
