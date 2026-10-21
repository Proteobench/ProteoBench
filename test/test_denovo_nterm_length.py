"""Length agreement between the de novo tokenizer and the score-length helpers.

`DenovoScores.convert_peptidoform` scores the N-terminal group as ONE token however many
modifications are stacked on it. Two helpers have to agree with that count, or
`collapse_aa_scores` raises "All arrays must be of the same length" and takes the whole run
with it:

* `get_length_peptidoform_with_nterm`, which sizes the broadcast for tools that supply no
  per-residue scores;
* `format_scores`, which reconciles the length for tools that do.

These tests pin the invariant for every N-terminal spelling, so the two sides cannot drift
apart again regardless of how a ProForma parser of the day reports the group.
"""

import copy

import numpy as np
import pytest
from psm_utils import Peptidoform

from proteobench.datapoint.denovo_datapoint import collapse_aa_scores
from proteobench.io.parsing.parse_settings import ParseSettingsDeNovo
from proteobench.score.denovoscores import DenovoScores

# Carbamylation (+43.005814) stacked with ammonia loss (-17.026549) sums to 25.979265, whose
# composition is H-2C1O1. A 133-residue InstaNovo vocabulary carries it as one token and
# detokenizes it to two ProForma tags; older vocabularies had it only as a single composite.
# Every spelling below is the same chemistry, and all must score identically in length.
COMPOSITE_SPELLINGS = [
    "[Formula:H-2C1O1]-ALHTDSVSLINITPR",
    "[Formula:C1H-2O1]-ALHTDSVSLINITPR",
    "[+25.979265]-ALHTDSVSLINITPR",
]
SINGLE_MOD = "[UNIMOD:5]-ALHTDSVSLINITPR"
UNMODIFIED = "ALHTDSVSLINITPR"


class _Settings(ParseSettingsDeNovo):
    """ParseSettingsDeNovo without the TOML plumbing; only the length helpers are exercised."""

    def __init__(self):
        pass


@pytest.fixture
def settings():
    return _Settings()


@pytest.fixture
def scorer():
    return DenovoScores()


def stacked_nterm(proforma: str = SINGLE_MOD) -> Peptidoform:
    """A peptidoform with two N-terminal modifications.

    Built by extending `n_term` rather than by parsing "[UNIMOD:5][UNIMOD:385]-...", because
    whether that string parses at all depends on the pyteomics version -- which is precisely
    the fragility these tests must not inherit.
    """
    peptidoform = Peptidoform(proforma)
    n_term = list(peptidoform.properties["n_term"])
    peptidoform.properties["n_term"] = n_term + [copy.deepcopy(n_term[0])]
    return peptidoform


class TestLengthMatchesTokenization:
    """`get_length_peptidoform_with_nterm` must equal the tokenizer's token count."""

    @pytest.mark.parametrize("proforma", [UNMODIFIED, SINGLE_MOD, *COMPOSITE_SPELLINGS])
    def test_parsed_spellings_agree(self, settings, scorer, proforma):
        peptidoform = Peptidoform(proforma)
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(scorer.convert_peptidoform(peptidoform))

    def test_two_stacked_nterm_mods_agree(self, settings, scorer):
        """The regression: two N-terminal mods used to give residues+2 against residues+1."""
        peptidoform = stacked_nterm()
        assert len(peptidoform.properties["n_term"]) == 2
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(scorer.convert_peptidoform(peptidoform))

    def test_the_nterm_group_counts_once(self, settings):
        """Three stacked mods are still one scored position, not three."""
        peptidoform = stacked_nterm()
        n_term = list(peptidoform.properties["n_term"])
        peptidoform.properties["n_term"] = n_term + [copy.deepcopy(n_term[0])]
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(peptidoform) + 1

    def test_unmodified_terminus_adds_nothing(self, settings):
        peptidoform = Peptidoform(UNMODIFIED)
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(peptidoform)

    def test_empty_nterm_list_adds_nothing(self, settings):
        """An empty list is not None; the tokenizer treats it as no N-terminal token."""
        peptidoform = Peptidoform(SINGLE_MOD)
        peptidoform.properties["n_term"] = []
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(peptidoform)


class TestFormatScores:
    """The tool-supplied path: surplus leading scores collapse onto the N-terminal group."""

    def test_surplus_score_is_collapsed_to_the_mean(self, settings):
        peptidoform = stacked_nterm()
        expected = settings.get_length_peptidoform_with_nterm(peptidoform)
        supplied = [0.2, 0.4] + [0.9] * len(peptidoform)  # one score per stacked mod
        out = settings.format_scores(supplied, peptidoform)
        assert len(out) == expected
        assert out[0] == pytest.approx(np.mean([0.2, 0.4]))
        assert out[1:] == [0.9] * len(peptidoform)

    def test_correct_length_is_left_alone(self, settings):
        peptidoform = Peptidoform(SINGLE_MOD)
        supplied = [0.3] + [0.9] * len(peptidoform)
        assert settings.format_scores(supplied, peptidoform) == supplied

    def test_unmodified_peptide_is_left_alone(self, settings):
        peptidoform = Peptidoform(UNMODIFIED)
        supplied = [0.9] * len(peptidoform)
        assert settings.format_scores(supplied, peptidoform) == supplied

    def test_string_input_is_parsed(self, settings):
        peptidoform = Peptidoform(UNMODIFIED)
        supplied = [0.9] * len(peptidoform)
        assert settings.format_scores(str(supplied), peptidoform) == supplied

    @pytest.mark.parametrize("proforma", COMPOSITE_SPELLINGS)
    def test_composite_spelling_does_not_raise(self, settings, proforma):
        """The old branch keyed on n_term[0].value == "H-2C1O1" and raised TypeError:
        list() on a NumPy scalar. Reaching that code must now be safe."""
        peptidoform = Peptidoform(proforma)
        supplied = [0.2, 0.4] + [0.9] * len(peptidoform)
        out = settings.format_scores(supplied, peptidoform)
        assert len(out) == settings.get_length_peptidoform_with_nterm(peptidoform)

    def test_shorter_than_expected_is_not_padded(self, settings):
        """Too FEW scores is a different fault and must not be silently patched over."""
        peptidoform = Peptidoform(SINGLE_MOD)
        supplied = [0.9] * (len(peptidoform) - 2)
        assert settings.format_scores(supplied, peptidoform) == supplied


class TestCollapseAaScoresEndToEnd:
    """The consumer that used to blow up: flattening scores against per-token match arrays."""

    def _frame(self, settings, scorer, peptidoform, supplied_scores):
        import pandas as pd

        ground_truth = Peptidoform(UNMODIFIED)
        match = scorer.evaluate_match(ground_truth, peptidoform)
        return pd.DataFrame(
            {
                "peptidoform": [peptidoform],
                "aa_scores": [settings.format_scores(supplied_scores, peptidoform)],
                "aa_matches_dn": [match["aa_matches_dn"]],
                "aa_exact_dn": [match["aa_exact_dn"]],
            }
        )

    def test_broadcast_path_flattens(self, settings, scorer):
        """Scores broadcast from the peptide score, as for a tool with no per-residue scores."""
        peptidoform = stacked_nterm()
        n = settings.get_length_peptidoform_with_nterm(peptidoform)
        frame = self._frame(settings, scorer, peptidoform, [0.75] * n)
        for evaluation in ("mass", "exact"):
            out = collapse_aa_scores(frame, evaluation_type=evaluation)
            assert len(out) == len(frame["aa_matches_dn"].iloc[0])

    def test_tool_supplied_path_flattens(self, settings, scorer):
        """One score per stacked N-terminal modification, as a tool may report."""
        peptidoform = stacked_nterm()
        supplied = [0.2, 0.4] + [0.9] * len(peptidoform)
        frame = self._frame(settings, scorer, peptidoform, supplied)
        out = collapse_aa_scores(frame, evaluation_type="mass")
        assert len(out) == len(frame["aa_matches_dn"].iloc[0])
