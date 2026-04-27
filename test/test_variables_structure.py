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

# All fields that every Variables dataclass must define:
#   - Registry discovery (module_registry.py)
#   - BaseStreamlitUI.__init__ usage
#   - BaseUIModule.__init__ usage
#   - Resource references
#   - Stage flags
REQUIRED_FIELDS = frozenset(
    [
        # Registry discovery
        "sidebar_label",
        "sidebar_path",
        "sidebar_category",
        "title",
        "doc_url",
        "keywords",
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


_variables_files = _get_variables_files()


@pytest.mark.parametrize("variables_file", _variables_files, ids=[f.stem for f in _variables_files])
def test_required_fields_present(variables_file):
    """Each Variables dataclass must define every field in REQUIRED_FIELDS."""
    defined = _collect_class_attribute_names(variables_file)
    missing = REQUIRED_FIELDS - defined
    assert not missing, f"{variables_file.name} is missing required fields: {sorted(missing)}"
