"""
Test that UIObjects classes correctly implement the BaseUIModule contract, and
that tab configurations only reference methods that actually exist.

Uses ast to parse source files so that no Streamlit import is needed.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = REPO_ROOT / "webinterface" / "pages"
PAGES_VARS_DIR = PAGES_DIR / "pages_variables"

BASE_UI_MODULE_FILE = PAGES_DIR / "base_pages" / "base.py"
BASE_STREAMLIT_UI_FILE = PAGES_DIR / "base.py"

# Known concrete UIObjects files: class_name -> source file
UIOBJECTS_FILES: Dict[str, Path] = {
    "QuantUIObjects": PAGES_DIR / "base_pages" / "quant.py",
    "DeNovoUIObjects": PAGES_DIR / "base_pages" / "denovo.py",
    "EntrapmentUIObjects": PAGES_DIR / "base_pages" / "entrapment.py",
}

KNOWN_BASE_CLASS = "BaseUIModule"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _get_abstract_method_names(filepath: Path, class_name: str) -> Set[str]:
    """Return the set of method names decorated with @abstractmethod in *class_name*."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    abstract: Set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in item.decorator_list:
                is_abstract = (isinstance(dec, ast.Name) and dec.id == "abstractmethod") or (
                    isinstance(dec, ast.Attribute) and dec.attr == "abstractmethod"
                )
                if is_abstract:
                    abstract.add(item.name)
    return abstract


def _get_class_method_names(filepath: Path, class_name: str) -> Set[str]:
    """Return the set of method names defined directly in *class_name*."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    methods: Set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.add(item.name)
    return methods


def _get_class_direct_bases(filepath: Path, class_name: str) -> List[str]:
    """Return the list of direct base-class name strings for *class_name*."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        return bases
    return []


def _method_names_from_tab_list(node: ast.AST) -> List[str]:
    """Return the method names (second element) of a literal list of (label, method) tuples."""
    if not isinstance(node, ast.List):
        return []
    method_names: List[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Tuple) and len(elt.elts) >= 2:
            second = elt.elts[1]
            if isinstance(second, ast.Constant) and isinstance(second.value, str):
                method_names.append(second.value)
    return method_names


def _get_tab_config_method_names(filepath: Path) -> List[str]:
    """
    Parse *filepath* and extract the tab method names from a tab configuration:
    either the module-level ``DEFAULT_TABS`` list or a module's ``tabs = [...]``
    class attribute in its Variables file.
    """
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in ("DEFAULT_TABS", "tabs") for t in node.targets
        ):
            return _method_names_from_tab_list(node.value)
    return []


def _get_uiobjects_class(filepath: Path) -> Optional[str]:
    """Return the class name assigned to ``uiobjects = ...`` in a Variables file."""
    tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "uiobjects" for t in node.targets)
            and isinstance(node.value, ast.Name)
        ):
            return node.value.id
    return None


def _get_module_variables_files() -> List[Path]:
    """Return every Variables file that defines a module page (one with ``uiobjects = ...``)."""
    return sorted(f for f in PAGES_VARS_DIR.rglob("*_variables.py") if _get_uiobjects_class(f))


# ---------------------------------------------------------------------------
# Tests: abstract method implementations
# ---------------------------------------------------------------------------


def test_abstract_methods_implemented_in_quant_uiobjects():
    """QuantUIObjects must implement every abstract method declared in BaseUIModule."""
    abstract = _get_abstract_method_names(BASE_UI_MODULE_FILE, KNOWN_BASE_CLASS)
    assert abstract, f"No abstract methods detected in {KNOWN_BASE_CLASS} — check parsing"

    implemented = _get_class_method_names(UIOBJECTS_FILES["QuantUIObjects"], "QuantUIObjects")
    missing = abstract - implemented
    assert not missing, f"QuantUIObjects is missing abstract method implementations: {sorted(missing)}"


def test_abstract_methods_implemented_in_denovo_uiobjects():
    """DeNovoUIObjects must implement every abstract method declared in BaseUIModule."""
    abstract = _get_abstract_method_names(BASE_UI_MODULE_FILE, KNOWN_BASE_CLASS)
    assert abstract, f"No abstract methods detected in {KNOWN_BASE_CLASS} — check parsing"

    implemented = _get_class_method_names(UIOBJECTS_FILES["DeNovoUIObjects"], "DeNovoUIObjects")
    missing = abstract - implemented
    assert not missing, f"DeNovoUIObjects is missing abstract method implementations: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Tests: inheritance
# ---------------------------------------------------------------------------


def test_quant_uiobjects_inherits_from_base_ui_module():
    """QuantUIObjects must directly inherit from BaseUIModule."""
    bases = _get_class_direct_bases(UIOBJECTS_FILES["QuantUIObjects"], "QuantUIObjects")
    assert KNOWN_BASE_CLASS in bases, f"QuantUIObjects does not directly inherit from {KNOWN_BASE_CLASS}. Found bases: {bases}"


def test_denovo_uiobjects_inherits_from_base_ui_module():
    """DeNovoUIObjects must directly inherit from BaseUIModule."""
    bases = _get_class_direct_bases(UIOBJECTS_FILES["DeNovoUIObjects"], "DeNovoUIObjects")
    assert (
        KNOWN_BASE_CLASS in bases
    ), f"DeNovoUIObjects does not directly inherit from {KNOWN_BASE_CLASS}. Found bases: {bases}"


# ---------------------------------------------------------------------------
# Tests: default tab config
# ---------------------------------------------------------------------------


def test_default_tab_config_methods_exist_in_quant_uiobjects():
    """All methods in pages.base.DEFAULT_TABS must exist in QuantUIObjects."""
    tab_methods = _get_tab_config_method_names(BASE_STREAMLIT_UI_FILE)
    assert tab_methods, "No methods found in pages.base.DEFAULT_TABS — check parsing"

    implemented = _get_class_method_names(UIOBJECTS_FILES["QuantUIObjects"], "QuantUIObjects")
    missing = set(tab_methods) - implemented
    assert not missing, f"Methods referenced in pages.base.DEFAULT_TABS are not defined in QuantUIObjects: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Tests: per-page tab-config override
# ---------------------------------------------------------------------------

_module_files = _get_module_variables_files()


@pytest.mark.parametrize("variables_file", _module_files, ids=[f.stem for f in _module_files])
def test_module_uiobjects_class_is_known(variables_file: Path):
    """Every module page names a UIObjects class this test knows the source of."""
    assert _get_uiobjects_class(variables_file) in UIOBJECTS_FILES


@pytest.mark.parametrize("variables_file", _module_files, ids=[f.stem for f in _module_files])
def test_module_tab_config_methods_exist_on_uiobjects(variables_file: Path):
    """Every tab method of a module page (its ``tabs`` or ``DEFAULT_TABS``) exists on its UIObjects class."""
    tab_methods = _get_tab_config_method_names(variables_file) or _get_tab_config_method_names(BASE_STREAMLIT_UI_FILE)
    uiobjects_class = _get_uiobjects_class(variables_file)
    implemented = _get_class_method_names(UIOBJECTS_FILES[uiobjects_class], uiobjects_class)
    missing = set(tab_methods) - implemented
    assert not missing, f"In {variables_file.name}: tab methods not defined in {uiobjects_class}: {sorted(missing)}"
