"""
Test that file-path fields in every Variables dataclass point to existing
resources on disk.

Uses ast to extract default string values so that no Streamlit import is
needed.  Paths are resolved relative to the ``webinterface/`` directory,
which is the working directory when the Streamlit application runs.
"""

import ast
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEBINTERFACE_DIR = REPO_ROOT / "webinterface"
PAGES_VARS_DIR = WEBINTERFACE_DIR / "pages" / "pages_variables"

# Fields to check: {field_name: expected_kind}
PATH_FIELDS = {
    "additional_params_json": "file",
    "parse_settings_dir": "dir",
}


def _get_variables_files():
    """Discover all *_variables.py files, excluding __init__.py and similar."""
    return sorted(f for f in PAGES_VARS_DIR.rglob("*_variables.py") if not f.name.startswith("_"))


def _extract_string_defaults(filepath: Path) -> dict:
    """Return {field_name: default_str} for all annotated string fields in the class bodies."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    defaults = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, ast.AnnAssign):
                continue
            if not isinstance(item.target, ast.Name):
                continue
            if item.value is None:
                continue
            if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                defaults[item.target.id] = item.value.value
    return defaults


_variables_files = _get_variables_files()

# Build a flat parameter list: (variables_file, field_name, expected_kind)
_params = [
    pytest.param(vf, field, kind, id=f"{vf.stem}__{field}")
    for vf in _variables_files
    for field, kind in PATH_FIELDS.items()
]


@pytest.mark.parametrize("variables_file,field_name,expected_kind", _params)
def test_referenced_path_exists(variables_file: Path, field_name: str, expected_kind: str):
    """Paths stored in Variables dataclass fields must point to existing resources."""
    defaults = _extract_string_defaults(variables_file)

    if field_name not in defaults:
        pytest.skip(f"{variables_file.name} does not define '{field_name}'")

    raw_path: str = defaults[field_name]
    # Paths are relative to webinterface/ (Streamlit's working directory)
    resolved: Path = (WEBINTERFACE_DIR / raw_path).resolve()

    if expected_kind == "file":
        assert resolved.is_file(), (
            f"In {variables_file.name}: '{field_name}' = '{raw_path}' "
            f"does not point to an existing file (resolved: {resolved})"
        )
    else:
        assert resolved.is_dir(), (
            f"In {variables_file.name}: '{field_name}' = '{raw_path}' "
            f"does not point to an existing directory (resolved: {resolved})"
        )
