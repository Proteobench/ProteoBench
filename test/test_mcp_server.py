import asyncio
import json
import os

import pandas as pd
import pytest

pytest.importorskip("mcp")

from proteobench.mcp import server  # noqa: E402
from proteobench.modules.constants import MODULE_SETTINGS_DIRS  # noqa: E402

MODULE_ID = "quant_lfq_DDA_ion_QExactive"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "quant", "quant_lfq_ion_DDA_QExactive")
PARAMS_DIR = os.path.join(os.path.dirname(__file__), "params")

# One fake public datapoint: very accurate but shallow.
PUBLIC = pd.DataFrame(
    [
        {
            "id": "Public_1",
            "software_name": "MaxQuant",
            "intermediate_hash": "abc",
            "results": {"3": {"median_abs_epsilon_eq_species": 0.0, "nr_feature": 1}},
            "median_abs_epsilon_eq_species": 0.0,
            "nr_feature": 1,
        }
    ]
)


@pytest.fixture(autouse=True)
def mock_github(monkeypatch, tmp_path):
    monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.read_results_json_repo", lambda *a, **kw: PUBLIC)
    monkeypatch.setattr(server, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(server, "_remote_size_mb", lambda url: None)
    server._module.cache_clear()
    server._public_datapoints.cache_clear()


def test_tools_are_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"list_modules", "explain_metrics", "benchmark_result", "get_public_results"} <= names


def test_all_modules_with_settings_are_discovered():
    discovered = {m["module_id"] for m in server.list_modules()}
    assert {MODULE_ID, "quant_lfq_DIA_ion_plasma", "denovo_DDA_HCD"} <= discovered
    assert discovered <= set(MODULE_SETTINGS_DIRS)


@pytest.mark.parametrize("module_id", sorted(server.MODULES))
def test_module_provides_what_the_server_needs(module_id):
    """Every discovered module must have a parameter template, supported tools and a metrics explanation."""
    assert os.path.exists(server._params_json(module_id))
    assert server.list_supported_tools(module_id)
    assert server.explain_metrics(module_id)["main"]


def test_unknown_module_gives_readable_error():
    with pytest.raises(server.ToolError, match="Unknown module_id"):
        server.list_supported_tools("nope")


def test_flatten_handles_nested_results_and_skips_lists():
    flat = server._flatten({3: {"a": 1.0}, "peptide": {"mass": {"precision": 0.5, "curve": [1, 2]}}})
    assert flat == {"3.a": 1.0, "peptide.mass.precision": 0.5}


def test_split_datapoint_separates_parameters_metrics_and_bookkeeping():
    row = pd.Series({"id": "x", "results": {}, "software_name": "MaxQuant", "nr_feature": 5, "comments": ""})
    params, metrics = server._split_datapoint(row, MODULE_ID)
    assert params == {"software_name": "MaxQuant"}
    assert metrics == {"nr_feature": 5}


def test_benchmark_result_compares_with_public():
    result = server.benchmark_result(
        MODULE_ID,
        "MaxQuant",
        os.path.join(DATA_DIR, "MaxQuant_evidence_sample.txt"),
        os.path.join(PARAMS_DIR, "mqpar_MQ1.6.3.3_MBR.xml"),
        validate=False,
    )
    nr_feature = result["comparison"]["nr_feature"]
    assert nr_feature["value"] > 1
    assert nr_feature["percentile"] == 100.0
    assert result["comparison"]["median_abs_epsilon_eq_species"]["percentile"] == 100.0  # public is 0.0
    assert json.load(open(result["metrics_json"]))["3.nr_feature"] == nr_feature["value"]
    assert os.path.exists(result["intermediate_csv"])


def test_get_public_results_filters_by_software():
    assert server.get_public_results(MODULE_ID, "maxquant")["total"] == 1
    assert server.get_public_results(MODULE_ID, "Sage")["total"] == 0


MAXQUANT_FILE = os.path.join(DATA_DIR, "MaxQuant_evidence_sample.txt")


def _benchmark_maxquant() -> str:
    return server.benchmark_result(MODULE_ID, "MaxQuant", MAXQUANT_FILE, validate=False)["intermediate_hash"]


def test_get_benchmark_inputs_lists_raw_data_fasta_and_runs():
    inputs = server.get_benchmark_inputs(MODULE_ID)
    assert inputs["files"]["raw_data"]["url"].endswith(".tar.gz")
    assert inputs["files"]["fasta"]["url"].endswith(".zip")
    assert set(inputs["condition_mapper"].values()) == {"A", "B"}


def test_check_parsing_reports_runs_and_missing_columns():
    good = server.check_parsing(MODULE_ID, "MaxQuant", MAXQUANT_FILE)
    assert good["ok"] and good["stage"] == "done"
    assert good["missing_runs"] == [] and len(good["rows_per_run"]) == 6
    wrong = server.check_parsing(MODULE_ID, "Sage", MAXQUANT_FILE)
    assert not wrong["ok"] and wrong["stage"] == "convert"
    assert "peptide" in wrong["missing_mapped_columns"]


def test_extract_parameters_splits_parsed_and_missing():
    params = server.extract_parameters(MODULE_ID, "MaxQuant", os.path.join(PARAMS_DIR, "mqpar_MQ1.6.3.3_MBR.xml"))
    assert params["parsed"]["software_version"] == "1.6.3.3"
    assert "software_version" not in params["not_parsed"]


def test_inspect_intermediate_filters_sorts_and_groups():
    source = _benchmark_maxquant()
    rows = server.inspect_intermediate(MODULE_ID, source, query="nr_observed >= 3", sort_by="epsilon", limit=2)
    assert rows["rows_matched"] <= rows["rows_total"] and len(rows["rows"]) == 2
    groups = server.inspect_intermediate(MODULE_ID, source, group_by="species", columns=["epsilon"])
    assert {g["species"] for g in groups["groups"]} <= {"HUMAN", "YEAST", "ECOLI"}
    assert "median_epsilon" in groups["groups"][0]


def test_compare_results_overlap_and_non_unique_key():
    source = _benchmark_maxquant()
    same = server.compare_results(MODULE_ID, source, source)
    assert same["overlap"]["only_a"] == same["overlap"]["only_b"] == 0
    assert os.path.exists(same["merged_csv"])
    non_unique = server.compare_results(MODULE_ID, source, source, key_columns=["species"])
    assert non_unique["key_unique"] is False and non_unique["overlap"] is None


def test_unknown_source_gives_readable_error():
    with pytest.raises(server.ToolError, match="neither an intermediate_hash"):
        server.inspect_intermediate(MODULE_ID, "does-not-exist")


def test_render_plots_writes_in_depth_html():
    result = server.render_plots(MODULE_ID, _benchmark_maxquant(), include_main=False)
    assert {"logfc", "cv", "ma_plot"} <= set(result["files"])
    assert all(os.path.exists(path) for path in result["files"].values())
