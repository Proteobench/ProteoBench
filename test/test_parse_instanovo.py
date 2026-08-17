from pathlib import Path

import pandas as pd

import proteobench.io.parsing.parse_settings as parse_settings_module
from proteobench.io.parsing.parse_denovo import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS

TESTDATA_DIR = Path(__file__).parent / "data" / "denovo"
INSTANOVO_RESULTS = TESTDATA_DIR / "results" / "instanovo" / "denovo_benchmark_test.instanovo.csv"


def test_load_instanovo_csv():
    actual = load_input_file(INSTANOVO_RESULTS, "InstaNovo")

    assert list(actual["scan_number"]) == [100, 101]
    assert list(actual["predictions"]) == ["PEPTIDE", "M[UNIMOD:35]PEPTIDE"]
    assert list(actual["log_probs"]) == [-0.25, -0.75]


def test_instanovo_parse_settings_convert_to_standard_format(tmp_path, monkeypatch):
    ground_truth = pd.DataFrame(
        {
            "spectrum_id": [100, 101],
            "peptidoform": ["PEPTIDE", "M[UNIMOD:35]PEPTIDE"],
            "proforma": ["PEPTIDE", "M[UNIMOD:35]PEPTIDE"],
            "precursor_mz": [400.2, 512.3],
            "retention_time": [10.0, 20.0],
            "title": ["scan=100", "scan=101"],
            "missing_frag_sites": [0, 1],
            "missing_frag_pct": [0.0, 0.1],
            "explained_y_pct": [0.8, 0.7],
            "explained_b_pct": [0.6, 0.5],
            "explained_by_pct": [0.9, 0.85],
            "explained_all_pct": [0.95, 0.9],
            "cos": [0.9, 0.8],
            "cos_ionb": [0.7, 0.6],
            "cos_iony": [0.8, 0.7],
            "spec_pearson": [0.85, 0.75],
            "dotprod": [0.95, 0.9],
            "collection": ["test", "test"],
        }
    )
    ground_truth.to_csv(tmp_path / parse_settings_module.GROUND_TRUTH_FILENAME, index=False, compression="gzip")

    monkeypatch.setattr(parse_settings_module, "GROUND_TRUTH_DIR_SERVER", str(tmp_path / "server"))
    monkeypatch.setattr(parse_settings_module, "GROUND_TRUTH_DIR_LOCAL_DENOVO", str(tmp_path))

    input_df = load_input_file(INSTANOVO_RESULTS, "InstaNovo")
    parser = ParseSettingsBuilder(
        parse_settings_dir=MODULE_SETTINGS_DIRS["denovo_DDA_HCD"],
        module_id="denovo_DDA_HCD",
    ).build_parser("InstaNovo")

    actual = parser.convert_to_standard_format(input_df)

    assert list(actual["spectrum_id"]) == [100, 101]
    assert list(actual["proforma"]) == ["PEPTIDE", "M[UNIMOD:35]PEPTIDE"]
    assert list(actual["score"]) == [-0.25, -0.75]
    assert actual["aa_scores"].iloc[0] == [-0.01, -0.02, -0.03, -0.04, -0.05, -0.06, -0.07]
    assert actual["M-Oxidation (denovo)"].tolist() == [False, True]
