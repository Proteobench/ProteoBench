"""Quant uploads use APB2 parsing and APB ProteoBench scoring directly."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pandas as pd
import pytest

from proteobench.modules.quant.apb_workflow import analyze_quant_upload
from proteobench.modules.quant.apb_settings import APBQuantSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive


_CUSTOM = Path(__file__).parent / "data/quant/quant_lfq_ion_DDA_QExactive/CustomFormat_DDA_quant_ions_test.txt"
_MIGRATED_MODULES = (
    "quant_lfq_DDA_ion_QExactive",
    "quant_lfq_DDA_ion_Astral",
    "quant_lfq_DDA_peptidoform",
    "quant_lfq_DIA_ion_AIF",
    "quant_lfq_DIA_ion_Astral",
    "quant_lfq_DIA_ion_diaPASEF",
    "quant_lfq_DIA_ion_lowinput",
    "quant_lfq_DIA_ion_ZenoTOF",
)


@pytest.mark.parametrize("module_id", _MIGRATED_MODULES)
def test_each_migrated_module_loads_apb_settings(module_id: str) -> None:
    settings = APBQuantSettingsBuilder("", module_id)
    assert settings.INPUT_FORMATS
    assert settings.module.settings.species_expected_ratio


_DDA_ION_MENU = [
    "AlphaPept",
    "Custom",
    "DIA-NN",
    "FragPipe",
    "i2MassChroQ",
    "MaxQuant",
    "MSAngel",
    "PEAKS",
    "ProlineStudio",
    "quantms",
    "Sage",
    "WOMBAT",
]
_DIA_ION_MENU = ["AlphaDIA", "Custom", "DIA-NN", "FragPipe", "MaxQuant", "PEAKS", "Spectronaut"]
_DDA_PEPTIDOFORM_MENU = ["MaxQuant", "Sage", "WOMBAT"]


@pytest.mark.parametrize(
    ("module_id", "expected"),
    [
        ("quant_lfq_DDA_ion_QExactive", _DDA_ION_MENU),
        ("quant_lfq_DDA_ion_Astral", _DDA_ION_MENU),
        ("quant_lfq_DDA_peptidoform", _DDA_PEPTIDOFORM_MENU),
        ("quant_lfq_DIA_ion_AIF", _DIA_ION_MENU),
        ("quant_lfq_DIA_ion_Astral", _DIA_ION_MENU),
        ("quant_lfq_DIA_ion_diaPASEF", _DIA_ION_MENU),
        ("quant_lfq_DIA_ion_lowinput", _DIA_ION_MENU),
        ("quant_lfq_DIA_ion_ZenoTOF", _DIA_ION_MENU),
    ],
)
def test_upload_menu_uses_apb2_rule_catalog(module_id: str, expected: list[str]) -> None:
    assert APBQuantSettingsBuilder("", module_id).INPUT_FORMATS == expected


@pytest.mark.parametrize(
    ("module_id", "category", "level"),
    [
        ("quant_lfq_DDA_ion_QExactive", "DDA", "ion"),
        ("quant_lfq_DIA_ion_Astral", "DIA", "ion"),
        ("quant_lfq_DDA_peptidoform", "DDA", "peptidoform"),
    ],
)
def test_upload_menu_queries_apb2_by_module_and_level(
    monkeypatch: pytest.MonkeyPatch, module_id: str, category: str, level: str
) -> None:
    calls = []

    def fake_get_rules(actual_category: str, *, level: str) -> list[SimpleNamespace]:
        calls.append((actual_category, level))
        return [SimpleNamespace(software_name="Example")]

    monkeypatch.setattr("proteobench.modules.quant.apb_settings.get_rules", fake_get_rules)

    assert APBQuantSettingsBuilder("", module_id).INPUT_FORMATS == ["Example"]
    assert calls == [(category, level)]


def test_custom_upload_uses_apb_parsing_and_scoring() -> None:
    analysis = analyze_quant_upload(_CUSTOM, software="pb_custom", module="dda_qexactive")

    assert analysis.software == "pbcustom"
    assert set(analysis.result.parsed.levels) == {"ion"}
    assert analysis.result.selection.layer_names == ("Intensity",)
    assert len(analysis.intermediate) == 8199
    assert set(analysis.selected_layer.analysis.scores.results) == {"1", "2", "3", "4", "5", "6"}
    assert "epsilon" in analysis.intermediate
    assert analysis.result.parsed.metadata["proteobench"]["provenance"]["scoring"]
    assert len(analysis.content_hash) == 64
    assert (
        analyze_quant_upload(_CUSTOM, software="Custom", module="dda_qexactive").content_hash == analysis.content_hash
    )
    datapoint = analysis.datapoint(input_format="Custom", user_input={})
    assert datapoint["intermediate_hash"] == analysis.content_hash
    assert datapoint["results"]["3"]["nr_feature"] == datapoint["nr_feature"]


def test_unsupported_producer_has_no_legacy_parser_fallback() -> None:
    with pytest.raises(ValueError, match="software"):
        analyze_quant_upload(_CUSTOM, software="metamorpheus", module="dda_qexactive")


def test_quant_ui_settings_come_from_apb_module() -> None:
    settings = APBQuantSettingsBuilder("", "quant_lfq_DDA_ion_QExactive")

    assert "Custom" in settings.INPUT_FORMATS
    assert "MetaMorpheus" not in settings.INPUT_FORMATS
    assert not settings.supports_secondary_result_upload
    assert settings.build_parser("Custom") is settings
    assert settings.species_expected_ratio()["YEAST"]["color"] == "#88ccef"
    with pytest.raises(ValueError, match="not offered"):
        settings.build_parser("MetaMorpheus")


def test_qexactive_module_uses_apb_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda self: None)
    module = DDAQuantIonModuleQExactive("")
    intermediate, datapoints, analysis = module.benchmarking(str(_CUSTOM), "Custom", {}, pd.DataFrame())
    assert module.last_apb_analysis is not None
    assert analysis is module.last_apb_analysis
    assert intermediate.equals(analysis.intermediate)
    assert len(intermediate) == 8199
    assert datapoints.iloc[-1]["intermediate_hash"] == module.last_apb_analysis.content_hash


def test_submission_archive_contains_scored_h5ad_and_csv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda self: None)
    module = DDAQuantIonModuleQExactive("")
    intermediate, datapoints, analysis = module.benchmarking(str(_CUSTOM), "Custom", {}, pd.DataFrame())
    digest = datapoints.iloc[-1]["intermediate_hash"]
    raw = BytesIO(_CUSTOM.read_bytes())
    module.write_intermediate_raw(str(tmp_path), digest, raw, intermediate, [], "test", ".txt", analysis=analysis)

    archive = tmp_path / digest / f"{digest}_data.zip"
    with ZipFile(archive) as bundle:
        assert {
            "input_file.txt",
            "result_performance.csv",
            "scored.h5ad",
            "scored.h5ad.apb.json",
            "comment.txt",
        } <= set(bundle.namelist())
    with pytest.raises(FileExistsError, match="already exists"):
        module.write_intermediate_raw(str(tmp_path), digest, raw, intermediate, [], "test", ".txt", analysis=analysis)


def test_quant_parameter_upload_uses_apb2_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda self: None)
    module = DDAQuantIonModuleQExactive("")
    parameters = module.load_params_file(
        [Path(__file__).parent / "params/mqpar_MQ1.6.3.3_MBR.xml"],
        "MaxQuant",
        str(Path(__file__).parent.parent / "proteobench/io/params/json/Quant/quant_lfq_DDA_ion.json"),
    )

    assert parameters.software_name == "MaxQuant"
    assert parameters.search_engine == "Andromeda"
    assert parameters.ident_fdr_psm == 0.01
    assert parameters.fixed_mods == "C[Carbamidomethyl]"
