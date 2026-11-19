"""Exact-mode matching compares modifications as chemistry, not as the text they were written in.

A tool and the ground truth can spell the same modification differently: a UNIMOD accession, a
PSI-MOD or Unimod name, a formula, a bare mass shift, or, for an N-terminal group, several stacked
tags against one formula tag. `DenovoScores.tokens_identical` must call those identical, and still
tell different modifications apart.
"""

import pytest

from proteobench.io.parsing.parse_settings import parse_peptidoform_or_none
from proteobench.score.denovoscores import DenovoScores

PEPTIDE = "QAATMESLTPLLINLAK"


@pytest.fixture(scope="module")
def scores():
    return DenovoScores()


def match_type(scores, ground_truth, prediction, allow_il=False, allow_deamidation=False):
    gt = parse_peptidoform_or_none(ground_truth)
    dn = parse_peptidoform_or_none(prediction)
    assert gt is not None and dn is not None
    return scores.evaluate_match(gt, dn, allow_il=allow_il, allow_deamidation=allow_deamidation)["match_type"]


def first_tokens(scores, a, b):
    return (
        scores.convert_peptidoform(parse_peptidoform_or_none(a))[0],
        scores.convert_peptidoform(parse_peptidoform_or_none(b))[0],
    )


# The nine-species ground truth writes carbamylation + ammonia loss as one formula tag; tools write
# the same group as two stacked UNIMOD tags, in either order, or as its mass.
@pytest.mark.parametrize(
    "prediction",
    [
        f"[UNIMOD:5][UNIMOD:385]-{PEPTIDE}",
        f"[UNIMOD:385][UNIMOD:5]-{PEPTIDE}",
        f"[UNIMOD:5]-[UNIMOD:385]-{PEPTIDE}",
        f"[Carbamyl][Ammonia-loss]-{PEPTIDE}",
        f"[Formula:C1H-2O1]-{PEPTIDE}",
        f"[+25.979]-{PEPTIDE}",
    ],
)
@pytest.mark.parametrize("allow_il", [False, True])
@pytest.mark.parametrize("allow_deamidation", [False, True])
def test_stacked_nterm_group_is_exact(scores, prediction, allow_il, allow_deamidation):
    ground_truth = f"[Formula:H-2C1O1]-{PEPTIDE}"
    assert match_type(scores, ground_truth, prediction, allow_il, allow_deamidation) == "exact"


@pytest.mark.parametrize(
    "ground_truth, prediction",
    [
        ("PEPM[UNIMOD:35]K", "PEPM[Oxidation]K"),
        ("PEPM[UNIMOD:35]K", "PEPM[+15.995]K"),
        ("PEPM[UNIMOD:35]K", "PEPM[Formula:O1]K"),
        ("PEPC[UNIMOD:4]K", "PEPC[Carbamidomethyl]K"),
        ("[UNIMOD:1]-PEPK", "[Acetyl]-PEPK"),
        ("[UNIMOD:1]-PEPK", "[+42.011]-PEPK"),
    ],
)
def test_equivalent_spellings_are_exact(scores, ground_truth, prediction):
    assert match_type(scores, ground_truth, prediction) == "exact"
    assert match_type(scores, prediction, ground_truth) == "exact"


@pytest.mark.parametrize(
    "a, b",
    [
        # Acetylation (42.0106 Da) and trimethylation (42.0470 Da): different compositions.
        ("K[UNIMOD:1]PEPR", "K[UNIMOD:37]PEPR"),
        # The same pair, one side written as a mass shift: compared by mass, 0.036 Da apart.
        ("K[+42.011]PEPR", "K[UNIMOD:37]PEPR"),
        # Two mass shifts further apart than the tolerance.
        ("M[+15.995]PEPK", "M[+16.019]PEPK"),
        # A modification against none.
        ("M[UNIMOD:35]PEPK", "MPEPK"),
        # One N-terminal tag of a stacked pair against the pair.
        (f"[UNIMOD:5]{PEPTIDE}", f"[UNIMOD:5][UNIMOD:385]-{PEPTIDE}"),
    ],
)
def test_different_modifications_are_not_identical(scores, a, b):
    token_a, token_b = first_tokens(scores, a, b)
    assert not scores.tokens_identical(token_a, token_b, allow_il=True, allow_deamidation=True)
    assert not scores.tokens_identical(token_b, token_a, allow_il=True, allow_deamidation=True)


@pytest.mark.parametrize("deamidated", ["N[UNIMOD:7]", "N[Deamidated]", "N[+0.984]", "N[Formula:H-1N-1O1]"])
def test_deamidation_toggle_reads_any_spelling(scores, deamidated):
    token_n, token_d = first_tokens(scores, f"{deamidated}PEPK", "DPEPK")
    assert scores.tokens_identical(token_n, token_d, allow_deamidation=True)
    assert not scores.tokens_identical(token_n, token_d, allow_deamidation=False)


def test_residues_still_differ(scores):
    token_i, token_l = first_tokens(scores, "IPEPK", "LPEPK")
    assert not scores.tokens_identical(token_i, token_l)
    assert scores.tokens_identical(token_i, token_l, allow_il=True)
    token_k, token_q = first_tokens(scores, "KPEPK", "QPEPK")
    assert not scores.tokens_identical(token_k, token_q, allow_il=True, allow_deamidation=True)


def test_identical_spelling_is_exact(scores):
    for peptide in (PEPTIDE, f"[UNIMOD:1]-{PEPTIDE}", "PEPM[UNIMOD:35]C[UNIMOD:4]K"):
        assert match_type(scores, peptide, peptide) == "exact"
