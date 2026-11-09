"""Regression tests for GHSA-p237-rc4h-82vq and GHSA-grf4-6jmf-4mp7.

Text read from uploaded result files and submitted datapoints is untrusted. It must never be
evaluated as Python: not by ``eval``/``exec`` (code execution) and not by ``ast.literal_eval``
(memory exhaustion, C-stack overflow and CPU blowups on crafted input). None of the affected sites
needs Python-literal parsing, because each reads a fixed text format:

- per-residue scores are comma-separated numbers, optionally in square brackets;
- NovoB writes sequences as the text ``['SEQUENCE']`` and spectrum ids as ``b'5280'``, from which
  the TOML ``spectrum_id_mapper`` pattern extracts the scan number;
- in-depth plot metrics are dicts, and only missing bins need filling.

Each code payload below would create a marker file if it were executed, so the tests check that
the marker is never written.
"""

import ast
import time
from pathlib import Path

import pandas as pd
import pytest
from psm_utils import Peptidoform

import proteobench
from proteobench.io.parsing.parse_denovo import _unwrap_novob_sequence, load_input_file
from proteobench.io.parsing.parse_settings import (
    MAX_SCORE_STRING_LENGTH,
    ParseSettingsBuilder,
    ParseSettingsDeNovo,
    parse_score_string,
)
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.plotting.plot_generator_denovo import EMPTY_METRICS, DeNovoPlotGenerator

# A well-formed row from the NovoB fork used by the de novo benchmark pipeline: Mcount, charge,
# peptide_mass, sequence_forward, mass_forward, probability_forward, sequence_reverse,
# mass_reverse, probability_reverse, spectrum_id.
NOVOB_ROW = ["1", "2", "1000.5", "['PEPTIDE']", "0.01", "0.9", "['PEPTIDR']", "0.02", "0.5", "b'5280'"]
SEQUENCE_COLUMNS = {"sequence_forward": 3, "sequence_reverse": 6}
SPECTRUM_ID_COLUMN = 9
DEEPLY_NESTED = "[" * 100_000 + "]" * 100_000


def _payload(marker: Path) -> str:
    """A Python expression that creates `marker` when executed."""
    return f"__import__('pathlib').Path('{marker.as_posix()}').touch()"


def _write_novob(path: Path, row: list) -> Path:
    path.write_text("\t".join(row) + "\n", encoding="utf-8")
    return path


class _Settings(ParseSettingsDeNovo):
    """ParseSettingsDeNovo without the TOML plumbing; only `format_scores` is exercised."""

    def __init__(self):
        pass


class TestParseScoreString:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("0.98494,0.97609,0.94686", [0.98494, 0.97609, 0.94686]),  # mzTab: Casanovo, AdaNovo, ContraNovo
            ("[0.98417956, 0.9437962, 0.9997547]", [0.98417956, 0.9437962, 0.9997547]),  # PepNet
            ("[-0.01, -0.02, -0.03]", [-0.01, -0.02, -0.03]),  # InstaNovo token_log_probs
            ("-0.71,-1.2e-05,3", [-0.71, -1.2e-05, 3.0]),
            (" [ 0.5 , 0.25 ] ", [0.5, 0.25]),
            ("0.9", [0.9]),
            ("[]", []),
        ],
    )
    def test_tool_formats(self, text, expected):
        assert parse_score_string(text) == expected

    @pytest.mark.parametrize(
        "text",
        [
            "__import__('os').getcwd()",
            "[0.1, foo]",
            "[[0.1, 0.2]]",
            "(0.1, 0.2)",
            "{'a': 1}",
            "0.1,,0.2",
            "nan,0.5",
            "0.5,inf",
        ],
    )
    def test_anything_but_numbers_is_rejected(self, text):
        with pytest.raises(ValueError):
            parse_score_string(text)

    def test_oversized_text_is_rejected(self):
        with pytest.raises(ValueError, match="characters long"):
            parse_score_string("0," * MAX_SCORE_STRING_LENGTH)

    def test_deep_nesting_is_rejected(self):
        depth = MAX_SCORE_STRING_LENGTH // 2
        with pytest.raises(ValueError):
            parse_score_string("[" * depth + "]" * depth)

    def test_worst_case_input_is_fast(self):
        n = MAX_SCORE_STRING_LENGTH
        start = time.perf_counter()
        for text in ["1" * n, "0." + "1" * (n - 2), "[" + "1," * (n // 2 - 1) + "]", "1" * (n - 1) + "x"]:
            try:
                parse_score_string(text)
            except ValueError:
                pass
        assert time.perf_counter() - start < 1.0


class TestNovoB:
    @pytest.mark.parametrize(
        "text, expected", [("['PEPTIDE']", "PEPTIDE"), ("['PEPmTIDEs']", "PEPmTIDEs"), ("['']", "")]
    )
    def test_sequence_wrapper_is_removed(self, text, expected):
        assert _unwrap_novob_sequence(text) == expected

    @pytest.mark.parametrize(
        "text",
        [
            "PEPTIDE",
            "['PEP', 'TIDE']",
            '["PEPTIDE"]',
            "['PEP TIDE']",
            "[__import__('os')]",
            # Explicit id: a 200k-character id overflows the PYTEST_CURRENT_TEST env var on Windows.
            pytest.param(DEEPLY_NESTED, id="deeply_nested"),
        ],
    )
    def test_anything_else_is_rejected(self, text):
        with pytest.raises(ValueError):
            _unwrap_novob_sequence(text)

    def test_wellformed_file_still_parses(self, tmp_path):
        df = load_input_file(str(_write_novob(tmp_path / "novob.tsv", NOVOB_ROW)), "NovoB")
        row = df.iloc[0]
        assert row["sequence_forward"] == "PEPTIDE"
        assert row["sequence_reverse"] == "PEPTIDR"
        # Forward has the higher probability, so it is selected.
        assert row["sequence"] == "PEPTIDE"
        assert row["score"] == pytest.approx(0.9)

    def test_scan_number_comes_from_the_toml_pattern(self):
        """No decoding needed: the NovoB spectrum_id_mapper pattern reads the scan from b'5280'."""
        parser = ParseSettingsBuilder(
            parse_settings_dir=MODULE_SETTINGS_DIRS["denovo_DDA_HCD"], module_id="denovo_DDA_HCD"
        ).build_parser("NovoB")
        assert parser.extract_scan_id("b'5280'") == 5280

    @pytest.mark.parametrize("column", SEQUENCE_COLUMNS)
    def test_code_in_a_sequence_cell_is_rejected(self, tmp_path, column):
        marker = tmp_path / "pwned"
        row = list(NOVOB_ROW)
        row[SEQUENCE_COLUMNS[column]] = _payload(marker)
        with pytest.raises(ValueError):
            load_input_file(str(_write_novob(tmp_path / "novob.tsv", row)), "NovoB")
        assert not marker.exists(), f"code in the {column} column was executed"

    def test_code_in_the_spectrum_id_cell_stays_text(self, tmp_path):
        marker = tmp_path / "pwned"
        row = list(NOVOB_ROW)
        row[SPECTRUM_ID_COLUMN] = _payload(marker)
        df = load_input_file(str(_write_novob(tmp_path / "novob.tsv", row)), "NovoB")
        assert df.iloc[0]["spectrum_id"] == row[SPECTRUM_ID_COLUMN]
        assert not marker.exists(), "code in the spectrum_id column was executed"


class TestFormatScores:
    def test_score_strings_still_parse(self):
        peptidoform = Peptidoform("PEPTIDE")
        assert _Settings().format_scores("[0.1, 0.2, 0.3]", peptidoform) == [0.1, 0.2, 0.3]
        assert _Settings().format_scores("0.1,0.2,0.3", peptidoform) == [0.1, 0.2, 0.3]

    def test_code_in_aa_scores_is_not_executed(self, tmp_path):
        marker = tmp_path / "pwned"
        with pytest.raises(ValueError):
            _Settings().format_scores(_payload(marker), Peptidoform("PEPTIDE"))
        assert not marker.exists(), "code in the aa_scores column was executed"

    def test_deeply_nested_aa_scores_are_rejected(self):
        with pytest.raises(ValueError):
            _Settings().format_scores(DEEPLY_NESTED, Peptidoform("PEPTIDE"))


def _metrics_df(datapoints) -> pd.DataFrame:
    """A datapoint frame from (id, spectrum bins, species) tuples."""
    return pd.DataFrame(
        {
            "results": [
                {"in_depth": {"Spectrum": {"Peptide Length": bins}, "Species": species}}
                for _, bins, species in datapoints
            ],
            "software_name": ["Casanovo"] * len(datapoints),
            "id": [dtp_id for dtp_id, _, _ in datapoints],
        }
    )


METRICS = {"exact": 0.4, "mass": 0.5, "n_spectra": 3}


class TestDeNovoPlots:
    def test_missing_bins_are_filled_with_empty_metrics(self):
        frame = _metrics_df(
            [
                ("dtp_1", {"7": METRICS, "8": METRICS}, {"Yeast": METRICS, "Human": METRICS}),
                ("dtp_2", {"8": METRICS}, {"Human": METRICS}),
            ]
        )
        plotter = DeNovoPlotGenerator()
        spectrum = plotter.plot_spectrum_feature(frame, "Peptide Length")
        species = plotter.plot_species_overview(frame)
        # dtp_2 has no "7" bin and no "Yeast" entry, so those points come from EMPTY_METRICS.
        assert list(spectrum.data[1].y) == [EMPTY_METRICS["mass"], METRICS["mass"]]
        assert list(species.data[1].y) == [EMPTY_METRICS["mass"], METRICS["mass"]]

    def test_code_in_spectrum_metrics_is_not_executed(self, tmp_path):
        marker = tmp_path / "pwned"
        frame = _metrics_df([("dtp_1", {"7": _payload(marker)}, {"Human": METRICS})])
        with pytest.raises(TypeError):
            DeNovoPlotGenerator().plot_spectrum_feature(frame, "Peptide Length")
        assert not marker.exists(), "code in a datapoint's spectrum metrics was executed"

    def test_code_in_species_metrics_is_not_executed(self, tmp_path):
        marker = tmp_path / "pwned"
        frame = _metrics_df([("dtp_1", {"7": METRICS}, {"Human": _payload(marker)})])
        with pytest.raises(TypeError):
            DeNovoPlotGenerator().plot_species_overview(frame)
        assert not marker.exists(), "code in a datapoint's species metrics was executed"


def test_library_never_evaluates_text_as_python():
    """Guard against reintroducing eval(), exec() or ast.literal_eval() in the proteobench package."""
    banned = {"eval", "exec", "literal_eval"}
    package_dir = Path(proteobench.__file__).parent
    offenders = []
    for source in package_dir.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name in banned:
                offenders.append(f"{source.relative_to(package_dir)}:{node.lineno} {name}()")
    assert not offenders, "Parse the specific text format instead of evaluating it: " + ", ".join(offenders)
