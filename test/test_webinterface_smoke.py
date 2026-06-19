"""Headless smoke tests for the Streamlit web interface.

Each module page (and ``Home.py``) is executed through
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
from webinterface_apptest_utils import WEB_DIR, mocked_backend, new_app  # noqa: E402

PAGE_FILES = sorted(p.name for p in (WEB_DIR / "pages").glob("[0-9]*.py"))


@pytest.mark.parametrize("page_file", PAGE_FILES, ids=[Path(p).stem for p in PAGE_FILES])
def test_module_page_renders_without_exception(page_file, monkeypatch):
    """Every module page must execute headless without raising an uncaught exception."""
    with mocked_backend():
        app_test = new_app(f"pages/{page_file}", monkeypatch)
        app_test.run()
    assert not app_test.exception, f"{page_file} raised: {[e.message for e in app_test.exception]}"


def test_home_page_renders_without_exception(monkeypatch):
    """The homepage must execute headless without raising an uncaught exception."""
    with mocked_backend(home=True):
        app_test = new_app("Home.py", monkeypatch)
        app_test.run()
    assert not app_test.exception, f"Home.py raised: {[e.message for e in app_test.exception]}"
