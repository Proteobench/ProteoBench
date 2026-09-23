"""QExactive quant modules use APB parsing and scoring."""

from pathlib import Path

import pandas as pd
import pytest

from proteobench.exceptions import DatasetAlreadyExistsOnServerError
from proteobench.modules.quant.apb_settings import APBQuantSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive

DATA = Path(__file__).parent / "data/quant/quant_lfq_ion_DDA_QExactive"
VERIFIED = {
    "Custom": "CustomFormat_DDA_quant_ions_test.txt",
    "MaxQuant": "MaxQuant_evidence_sample.txt",
    "FragPipe": "FragPipe_MSFragger_combined_ion.tsv",
    "MSAngel": "MSAngel_DDA_quan_ions_subset.xlsx",
    "quantms": "sample_dda_quantms.sdrf_openms_design_msstats_in.csv",
    "WOMBAT": "WOMBAT_stand_ion_quant_mergedproline.csv",
}


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch) -> DDAQuantIonModuleQExactive:
    monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda self: None)
    return DDAQuantIonModuleQExactive("")


def test_upload_handoff_uses_apb(module: DDAQuantIonModuleQExactive) -> None:
    intermediate, datapoints, analysis = module.benchmarking(
        str(DATA / VERIFIED["Custom"]), "Custom", {}, pd.DataFrame()
    )
    assert not intermediate.empty
    assert analysis.result.selection.layer_names == ("Intensity",)
    assert datapoints.iloc[-1]["intermediate_hash"] == analysis.content_hash


def test_menu_only_lists_verified_producers() -> None:
    assert set(APBQuantSettingsBuilder("", "quant_lfq_DDA_ion_QExactive").INPUT_FORMATS) == set(VERIFIED)


def test_duplicate_upload_retains_one_datapoint(module: DDAQuantIonModuleQExactive) -> None:
    source = str(DATA / VERIFIED["MaxQuant"])
    _, previous, _ = module.benchmarking(source, "MaxQuant", {}, pd.DataFrame())
    _, datapoints, _ = module.benchmarking(source, "MaxQuant", {}, previous)
    assert len(datapoints) == 1


def test_duplicate_public_hash_is_rejected(module: DDAQuantIonModuleQExactive) -> None:
    datapoints = pd.DataFrame(
        {"old_new": ["old", "new"], "intermediate_hash": ["duplicate", "duplicate"], "id": ["old", "new"]}
    )
    with pytest.raises(DatasetAlreadyExistsOnServerError):
        module.check_new_unique_hash(datapoints)
