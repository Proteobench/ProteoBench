"""Headless smoke tests for the Streamlit web interface.

Each module page (built from its Variables class), the debug page and ``Home.py``
(the st.navigation router, rendering the home page) are executed through
``streamlit.testing.v1.AppTest`` with GitHub access and network calls mocked,
asserting that the page renders without raising. This complements the static
AST contract tests (``test_variables_*.py``, ``test_uiobjects_compliance.py``)
by catching failures that only appear when a page is actually run: import
errors, broken UIObjects wiring, missing methods, and crashes in the initial
(no-public-data) render.

The whole module is skipped when the streamlit web stack is not installed, so
it is a no-op in the core-only development environment while running fully in
CI (where ``pip install .`` provides streamlit and the webinterface
dependencies).
"""

import sys
from pathlib import Path

import pytest

# Skip the entire module when streamlit is unavailable (core-only dev env).
pytest.importorskip("streamlit", reason="webinterface smoke tests require the streamlit web stack")

# Ensure the sibling helper module is importable regardless of pytest import mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ast  # noqa: E402

from webinterface_apptest_utils import WEB_DIR, mocked_backend, new_app, new_module_app  # noqa: E402

PAGES_VARS_DIR = WEB_DIR / "pages" / "pages_variables"


def _module_pages():
    """(import path, class name) of every Variables class that defines a module page (has ``uiobjects``)."""
    found = []
    for path in sorted(PAGES_VARS_DIR.rglob("*_variables.py")):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.ClassDef) and any(
                isinstance(item, ast.Assign) and any(getattr(t, "id", None) == "uiobjects" for t in item.targets)
                for item in node.body
            ):
                module = ".".join(("pages",) + path.relative_to(WEB_DIR / "pages").with_suffix("").parts)
                found.append((module, node.name))
    return found


MODULE_PAGES = _module_pages()


@pytest.mark.parametrize("variables_module,variables_class", MODULE_PAGES, ids=[c for _, c in MODULE_PAGES])
def test_module_page_renders_without_exception(variables_module, variables_class, monkeypatch):
    """Every module page must execute headless without raising an uncaught exception."""
    assert MODULE_PAGES, "no module Variables classes found"
    with mocked_backend():
        app_test = new_module_app(variables_module, variables_class, monkeypatch)
        app_test.run()
    assert not app_test.exception, f"{variables_class} raised: {[e.message for e in app_test.exception]}"


def test_debug_page_renders_without_exception(monkeypatch):
    """The local-only debug page (a file page) must execute headless without raising."""
    with mocked_backend():
        app_test = new_app("pages/0_debug_session_state.py", monkeypatch)
        app_test.run()
    assert not app_test.exception, f"debug page raised: {[e.message for e in app_test.exception]}"


def test_home_page_renders_without_exception(monkeypatch):
    """The homepage must execute headless without raising an uncaught exception."""
    with mocked_backend(home=True):
        app_test = new_app("Home.py", monkeypatch)
        app_test.run()
    assert not app_test.exception, f"Home.py raised: {[e.message for e in app_test.exception]}"
