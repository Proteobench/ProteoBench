"""AIF quant modules use APB parsing and scoring."""

from pathlib import Path

import pandas as pd
import pytest

from proteobench.modules.quant.apb_settings import APBQuantSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModuleAIF

DATA = Path(__file__).parent / "data/quant/quant_lfq_ion_DIA_AIF"
VERIFIED = {
    "AlphaDIA": "AlphaDIA_1.10_sample.tsv",
    "MaxQuant": "MaxDIA_sample_test.txt",
    "FragPipe": "Fragpipe_combined_ion.tsv",
}


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch) -> DIAQuantIonModuleAIF:
    monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda self: None)
    return DIAQuantIonModuleAIF("")


def test_upload_handoff_uses_apb(module: DIAQuantIonModuleAIF) -> None:
    intermediate, datapoints, analysis = module.benchmarking(
        str(DATA / VERIFIED["AlphaDIA"]), "AlphaDIA", {}, pd.DataFrame()
    )
    assert not intermediate.empty
    assert analysis.result.selection.layer_names == ("Intensity",)
    assert datapoints.iloc[-1]["intermediate_hash"] == analysis.content_hash


def test_menu_only_lists_verified_producers() -> None:
    assert set(APBQuantSettingsBuilder("", "quant_lfq_DIA_ion_AIF").INPUT_FORMATS) == set(VERIFIED)


def test_distinct_producers_add_distinct_datapoints(module: DIAQuantIonModuleAIF) -> None:
    _, previous, _ = module.benchmarking(str(DATA / VERIFIED["AlphaDIA"]), "AlphaDIA", {}, pd.DataFrame())
    _, datapoints, _ = module.benchmarking(str(DATA / VERIFIED["MaxQuant"]), "MaxQuant", {}, previous)
    assert len(datapoints) == 2
