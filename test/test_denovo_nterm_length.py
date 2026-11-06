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
from proteobench.io.parsing.parse_settings import (
    ParseSettingsDeNovo,
    parse_peptidoform_or_none,
    split_nterm_tags,
)
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

    @pytest.mark.parametrize("as_text", [False, True], ids=["list", "comma_separated_string"])
    def test_surplus_is_collapsed_whatever_the_container(self, settings, as_text):
        """The native form matters: every mzTab/TSV tool stores its scores as a comma-separated
        string, and `eval("0.2,0.4,0.9")` is a tuple, not a list. Guarding on `list` alone left
        this branch dead for Casanovo, AdaNovo, ContraNovo, DeepNovo and PointNovo -- the very
        tools that can emit one score per N-terminal modification."""
        peptidoform = stacked_nterm()
        supplied = [0.2, 0.4] + [0.9] * len(peptidoform)
        payload = ",".join(str(x) for x in supplied) if as_text else supplied
        out = settings.format_scores(payload, peptidoform)
        assert len(out) == settings.get_length_peptidoform_with_nterm(peptidoform)
        assert out[0] == pytest.approx(np.mean([0.2, 0.4]))
        assert list(out[1:]) == [0.9] * len(peptidoform)

    def test_tuple_input_is_collapsed(self, settings):
        """A tuple reaches `format_scores` directly whenever a loader has already parsed the
        score string, so it must take the same path as a list."""
        peptidoform = stacked_nterm()
        supplied = (0.2, 0.4) + (0.9,) * len(peptidoform)
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


class TestBlankPredictionIsNotAPeptidoform:
    """A spectrum the tool declined to call must not become a zero-length peptidoform."""

    @pytest.mark.parametrize("blank", ["", "   ", None, float("nan"), np.nan])
    def test_blank_prediction_yields_none(self, blank):
        """`Peptidoform("")` parses, so an empty prediction used to survive every
        `dropna(subset="peptidoform")` carrying a NaN `aa_scores` and kill `collapse_aa_scores`
        with "'float' object is not iterable"."""
        assert parse_peptidoform_or_none(blank) is None

    def test_unparsable_sequence_yields_none(self):
        assert parse_peptidoform_or_none("C(+57.02)PEPTIDE") is None

    @pytest.mark.parametrize("proforma", [UNMODIFIED, SINGLE_MOD, *COMPOSITE_SPELLINGS])
    def test_real_predictions_still_parse(self, proforma):
        assert parse_peptidoform_or_none(proforma) == Peptidoform(proforma)

    def test_blank_rows_cannot_reach_collapse(self, settings, scorer):
        """The end-to-end shape: a frame built from a blank prediction is empty after the
        `dropna` that `get_metrics` applies, so `collapse_aa_scores` never sees it."""
        import pandas as pd

        frame = pd.DataFrame({"peptidoform": [parse_peptidoform_or_none("")], "aa_scores": [np.nan]})
        assert len(frame.dropna(subset="peptidoform")) == 0


class TestStackedNtermTagsSurviveParsing:
    """Both N-terminal tags must reach the peptidoform, in either spelling.

    pyteomics 4.7.5 keeps only the LAST tag of "[A]-[B]-SEQ" and rejects "[A][B]-SEQ"
    outright, so a prediction carrying carbamylation stacked with ammonia loss used to lose
    one of the two silently. The score LENGTH came out right either way -- which is what made
    the loss invisible -- but the surviving N-terminal group had the wrong mass.
    """

    STACKED = [
        "[UNIMOD:5]-[UNIMOD:385]-ALHTDSVSLINITPR",  # produced by a sequence_mapper, token by token
        "[UNIMOD:5][UNIMOD:385]-ALHTDSVSLINITPR",  # the canonical ProForma spelling
    ]
    # Carbamyl (+43.005814) stacked with ammonia loss (-17.026549).
    STACKED_MASS = 25.979265

    @pytest.mark.parametrize(
        "proforma, expected",
        [
            ("ALHTDSVSLINITPR", ([], "ALHTDSVSLINITPR")),
            ("[UNIMOD:1]-ALHTDSVSLINITPR", (["UNIMOD:1"], "ALHTDSVSLINITPR")),
            ("[A]-[B]-PEPTIDE", (["A", "B"], "PEPTIDE")),
            ("[A][B]-PEPTIDE", (["A", "B"], "PEPTIDE")),
            ("PEP[UNIMOD:4]TIDE", ([], "PEP[UNIMOD:4]TIDE")),
            ("[A]", ([], "[A]")),  # unterminated: not an N-terminal run, left for the parser to reject
        ],
    )
    def test_split_nterm_tags(self, proforma, expected):
        assert split_nterm_tags(proforma) == expected

    @pytest.mark.parametrize("proforma", STACKED)
    def test_both_modifications_are_kept(self, proforma):
        peptidoform = parse_peptidoform_or_none(proforma)
        assert peptidoform is not None
        n_term = peptidoform.properties["n_term"]
        assert len(n_term) == 2
        assert sum(mod.mass for mod in n_term) == pytest.approx(self.STACKED_MASS, abs=1e-4)

    @pytest.mark.parametrize("proforma", STACKED)
    def test_stacking_does_not_change_any_length(self, settings, scorer, proforma):
        """The terminus is one scored position however many modifications sit on it, so the
        extra tag must change the mass and the token string but no length."""
        peptidoform = parse_peptidoform_or_none(proforma)
        single = Peptidoform(SINGLE_MOD)
        assert len(peptidoform) == len(single)
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(scorer.convert_peptidoform(peptidoform))
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(peptidoform) + 1

    def test_tag_order_is_preserved(self):
        """Order matters for the token string, so the tags must not be reversed or sorted."""
        peptidoform = parse_peptidoform_or_none("[UNIMOD:385]-[UNIMOD:1]-LVPLHTHLWYDPK")
        assert [mod.id for mod in peptidoform.properties["n_term"]] == [385, 1]

    @pytest.mark.parametrize("proforma", STACKED)
    def test_tool_supplied_scores_collapse_end_to_end(self, settings, scorer, proforma):
        """The whole chain on a *parsed* peptidoform rather than a hand-built one: one score
        per stacked modification, in the comma-separated form a tool actually emits."""
        peptidoform = parse_peptidoform_or_none(proforma)
        needed = len(scorer.convert_peptidoform(peptidoform))
        supplied = [0.2, 0.4] + [0.9] * len(peptidoform)
        out = settings.format_scores(",".join(str(x) for x in supplied), peptidoform)
        assert len(out) == needed
        assert out[0] == pytest.approx(np.mean([0.2, 0.4]))

    @pytest.mark.parametrize(
        "tag", ["not a modification", "UNIMOD:99999999", "UNIMOD:abc", "Formula:ZZ9", "+notanumber"]
    )
    def test_an_unresolvable_tag_yields_none(self, tag):
        """ProForma happily accepts a free-text tag, and the mass lookup only fails later inside
        `get_token_mass`. "[A][B]-SEQ" used to be rejected by the parser outright, so reattaching
        tags must not become a way for junk to reach scoring and blow up mid-run."""
        assert parse_peptidoform_or_none(f"[{tag}][UNIMOD:1]-PEPTIDE") is None
        assert parse_peptidoform_or_none(f"[{tag}]-[UNIMOD:1]-PEPTIDE") is None

    def test_a_resolvable_name_tag_is_kept(self):
        """The check is on the mass resolving, not on the tag's spelling."""
        peptidoform = parse_peptidoform_or_none("[Acetyl][UNIMOD:1]-PEPTIDE")
        assert len(peptidoform.properties["n_term"]) == 2
