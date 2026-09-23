"""GitHub archive requests made by the home page."""

import io
import json
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("streamlit")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webinterface"))
import UI_utils  # noqa: E402


@pytest.mark.parametrize(
    ("token", "expected_headers"),
    [
        ("", {}),
        ("  ", {}),
        ("example-token", {"Authorization": "token example-token"}),
    ],
)
def test_submission_archive_authentication(monkeypatch, token, expected_headers):
    """Empty secrets must not turn a public GitHub request into a 401."""
    archive = io.BytesIO()
    payload = json.dumps({"software_name": "Example"}).encode()
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        entry = tarfile.TarInfo("result.json")
        entry.size = len(payload)
        tar.addfile(entry, io.BytesIO(payload))

    captured_headers = []

    def fake_get(url, *, headers, timeout):
        assert url.endswith("/Proteobench/Results_quant_ion_DDA/tarball/main")
        captured_headers.append(headers)
        return SimpleNamespace(content=archive.getvalue(), raise_for_status=lambda: None)

    monkeypatch.setattr(UI_utils.st, "secrets", {"gh": {"token": token}})
    monkeypatch.setattr(
        UI_utils,
        "get_all_modules",
        lambda: {"Quant": [SimpleNamespace(results_repo="Results_quant_ion_DDA")]},
    )
    monkeypatch.setattr(UI_utils.requests, "get", fake_get)

    result = UI_utils.get_module_submission_data.__wrapped__()

    assert captured_headers == [expected_headers]
    assert result == {"Results_quant_ion_DDA": {"Example": 1}}
