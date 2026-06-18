"""
Test that every Variables dataclass in pages_variables/ defines all fields
required by BaseStreamlitUI, BaseUIModule, and module_registry.

Uses ast to parse source files so that no Streamlit import is needed.
New modules are covered automatically: just add a *_variables.py file and
the parametrization discovers it at collection time.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES_VARS_DIR = REPO_ROOT / "webinterface" / "pages" / "pages_variables"

# Fields required of EVERY Variables dataclass, including local-only debug pages.
# These are read directly (no getattr fallback) by module_registry.get_all_modules()
# to populate the sidebar navigation and the documentation homepage grid.
REGISTRY_FIELDS = frozenset(
    [
        "sidebar_label",
        "sidebar_path",
        "sidebar_category",
        "title",
        "doc_url",
        "keywords",
    ]
)

# Fields required only of Variables dataclasses that back a full module page
# (one instantiated through BaseStreamlitUI / its subclasses). These are consumed
# by BaseStreamlitUI.__init__, BaseUIModule, the tab modules, and display_banner.
# Debug-only pages (sidebar_category == "Debug") are standalone scripts that do not
# go through that machinery, so they are exempt.
FRAMEWORK_FIELDS = frozenset(
    [
        # BaseStreamlitUI / BaseUIModule usage
        "submit",
        "parse_settings_dir",
        "params_file_dict",
        # Resource references
        "additional_params_json",
        "github_link_pr",
        # Stage flags
        "alpha_warning",
        "beta_warning",
        "archived_warning",
    ]
)

# Category marking local-only development pages, exempt from FRAMEWORK_FIELDS.
DEBUG_CATEGORY = "Debug"


def _get_variables_files():
    """Discover all *_variables.py files, excluding __init__.py and similar."""
    return sorted(f for f in PAGES_VARS_DIR.rglob("*_variables.py") if not f.name.startswith("_"))


def _collect_class_attribute_names(filepath: Path) -> set:
    """Return the set of attribute names defined at class body level in the file."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            # Annotated assignment:  field: type = value
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                names.add(item.target.id)
            # Plain assignment:  field = value  (e.g. class-level non-annotated constant)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
    return names


def _get_sidebar_category(filepath: Path):
    """Return the string default of ``sidebar_category`` in the file, or None.

    Used to identify local-only debug pages (``sidebar_category == "Debug"``),
    which are exempt from the BaseStreamlitUI framework-field requirements.
    """
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if (
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == "sidebar_category"
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            ):
                return item.value.value
    return None


_variables_files = _get_variables_files()


@pytest.mark.parametrize("variables_file", _variables_files, ids=[f.stem for f in _variables_files])
def test_registry_fields_present(variables_file):
    """Every Variables dataclass must define the fields module_registry reads directly."""
    defined = _collect_class_attribute_names(variables_file)
    missing = REGISTRY_FIELDS - defined
    assert not missing, f"{variables_file.name} is missing required registry fields: {sorted(missing)}"


@pytest.mark.parametrize("variables_file", _variables_files, ids=[f.stem for f in _variables_files])
def test_framework_fields_present(variables_file):
    """Module-page Variables dataclasses must define the BaseStreamlitUI framework fields.

    Local-only debug pages (``sidebar_category == "Debug"``) are standalone scripts
    that never go through BaseStreamlitUI, so they are exempt from these fields.
    """
    if _get_sidebar_category(variables_file) == DEBUG_CATEGORY:
        pytest.skip(f"{variables_file.name} is a {DEBUG_CATEGORY} page, exempt from framework fields")

    defined = _collect_class_attribute_names(variables_file)
    missing = FRAMEWORK_FIELDS - defined
    assert not missing, f"{variables_file.name} is missing required framework fields: {sorted(missing)}"
