"""Coverage is a share of the reference, so it must never exceed 1.

At peptide level one prediction belongs to one spectrum, so counting scored items counts
covered spectra. At amino-acid level the scored items are *predicted* residues while the
reference is counted in *reference* residues, and those are independent totals: a tool
whose predicted peptides are collectively longer than the reference used to report a
coverage above 1. These tests pin the distinction and leave precision/recall alone.
"""

import numpy as np
import pandas as pd
import pytest

from proteobench.datapoint.denovo_datapoint import (
    DenovoDatapoint,
    calculate_prc,
    get_prc_curve,
)


def _row(gt_len: int, pred_len: int, n_correct: int, score: float = 0.9, dropped: bool = False):
    """One intermediate row: `gt_len` reference residues, `pred_len` predicted ones."""
    matches_dn = np.array([i < n_correct for i in range(pred_len)])
    return {
        "peptidoform": None if dropped else f"PEPTIDE{gt_len}",
        "score": score,
        "match_type": "exact" if n_correct == pred_len == gt_len else "mismatch",
        "aa_scores": [score] * pred_len,
        "aa_matches_gt": np.array([i < n_correct for i in range(gt_len)]),
        "aa_matches_dn": matches_dn,
        "aa_exact_dn": matches_dn,
    }


def _metrics(rows, level: str):
    df = pd.DataFrame(rows)
    return DenovoDatapoint.get_metrics(self=DenovoDatapoint(), df=df, level=level, evaluation="mass")


def test_aa_coverage_stays_within_one_when_predictions_are_longer_than_the_reference():
    """The regression: predicting more residues than exist must not read as >100% coverage."""
    rows = [_row(gt_len=2, pred_len=5, n_correct=1), _row(gt_len=2, pred_len=5, n_correct=1)]

    res = _metrics(rows, "aa")

    # 10 predicted residues against 4 reference residues previously gave 10/4 = 2.5.
    assert res["coverage"] == pytest.approx(1.0)
    assert res["coverage"] <= 1.0


def test_aa_coverage_is_the_reference_share_of_the_attempted_spectra():
    """With a row dropped for an unparseable prediction, only its reference residues leave."""
    rows = [
        _row(gt_len=5, pred_len=7, n_correct=3),
        _row(gt_len=4, pred_len=4, n_correct=4),
        _row(gt_len=6, pred_len=6, n_correct=0, dropped=True),
    ]

    res = _metrics(rows, "aa")

    # Reference residues: 15 in total, 9 on the two rows that kept a prediction.
    assert res["coverage"] == pytest.approx(9 / 15)


def test_aa_precision_and_recall_denominators_are_untouched():
    """Only coverage changes: precision stays per predicted residue, recall per reference one."""
    rows = [
        _row(gt_len=5, pred_len=7, n_correct=3),
        _row(gt_len=4, pred_len=4, n_correct=4),
        _row(gt_len=6, pred_len=6, n_correct=0, dropped=True),
    ]

    res = _metrics(rows, "aa")

    assert res["precision"] == pytest.approx(7 / 11)  # correct / predicted residues
    assert res["recall"] == pytest.approx(7 / 15)  # correct / reference residues


def test_peptide_coverage_is_unchanged():
    """One prediction per spectrum, so scored items already count covered spectra."""
    rows = [
        _row(gt_len=5, pred_len=5, n_correct=5),
        _row(gt_len=4, pred_len=4, n_correct=4),
        _row(gt_len=6, pred_len=6, n_correct=0, dropped=True),
    ]

    res = _metrics(rows, "peptide")

    assert res["coverage"] == pytest.approx(2 / 3)


def test_coverage_equals_recall_over_precision_only_when_the_counts_share_a_unit():
    """The identity that exposed the bug.

    `recall / precision` is always the scored-item count over the reference size. At
    peptide level that is coverage; at amino-acid level it is a ratio between predicted
    and reference residue counts, which is what used to be reported as coverage.
    """
    # One peptide matched exactly, so peptide precision is non-zero and the ratio is defined.
    rows = [_row(gt_len=2, pred_len=2, n_correct=2), _row(gt_len=2, pred_len=5, n_correct=1)]

    peptide = _metrics(rows, "peptide")
    assert peptide["coverage"] == pytest.approx(peptide["recall"] / peptide["precision"])

    amino_acid = _metrics(rows, "aa")
    # 7 predicted residues over 4 reference residues: the old coverage, now plainly not one.
    assert amino_acid["recall"] / amino_acid["precision"] == pytest.approx(7 / 4)
    assert amino_acid["coverage"] == pytest.approx(1.0)


def test_curve_coverage_is_bounded_and_ends_at_the_single_point_coverage():
    """The curve shares the denominator, so it needs the same correction."""
    rows = [
        _row(gt_len=2, pred_len=5, n_correct=1, score=0.9),
        _row(gt_len=2, pred_len=5, n_correct=1, score=0.4),
    ]
    df = pd.DataFrame(rows)

    point = DenovoDatapoint.get_metrics(self=DenovoDatapoint(), df=df, level="aa", evaluation="mass")
    curve = point["curve"]["coverage"]

    assert max(curve) <= 1.0
    assert max(curve) == pytest.approx(point["coverage"])


def test_calculate_prc_defaults_n_covered_to_the_scored_item_count():
    """Callers that pass no `n_covered` keep the previous behaviour."""
    scores = [0.9, 0.8, 0.7]
    correct = [True, True, False]

    assert calculate_prc(scores, correct, n_spectra=4)["coverage"] == pytest.approx(3 / 4)
    assert calculate_prc(scores, correct, n_spectra=4, n_covered=2)["coverage"] == pytest.approx(2 / 4)


def test_get_prc_curve_axis_is_unchanged_when_n_covered_defaults():
    """Peptide-level curves must come out byte-identical to before the fix."""
    scores = [0.9, 0.8, 0.7, 0.6]
    correct = [True, False, True, False]

    curve = get_prc_curve(scores, correct, n_spectra=8)

    # rank / n_spectra, as before: the scale factor is 1 when n_covered == len(scores_all).
    assert curve["coverage"].tolist() == pytest.approx([1 / 8, 2 / 8, 3 / 8, 4 / 8])


def test_get_prc_curve_scales_the_axis_by_the_attempted_fraction():
    scores = [0.9, 0.8, 0.7, 0.6]
    correct = [True, False, True, False]

    curve = get_prc_curve(scores, correct, n_spectra=8, n_covered=4)

    assert curve["coverage"].tolist() == pytest.approx([1 / 8, 2 / 8, 3 / 8, 4 / 8])
    assert max(curve["coverage"]) == pytest.approx(4 / 8)


def test_empty_predictions_still_return_an_empty_curve():
    assert get_prc_curve([], [], n_spectra=5, n_covered=0).empty
