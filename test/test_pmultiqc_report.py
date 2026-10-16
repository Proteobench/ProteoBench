"""The web report action supports both pMultiQC CLI spellings."""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("streamlit")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webinterface"))
from pages.base_pages.tabs import tab3_view_single_result as report_tab  # noqa: E402


@pytest.mark.parametrize("reject_underscore", [False, True])
def test_pmultiqc_report_uses_supported_plugin_flag(monkeypatch, reject_underscore):
    """Retry only when the installed CLI does not recognize the plugin flag."""
    flags = []
    errors = []
    successes = []

    def fake_run(command, **kwargs):
        assert kwargs["capture_output"] is True
        assert (Path(command[2]) / "result_performance.csv").is_file()
        flags.append(command[1])
        if reject_underscore and command[1] == "--proteobench_plugin":
            return subprocess.CompletedProcess(command, 2, stderr="No such option: --proteobench_plugin")
        (Path(command[4]) / "multiqc_report.html").write_text("<html>report</html>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stderr="")

    monkeypatch.setattr(report_tab.st, "button", lambda label: True)
    monkeypatch.setattr(report_tab.st, "error", errors.append)
    monkeypatch.setattr(report_tab.st, "success", successes.append)
    monkeypatch.setattr(report_tab.subprocess, "run", fake_run)

    html = report_tab.create_pmultiqc_report_section(pd.DataFrame({"species": ["HUMAN"]}))

    assert html == "<html>report</html>"
    assert flags == (
        ["--proteobench_plugin", "--proteobench-plugin"] if reject_underscore else ["--proteobench_plugin"]
    )
    assert not errors
    assert successes == ["pMultiQC report generated successfully."]
