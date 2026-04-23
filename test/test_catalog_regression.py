"""Regression harness over the test-dataset catalog.

For each row in `test_data_download/raw_file_db_downloaded.csv`, re-runs the
corresponding quant module's benchmarking pipeline against the cached input
file and compares the regenerated metrics to the values stored in the
original submission JSON at `json_dir/{repo}/{repo}-main/{hash}.json`.

Skipped entirely if the catalog CSV or json_dir is absent, so the suite
stays green on a fresh clone. Opt in locally by running:

    cd test_data_download && make catalog && make select && make download
"""

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

from proteobench.datapoint.quant_datapoint import QuantDatapointHYE
from proteobench.modules.quant.quant_lfq_ion_DDA_Astral import DDAQuantIonAstralModule
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModuleAIF
from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import DIAQuantIonModulediaPASEF
from proteobench.modules.quant.quant_lfq_ion_DIA_singlecell import DIAQuantIonModulediaSC
from proteobench.modules.quant.quant_lfq_ion_DIA_ZenoTOF import DIAQuantIonModuleZenoTOF
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import DDAQuantPeptidoformModule

pytestmark = pytest.mark.regression


MODULE_KEY_TO_CLASS = {
    "dda_qexactive": DDAQuantIonModuleQExactive,
    "dda_astral": DDAQuantIonAstralModule,
    "dda_peptidoform": DDAQuantPeptidoformModule,
    "dia_astral": DIAQuantIonModuleAstral,
    "dia_diapasef": DIAQuantIonModulediaPASEF,
    "dia_aif": DIAQuantIonModuleAIF,
    "dia_zenotof": DIAQuantIonModuleZenoTOF,
    "dia_singlecell": DIAQuantIonModulediaSC,
}

METRICS_TO_CHECK = [
    "nr_prec",
    "roc_auc",
    "median_abs_epsilon_global",
    "mean_abs_epsilon_global",
    "CV_median",
]

THRESHOLD = 3

DATA_ROOT = Path(__file__).parent.parent / "test_data_download"
CSV_PATH = DATA_ROOT / "raw_file_db_downloaded.csv"
JSON_ROOT = DATA_ROOT / "json_dir"
OVERRIDES_PATH = Path(__file__).parent / "catalog_regression_overrides.json"

_OVERRIDES = {}
if OVERRIDES_PATH.exists():
    with open(OVERRIDES_PATH) as _f:
        _OVERRIDES = {k: v for k, v in json.load(_f).items() if not k.startswith("_")}


def _load_parametrize_rows():
    """Read the catalog CSV and return (rows, ids) for pytest.parametrize.

    Returns empty lists if the CSV or json_dir is missing — the test body
    then skips cleanly. Rows with status != 'ok' or with legacy JSONs that
    lack any METRICS_TO_CHECK key are filtered out at collection time.
    """
    if not CSV_PATH.exists() or not JSON_ROOT.exists():
        return [], []

    df = pd.read_csv(CSV_PATH)
    df = df[df["status"] == "ok"]

    rows, ids = [], []
    for row in df.to_dict(orient="records"):
        override = _OVERRIDES.get(row["intermediate_hash"])
        if override is not None:
            expected = override["metrics"]
        else:
            json_path = JSON_ROOT / row["repo_name"] / f"{row['repo_name']}-main" / f"{row['intermediate_hash']}.json"
            if not json_path.exists():
                continue
            with open(json_path) as f:
                stored = json.load(f)
            expected = stored.get("results", {}).get(str(THRESHOLD), {})
            if not all(m in expected for m in METRICS_TO_CHECK):
                continue
        rows.append((row, expected))
        software = str(row["software_name"]).replace(" ", "_").replace("/", "-")
        version = str(row["software_version"]).strip().replace(" ", "_") or "na"
        ids.append(f"{row['module']}__{software}__{version}__{row['intermediate_hash'][:8]}")
    return rows, ids


_ROWS, _IDS = _load_parametrize_rows()


@pytest.fixture(autouse=True)
def _mock_github(monkeypatch):
    """Skip the GithubProteobotRepo clone that ModuleClass.__init__ triggers."""
    monkeypatch.setattr(
        "proteobench.github.gh.GithubProteobotRepo.clone_repo",
        lambda self: None,
    )
    monkeypatch.setattr(
        "proteobench.github.gh.GithubProteobotRepo.read_results_json_repo",
        lambda self: pd.DataFrame(),
    )


@pytest.mark.skipif(
    not CSV_PATH.exists(),
    reason=f"{CSV_PATH.name} not found — run `make -C test_data_download download` to populate.",
)
@pytest.mark.skipif(not _ROWS, reason="no catalog rows passed the pre-filter (status + metric presence)")
@pytest.mark.parametrize("row,stored_metrics", _ROWS, ids=_IDS)
def test_catalog_row_metrics_match_stored(row, stored_metrics):
    """Regenerated metrics must match what the submission JSON recorded."""
    module_cls = MODULE_KEY_TO_CLASS[row["module"]]
    input_file = JSON_ROOT / row["input_file_path"]
    assert input_file.exists(), f"input file missing: {input_file}"

    hash_dir = input_file.parent
    secondary_candidates = sorted(hash_dir.glob("input_file_secondary.*"))
    secondary = str(secondary_candidates[0]) if secondary_candidates else None

    module = module_cls(token="")
    intermediate, _, _ = module.benchmarking(
        str(input_file),
        row["software_name"],
        user_input=defaultdict(str),
        all_datapoints=None,
        input_file_secondary=secondary,
    )

    regenerated = QuantDatapointHYE.get_metrics(intermediate, min_nr_observed=THRESHOLD)[THRESHOLD]

    mismatches = []
    for metric in METRICS_TO_CHECK:
        expected = stored_metrics[metric]
        actual = regenerated.get(metric)
        if actual != pytest.approx(expected, rel=1e-4, abs=1e-6):
            mismatches.append(f"  {metric}: regenerated={actual!r} stored={expected!r}")
    assert not mismatches, "metric drift detected:\n" + "\n".join(mismatches)
