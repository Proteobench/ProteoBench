"""
Unit tests for the Streamlit submission-validation glue
(``webinterface/pages/base_pages/utils/validation_ui.py``), focused on
surfacing best-effort sample/run-name auto-corrections (currently PEAKS only)
as warnings - so both the submitter and the pull-request reviewer can see
exactly which name(s) were auto-matched and reject the submission if a match
looks wrong.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

pytest.importorskip("streamlit")

import streamlit as st  # noqa: E402

# Put webinterface/ on the import path (pages.*, streamlit_utils, ...).
WEB_DIR = Path(__file__).resolve().parent.parent / "webinterface"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from pages.base_pages.utils import validation_ui  # noqa: E402
from proteobench.io.parsing.run_name_matching import RunNameMatch  # noqa: E402


def _fake_variables():
    return SimpleNamespace(input_df_submission="test_input_df_submission", input_df="test_input_df")


def test_run_name_corrections_are_surfaced_as_warnings(monkeypatch):
    corrections = [
        RunNameMatch(
            observed="LFQ_timstofSCP_diaPASEF_Condition_A_Sample_Alpha_01 Normalized Area",
            expected="LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_01 Normalized Area",
            score=0.9,
        )
    ]
    monkeypatch.setattr(
        validation_ui,
        "_build_standard_dataframe",
        lambda ionmodule, input_format, input_df: (pd.DataFrame({"a": [1]}), corrections),
    )

    variables = _fake_variables()
    st.session_state[variables.input_df] = pd.DataFrame({"a": [1]})

    report = validation_ui.run_submission_validation(
        variables=variables,
        ionmodule=SimpleNamespace(parse_settings_dir="does-not-matter", module_id="does-not-matter"),
        user_input={"input_format": "PEAKS"},
        params=None,
    )

    run_name_issues = [i for i in report.issues if i.code == "run_name_auto_corrected"]
    assert len(run_name_issues) == 1
    issue = run_name_issues[0]
    assert issue.observed == corrections[0].observed
    assert issue.expected == corrections[0].expected
    # Must be a WARNING (not INFO): report.summary() excludes info by default,
    # and summary() is what gets embedded in the pull-request description.
    from proteobench.validation import Severity

    assert issue.severity == Severity.WARNING
    assert corrections[0].observed in report.summary()


def test_no_corrections_means_no_run_name_warnings(monkeypatch):
    monkeypatch.setattr(
        validation_ui,
        "_build_standard_dataframe",
        lambda ionmodule, input_format, input_df: (pd.DataFrame({"a": [1]}), []),
    )

    variables = _fake_variables()
    st.session_state[variables.input_df] = pd.DataFrame({"a": [1]})

    report = validation_ui.run_submission_validation(
        variables=variables,
        ionmodule=SimpleNamespace(parse_settings_dir="does-not-matter", module_id="does-not-matter"),
        user_input={"input_format": "MaxQuant"},
        params=None,
    )

    assert [i for i in report.issues if i.code == "run_name_auto_corrected"] == []
