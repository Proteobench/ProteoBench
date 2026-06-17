"""Interaction tests for the Streamlit web interface.

These go beyond the smoke tests (``test_webinterface_smoke``) by driving real
widgets through ``streamlit.testing.v1.AppTest`` against a realistic public
dataset, and by exercising the submission backend:

* Tab 1 result slider: set it across its range and confirm the
  filter/recompute/plot pipeline survives at the boundary thresholds.
* Tab 2 software selector: change the selected tool and confirm the page
  re-runs cleanly with the new selection.
* Submission: call the pull-request path (``clone_pr``) with GitHub I/O mocked
  and confirm a PR is created. The Tab 6 submission *form* is gated behind a
  metadata file upload, and ``st.file_uploader`` cannot be driven by AppTest, so
  the submission logic is tested directly rather than through the UI.

The whole module is skipped when the streamlit web stack is not installed.
"""

import os
import sys
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

# Skip the entire module when streamlit is unavailable (core-only dev env).
pytest.importorskip("streamlit", reason="webinterface interaction tests require the streamlit web stack")

# Ensure the sibling helper module is importable regardless of pytest import mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from webinterface_apptest_utils import EMPTY_DATAPOINTS, mocked_backend, new_app  # noqa: E402

from proteobench.github.gh import GithubProteobotRepo  # noqa: E402
from proteobench.io.params import ProteoBenchParameters  # noqa: E402
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive  # noqa: E402

QEXACTIVE_PAGE = "pages/2_Quant_LFQ_DDA_ion_QExactive.py"
TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/quant/quant_lfq_ion_DDA_QExactive")
MAXQUANT_FILE = os.path.join(TESTDATA_DIR, "MaxQuant_evidence_sample.txt")

# Minimal valid user input for the benchmarking pipeline (mirrors the module test).
USER_INPUT = {
    "software_name": "MaxQuant",
    "software_version": "1.0",
    "search_engine_version": "1.0",
    "search_engine": "MaxQuant",
    "ident_fdr_psm": 0.01,
    "ident_fdr_peptide": 0.05,
    "ident_fdr_protein": 0.1,
    "enable_match_between_runs": 1,
    "precursor_mass_tolerance": "0.02 Da",
    "fragment_mass_tolerance": "0.02 Da",
    "enzyme": "Trypsin",
    "allowed_miscleavages": 1,
    "min_peptide_length": 6,
    "max_peptide_length": 30,
}


@pytest.fixture(scope="module")
def benchmarked_datapoints() -> pd.DataFrame:
    """Run the real QExactive pipeline once to obtain a valid one-row datapoint frame.

    Produces a genuine ``results`` structure (thresholds 1..6) and a real
    ``software_name`` so the public-results plot and table render as in production.
    GitHub access is mocked so no network or clone occurs.
    """
    with (
        mock.patch.object(GithubProteobotRepo, "clone_repo", lambda self: None),
        mock.patch.object(GithubProteobotRepo, "read_results_json_repo", lambda self: EMPTY_DATAPOINTS.copy()),
    ):
        module = DDAQuantIonModuleQExactive("")
        _, all_datapoints, _ = module.benchmarking(MAXQUANT_FILE, "MaxQuant", USER_INPUT, None)
    assert len(all_datapoints) == 1
    return all_datapoints


def test_tab1_slider_drives_recompute_without_error(benchmarked_datapoints, monkeypatch):
    """Driving the Tab 1 result slider across its range re-runs the page cleanly."""
    with mocked_backend(datapoints=benchmarked_datapoints):
        app_test = new_app(QEXACTIVE_PAGE, monkeypatch)
        app_test.run()
        assert not app_test.exception, f"initial render raised: {[e.message for e in app_test.exception]}"

        # The Tab 1 main slider (st.select_slider) is the first select_slider on the page.
        assert len(app_test.select_slider) >= 1, "expected at least one select_slider on the page"
        slider = app_test.select_slider[0]
        options = list(slider.options)
        assert len(options) >= 2, f"slider should expose a range of thresholds, got {options}"

        # Drive to both extremes; each setting recomputes metrics from the results dict.
        # options/value may differ in type (e.g. formatted '1' vs underlying 1), so compare as strings.
        for target in (options[0], options[-1]):
            app_test.select_slider[0].set_value(target).run()
            assert (
                not app_test.exception
            ), f"setting slider to {target} raised: {[e.message for e in app_test.exception]}"
            assert str(app_test.select_slider[0].value) == str(target)


def test_tab2_software_selector_changes_selection(benchmarked_datapoints, monkeypatch):
    """Selecting a different tool in the Tab 2 software selector re-runs cleanly."""
    with mocked_backend(datapoints=benchmarked_datapoints):
        app_test = new_app(QEXACTIVE_PAGE, monkeypatch)
        app_test.run()
        assert not app_test.exception

        selector = app_test.selectbox(key="software_tool_selector")
        options = list(selector.options)
        assert len(options) >= 2, f"expected multiple software options, got {options}"

        # Pick an option different from the current selection.
        target = next(opt for opt in options if opt != selector.value)
        app_test.selectbox(key="software_tool_selector").select(target).run()

        assert not app_test.exception, f"changing software raised: {[e.message for e in app_test.exception]}"
        assert app_test.selectbox(key="software_tool_selector").value == target


def test_submission_creates_pull_request(benchmarked_datapoints, tmp_path):
    """clone_pr opens a pull request for a benchmarked datapoint (GitHub I/O mocked)."""
    create_pr = mock.Mock(return_value=4242)
    remote_git = "github.com/Proteobot/Results_quant_ion_DDA.git"

    with (
        mock.patch.object(GithubProteobotRepo, "clone_repo", lambda self: None),
        mock.patch.object(GithubProteobotRepo, "clone_repo_pr", lambda self: None),
        mock.patch.object(GithubProteobotRepo, "read_results_json_repo", lambda self: EMPTY_DATAPOINTS.copy()),
        mock.patch.object(GithubProteobotRepo, "create_branch", lambda self, branch_name: None),
        mock.patch.object(GithubProteobotRepo, "commit", lambda self, name, message: None),
        mock.patch.object(GithubProteobotRepo, "create_pull_request", create_pr),
    ):
        module = DDAQuantIonModuleQExactive("")
        module.t_dir_pr = str(tmp_path)  # clone_pr writes the datapoint JSON here

        url = module.clone_pr(
            benchmarked_datapoints.copy(),
            ProteoBenchParameters(),
            remote_git=remote_git,
            submission_comments="integration test",
            submission_source="local",
        )

    assert create_pr.called, "create_pull_request was not called"
    assert create_pr.call_args.kwargs.get("submission_source") == "local"
    assert url == "https://github.com/Proteobot/Results_quant_ion_DDA/pull/4242"

    # The datapoint JSON must have been written to the PR working directory.
    written = list(tmp_path.glob("*.json"))
    assert len(written) == 1, f"expected one datapoint JSON, found {written}"


def test_tab2_file_upload_runs_benchmarking(monkeypatch):
    """Upload a result file through the real file_uploader and run the Tab 2 benchmarking flow.

    Exercises the full upload path: file_uploader -> temp-file write -> parse ->
    ionmodule.benchmarking -> submitted datapoint, ending in the success message.
    streamlit>=1.58's AppTest supports driving st.file_uploader directly.
    """
    content = Path(MAXQUANT_FILE).read_bytes()
    with mocked_backend():
        app_test = new_app(QEXACTIVE_PAGE, monkeypatch)
        app_test.run()

        # The software selector is outside the form; set it before submitting.
        app_test.selectbox(key="software_tool_selector").set_value("MaxQuant").run()
        assert not app_test.exception

        # Upload the result file to the main uploader and submit the form.
        app_test.file_uploader[0].upload("MaxQuant_evidence_sample.txt", content)
        submit = next(b for b in app_test.button if b.label == "Parse and bench")
        submit.click().run()

    assert not app_test.exception, f"submission run raised: {[e.message for e in app_test.exception]}"
    assert any(
        "submitted successfully" in str(info.value) for info in app_test.info
    ), f"expected success message; infos seen: {[info.value for info in app_test.info]}"
