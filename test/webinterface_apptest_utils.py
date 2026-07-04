"""Shared helpers for the headless AppTest-based webinterface tests.

This module is imported only by test modules that have already established the
streamlit web stack is present (via ``pytest.importorskip("streamlit")``), so it
imports streamlit at module level. Its filename intentionally does not match the
pytest collection pattern, so pytest never imports it directly.

It centralises the setup shared by the smoke tests (``test_webinterface_smoke``)
and the interaction tests (``test_webinterface_interaction``): putting
``webinterface/`` on the import path, stubbing the JS-only ``streamlit_tour``
component, and the standard backend mocks (GitHub access, multipage navigation,
and the homepage's network statistics).
"""

import contextlib
import sys
import types
from pathlib import Path
from unittest import mock

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "webinterface"

# webinterface/ must be importable (pages.*, _base, UI_utils, streamlit_utils) and
# is also Streamlit's working directory when the application runs.
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))


def install_tour_stub() -> None:
    """Replace ``streamlit_tour`` with a no-op stub for headless runs.

    ``streamlit_tour`` is a driver.js overlay component that cannot render in
    headless ``AppTest``; v1.1.0 is additionally import-incompatible with
    ``streamlit>=1.58``. The real package is used when it imports cleanly;
    otherwise the stub lets the pages import and exercise their actual logic.
    """
    try:
        import streamlit_tour  # noqa: F401

        return
    except Exception:  # noqa: BLE001 - any import/component-registration failure -> stub it
        pass

    fake = types.ModuleType("streamlit_tour")

    class _TourMeta(type):
        def __getattr__(cls, name):
            # Tour.info(...), Tour.bind(...), etc. used to build step lists.
            return lambda *a, **k: {}

    class _Tour(metaclass=_TourMeta):
        def __init__(self, *a, **k):
            pass

        def start(self, *a, **k):
            pass

    fake.Tour = _Tour
    fake.Step = _Tour  # tour_steps.py: from streamlit_tour import Step
    sys.modules["streamlit_tour"] = fake


install_tour_stub()

# Zero-row datapoints frame carrying the columns the public-results render path
# touches. Drives the genuine "no submissions yet" state every page must survive.
EMPTY_DATAPOINTS = pd.DataFrame(columns=["id", "intermediate_hash", "software_name", "results", "nr_feature"])


@contextlib.contextmanager
def mocked_backend(datapoints: pd.DataFrame = None, home: bool = False, extra_patches=()):
    """Patch GitHub access, multipage navigation, and (for Home) network stats.

    Parameters
    ----------
    datapoints : pd.DataFrame, optional
        Frame returned by ``read_results_json_repo``. Defaults to the empty state.
    home : bool, optional
        When True, also stub the homepage's network-backed statistics helpers.
    extra_patches : iterable, optional
        Additional ``mock.patch`` objects to enter for the duration of the block.
    """
    df = EMPTY_DATAPOINTS if datapoints is None else datapoints
    patches = [
        # QuantModule.__init__ clones a GitHub repo on construction; suppress it.
        mock.patch("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda self: None),
        # Public results are loaded from the cloned repo.
        mock.patch("proteobench.github.gh.GithubProteobotRepo.read_results_json_repo", lambda self: df.copy()),
        # st.page_link / st.switch_page need the multipage registry that
        # AppTest.from_file (single-file mode) does not build.
        mock.patch.object(st, "page_link", lambda *a, **k: None),
        mock.patch.object(st, "switch_page", lambda *a, **k: None),
    ]
    if home:
        import UI_utils  # only importable with webinterface on sys.path

        patches += [
            mock.patch.object(UI_utils, "get_n_submitted_points", lambda *a, **k: 0),
            mock.patch.object(UI_utils, "build_submissions_figure", lambda *a, **k: (None, {})),
        ]
    patches += list(extra_patches)
    with contextlib.ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        yield


def new_app(page_rel: str, monkeypatch, timeout: int = 120) -> AppTest:
    """Return a configured (not yet run) AppTest for a webinterface page.

    The caller runs it inside a :func:`mocked_backend` block so the patches stay
    active across the initial run and any subsequent widget-driven re-runs.
    """
    monkeypatch.chdir(WEB_DIR)
    app_test = AppTest.from_file(str(WEB_DIR / page_rel), default_timeout=timeout)
    app_test.secrets["gh"] = {"token": ""}
    return app_test
