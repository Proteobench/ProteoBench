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

BASE_UI_MODULE_FILE = PAGES_DIR / "base_pages" / "base.py"
BASE_STREAMLIT_UI_FILE = PAGES_DIR / "base.py"

# Known concrete UIObjects files: class_name -> source file
UIOBJECTS_FILES: Dict[str, Path] = {
    "QuantUIObjects": PAGES_DIR / "base_pages" / "quant.py",
    "DeNovoUIObjects": PAGES_DIR / "base_pages" / "denovo.py",
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


def _get_tab_config_method_names(filepath: Path) -> List[str]:
    """
    Parse *filepath* and extract the list of method-name strings from any
    ``get_tab_config`` function/method.  Returns the method names (second
    element of each tuple in the returned list).
    """
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != "get_tab_config":
            continue
        # Walk the body looking for a return of a list of 2-tuples
        for stmt in ast.walk(node):
            if not isinstance(stmt, ast.Return):
                continue
            if not isinstance(stmt.value, ast.List):
                continue
            method_names: List[str] = []
            for elt in stmt.value.elts:
                if isinstance(elt, ast.Tuple) and len(elt.elts) >= 2:
                    second = elt.elts[1]
                    if isinstance(second, ast.Constant) and isinstance(second.value, str):
                        method_names.append(second.value)
            return method_names
    return []


def _get_uiobjects_class_from_page(filepath: Path) -> Optional[str]:
    """
    Parse a page file and return the UIObjects class name passed as the
    ``uiobjects`` keyword argument to any constructor call.
    """
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "uiobjects" and isinstance(kw.value, ast.Name):
                return kw.value.id
    return None


def _get_page_files() -> List[Path]:
    """Return all numbered page files in webinterface/pages/ (e.g. 2_*.py, 11_*.py).

    The pattern ``[0-9]*.py`` matches any file whose name starts with a digit
    followed by any characters, so multi-digit prefixes such as ``10_`` and
    ``11_`` are included.
    """
    return sorted(f for f in PAGES_DIR.glob("[0-9]*.py") if f.is_file())


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
    assert KNOWN_BASE_CLASS in bases, (
        f"QuantUIObjects does not directly inherit from {KNOWN_BASE_CLASS}. Found bases: {bases}"
    )


def test_denovo_uiobjects_inherits_from_base_ui_module():
    """DeNovoUIObjects must directly inherit from BaseUIModule."""
    bases = _get_class_direct_bases(UIOBJECTS_FILES["DeNovoUIObjects"], "DeNovoUIObjects")
    assert KNOWN_BASE_CLASS in bases, (
        f"DeNovoUIObjects does not directly inherit from {KNOWN_BASE_CLASS}. Found bases: {bases}"
    )


# ---------------------------------------------------------------------------
# Tests: default tab config
# ---------------------------------------------------------------------------


def test_default_tab_config_methods_exist_in_quant_uiobjects():
    """All methods in BaseStreamlitUI.get_tab_config() must exist in QuantUIObjects."""
    tab_methods = _get_tab_config_method_names(BASE_STREAMLIT_UI_FILE)
    assert tab_methods, "No methods found in BaseStreamlitUI.get_tab_config() — check parsing"

    implemented = _get_class_method_names(UIOBJECTS_FILES["QuantUIObjects"], "QuantUIObjects")
    missing = set(tab_methods) - implemented
    assert not missing, (
        f"Methods referenced in BaseStreamlitUI.get_tab_config() are not defined in QuantUIObjects: {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# Tests: per-page tab-config override
# ---------------------------------------------------------------------------

_page_files = _get_page_files()


@pytest.mark.parametrize("page_file", _page_files, ids=[f.stem for f in _page_files])
def test_page_tab_config_override_methods_exist_on_uiobjects(page_file: Path):
    """
    For pages that override get_tab_config(), every referenced method must
    exist on the UIObjects class that the page instantiates.
    """
    override_methods = _get_tab_config_method_names(page_file)
    if not override_methods:
        pytest.skip(f"{page_file.name} does not define/override get_tab_config()")

    uiobjects_class = _get_uiobjects_class_from_page(page_file)
    if uiobjects_class is None:
        pytest.skip(f"{page_file.name} does not pass 'uiobjects=' to any constructor")

    if uiobjects_class not in UIOBJECTS_FILES:
        pytest.skip(f"UIObjects class '{uiobjects_class}' in {page_file.name} is not in the known set — skipping")

    implemented = _get_class_method_names(UIOBJECTS_FILES[uiobjects_class], uiobjects_class)
    missing = set(override_methods) - implemented
    assert not missing, (
        f"In {page_file.name}: get_tab_config() references methods not defined in "
        f"{uiobjects_class}: {sorted(missing)}"
    )
