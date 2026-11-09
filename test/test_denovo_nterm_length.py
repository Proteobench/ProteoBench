"""Length agreement between the de novo tokenizer and the score-length helpers.

`DenovoScores.convert_peptidoform` scores the N-terminal group as ONE token however many
modifications are stacked on it. `get_length_peptidoform_with_nterm` (which sizes the broadcast
for tools without per-residue scores) and `format_scores` (which reconciles the length for tools
with them) must both agree, or `collapse_aa_scores` raises "All arrays must be of the same
length". These tests pin that invariant for every N-terminal spelling.
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
# composition is H-2C1O1. Every spelling below is the same chemistry and must score the same
# in length.
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
    """A peptidoform with two N-terminal modifications, built by extending `n_term` rather than
    by parsing a stacked string, whose handling depends on the pyteomics version."""
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
        """Every mzTab/TSV tool stores its scores as a comma-separated string, which evals to a
        tuple, not a list. Guarding on `list` alone left this branch dead for those tools."""
        peptidoform = stacked_nterm()
        supplied = [0.2, 0.4] + [0.9] * len(peptidoform)
        payload = ",".join(str(x) for x in supplied) if as_text else supplied
        out = settings.format_scores(payload, peptidoform)
        assert len(out) == settings.get_length_peptidoform_with_nterm(peptidoform)
        assert out[0] == pytest.approx(np.mean([0.2, 0.4]))
        assert list(out[1:]) == [0.9] * len(peptidoform)

    def test_tuple_input_is_collapsed(self, settings):
        """A tuple reaches `format_scores` whenever a loader already parsed the score string."""
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
        """`Peptidoform("")` parses as length 0, so an empty prediction used to survive every
        `dropna(subset="peptidoform")` with NaN scores and kill `collapse_aa_scores`."""
        assert parse_peptidoform_or_none(blank) is None

    def test_unparsable_sequence_yields_none(self):
        assert parse_peptidoform_or_none("C(+57.02)PEPTIDE") is None

    @pytest.mark.parametrize("proforma", [UNMODIFIED, SINGLE_MOD, *COMPOSITE_SPELLINGS])
    def test_real_predictions_still_parse(self, proforma):
        assert parse_peptidoform_or_none(proforma) == Peptidoform(proforma)

    def test_blank_rows_cannot_reach_collapse(self, settings, scorer):
        """A frame built from a blank prediction is empty after the `dropna` `get_metrics`
        applies, so `collapse_aa_scores` never sees it."""
        import pandas as pd

        frame = pd.DataFrame({"peptidoform": [parse_peptidoform_or_none("")], "aa_scores": [np.nan]})
        assert len(frame.dropna(subset="peptidoform")) == 0


class TestStackedNtermTagsSurviveParsing:
    """Both N-terminal tags must reach the peptidoform, in either spelling.

    pyteomics 4.7.5 keeps only the LAST tag of "[A]-[B]-SEQ" and rejects "[A][B]-SEQ", so
    stacked chemistry silently lost a modification. The score length came out right either way,
    which is what hid it; the surviving terminus had the wrong mass.
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
            # Dash-less: InstaNovo writes this in its per-beam columns. Unambiguously
            # N-terminal -- a bracket before the first residue cannot be anything else.
            ("[UNIMOD:1]GATVHGHSVR", (["UNIMOD:1"], "GATVHGHSVR")),
            ("[A][B]PEPTIDE", (["A", "B"], "PEPTIDE")),
            ("[A]-[B]PEPTIDE", (["A", "B"], "PEPTIDE")),
            ("PEP[UNIMOD:4]TIDE", ([], "PEP[UNIMOD:4]TIDE")),
            ("[A]", ([], "[A]")),  # unterminated: not an N-terminal run, left for the parser to reject
        ],
    )
    def test_split_nterm_tags(self, proforma, expected):
        assert split_nterm_tags(proforma) == expected

    @pytest.mark.parametrize(
        "proforma",
        ["[UNIMOD:1]GATVHGHSVR", "[UNIMOD:1]-GATVHGHSVR"],
        ids=["dash_less", "canonical"],
    )
    def test_dash_less_spelling_matches_the_canonical_one(self, settings, scorer, proforma):
        """pyteomics rejects "[MOD]SEQ", so it is rebuilt canonically; both spellings must then
        give the same terminus, mass and token count."""
        peptidoform = parse_peptidoform_or_none(proforma)
        assert peptidoform is not None
        assert len(peptidoform.properties["n_term"]) == 1
        assert peptidoform.properties["n_term"][0].mass == pytest.approx(42.0106, abs=1e-4)
        assert len(peptidoform) == 10
        assert settings.get_length_peptidoform_with_nterm(peptidoform) == len(scorer.convert_peptidoform(peptidoform))

    def test_tags_without_residues_yield_none(self):
        assert parse_peptidoform_or_none("[UNIMOD:1]-") is None

    @pytest.mark.parametrize("proforma", STACKED)
    def test_both_modifications_are_kept(self, proforma):
        peptidoform = parse_peptidoform_or_none(proforma)
        assert peptidoform is not None
        n_term = peptidoform.properties["n_term"]
        assert len(n_term) == 2
        assert sum(mod.mass for mod in n_term) == pytest.approx(self.STACKED_MASS, abs=1e-4)

    @pytest.mark.parametrize("proforma", STACKED)
    def test_stacking_does_not_change_any_length(self, settings, scorer, proforma):
        """The terminus is one scored position however many modifications sit on it."""
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
        """The whole chain on a parsed peptidoform rather than a hand-built one, with the scores
        in the comma-separated form a tool actually emits."""
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


class TestEveryModificationMassResolves:
    """An unresolvable tag must drop the row here, not crash later in `get_token_mass`.

    ProForma allows name-based tags, so "[Acetyl]" (valid) and "[not a modification]" (junk)
    both parse; pyteomics resolves the mass only when asked.
    """

    @pytest.mark.parametrize(
        "proforma",
        [
            "PEPC[UNIMOD:99999999]TIDE",
            "PEPC[not a modification]TIDE",
            "PEP[Formula:ZZ9]TIDE",
            "[UNIMOD:99999999]-PEPTIDE",
            "[not a modification]-PEPTIDE",
            "[UNIMOD:99999999][UNIMOD:5]-PEPTIDE",
        ],
    )
    def test_unresolvable_mass_yields_none(self, proforma):
        assert parse_peptidoform_or_none(proforma) is None

    @pytest.mark.parametrize(
        "proforma",
        [
            "PEPTIDE",
            "PEPC[UNIMOD:4]TIDE",
            "[UNIMOD:1]-PEPTIDE",
            "[Acetyl]-PEPTIDE",  # a name tag is legal ProForma and does resolve
            "[UNIMOD:5][UNIMOD:385]-PEPTIDE",
        ],
    )
    def test_resolvable_peptidoforms_are_kept(self, proforma):
        assert parse_peptidoform_or_none(proforma) is not None

    def test_every_scored_position_can_be_massed(self, scorer):
        """The guarantee the check buys: `get_token_mass` succeeds for every token."""
        peptidoform = parse_peptidoform_or_none("[UNIMOD:5][UNIMOD:385]-PEPC[UNIMOD:4]TIDEM[UNIMOD:35]K")
        for token in scorer.convert_peptidoform(peptidoform):
            assert isinstance(scorer.get_token_mass(token), float)


class TestUnscorableRowsAreDropped:
    """The last gate before scoring: one bad row must not abort the whole run.

    These exercise the drop mechanics on deliberately tiny frames, so the wholesale-misalignment
    threshold is lifted; `TestWholesaleMisalignmentIsRefused` covers the threshold itself.
    """

    @pytest.fixture(autouse=True)
    def _allow_any_fraction(self, settings):
        settings.max_unscorable_fraction = 1.0

    def _frame(self, rows):
        import pandas as pd

        return pd.DataFrame({"peptidoform": [p for p, _ in rows], "aa_scores": [sc for _, sc in rows]})

    def test_mismatched_rows_are_dropped_and_good_ones_kept(self, settings):
        good = Peptidoform(SINGLE_MOD)  # residues + 1 scored positions
        n = settings.get_length_peptidoform_with_nterm(good)
        frame = self._frame(
            [
                (good, [0.9] * n),  # correct
                (good, [0.9] * (n - 2)),  # too few: a genuine fault
                (good, [0.9] * (n + 3)),  # surplus stacking cannot explain
                (Peptidoform(UNMODIFIED), [0.9] * len(Peptidoform(UNMODIFIED))),  # correct
            ]
        )
        out = settings.drop_unscorable_rows(frame)
        assert len(out) == 2
        assert list(out.index) == [0, 3]

    def test_a_clean_frame_is_untouched(self, settings):
        peptidoform = Peptidoform(SINGLE_MOD)
        n = settings.get_length_peptidoform_with_nterm(peptidoform)
        frame = self._frame([(peptidoform, [0.9] * n)] * 3)
        assert len(settings.drop_unscorable_rows(frame)) == 3

    def test_unsized_scores_are_dropped(self, settings):
        """A NaN `aa_scores` has no length at all and would raise on `chain(*)`."""
        frame = self._frame([(Peptidoform(UNMODIFIED), np.nan)])
        assert len(settings.drop_unscorable_rows(frame)) == 0

    def test_the_drop_is_reported(self, settings, caplog):
        """Dropping data silently would be its own bug; the count must reach the log."""
        peptidoform = Peptidoform(SINGLE_MOD)
        frame = self._frame([(peptidoform, [0.9] * 3)])
        with caplog.at_level("WARNING"):
            settings.drop_unscorable_rows(frame)
        assert "could not be lined up with the peptidoform tokens for 1 of 1 PSMs" in caplog.text
        assert "Those PSMs were dropped" in caplog.text

    def test_collapse_survives_what_used_to_raise(self, settings, scorer):
        """End to end: a frame holding one bad row still flattens."""
        import pandas as pd

        good = Peptidoform(SINGLE_MOD)
        n = settings.get_length_peptidoform_with_nterm(good)
        frame = self._frame([(good, [0.9] * n), (good, [0.9] * (n - 2))])
        kept = settings.drop_unscorable_rows(frame)
        matches = [scorer.evaluate_match(Peptidoform(UNMODIFIED), p) for p in kept["peptidoform"]]
        kept = kept.assign(
            aa_matches_dn=[m["aa_matches_dn"] for m in matches],
            aa_exact_dn=[m["aa_exact_dn"] for m in matches],
        )
        assert len(collapse_aa_scores(kept, evaluation_type="mass")) == n


class TestMissingPerResidueScoresFallBackToThePeptideScore:
    """A present-but-empty score column must behave like an absent one.

    InstaNovo's diffusion and refinement paths emit `token_log_probs` as an empty field on
    every row, so testing only for the column's presence left those PSMs with a NaN that no
    later step can use -- 779,879 of 779,879 rows dropped.
    """

    def _frame(self, scores, peptide_scores=None):
        import pandas as pd

        peptidoform = Peptidoform(SINGLE_MOD)
        return pd.DataFrame(
            {
                "peptidoform": [peptidoform] * len(scores),
                "score": peptide_scores if peptide_scores is not None else [-0.5] * len(scores),
                "aa_scores": scores,
            }
        )

    @pytest.mark.parametrize(
        "scores",
        [
            [np.nan, np.nan],  # all missing: the column arrives as a float dtype
            [np.nan, ""],  # a blank string counts as missing too
            [np.nan, [0.1] * 16],  # only some rows missing
        ],
        ids=["all_missing", "blank_string", "partially_missing"],
    )
    def test_missing_scores_are_filled_whatever_the_column_dtype(self, settings, scores):
        """A column of only missing values gets a float (or str) dtype that cannot hold lists,
        so the fill has to cast to object first or pandas 3 refuses the assignment."""
        frame = self._frame(scores)
        n = settings.get_length_peptidoform_with_nterm(Peptidoform(SINGLE_MOD))
        filled = settings.fill_missing_aa_scores(frame)
        assert all(len(row) == n for row in filled["aa_scores"])
        assert list(filled["aa_scores"].iloc[0]) == [-0.5] * n
        assert len(settings.drop_unscorable_rows(filled)) == len(scores)

    def test_supplied_scores_are_left_alone(self, settings):
        n = settings.get_length_peptidoform_with_nterm(Peptidoform(SINGLE_MOD))
        filled = settings.fill_missing_aa_scores(self._frame([[0.1] * n]))
        assert list(filled["aa_scores"].iloc[0]) == [0.1] * n

    def test_an_absent_column_is_filled_too(self, settings):
        frame = self._frame([np.nan]).drop(columns="aa_scores")
        n = settings.get_length_peptidoform_with_nterm(Peptidoform(SINGLE_MOD))
        assert len(settings.fill_missing_aa_scores(frame)["aa_scores"].iloc[0]) == n

    def test_a_missing_peptide_score_broadcasts_nothing(self, settings):
        """A list of NaN would have the right length and the wrong meaning, and would sail
        through the length gate into the precision-coverage curve."""
        frame = self._frame([np.nan], peptide_scores=[np.nan])
        assert settings.broadcast_peptide_score(frame).iloc[0] is None


class TestWholesaleMisalignmentIsRefused:
    """Dropping rows is only safe while it stays rare."""

    def _frame(self, n_rows, n_scores):
        import pandas as pd

        peptidoform = Peptidoform(SINGLE_MOD)
        return pd.DataFrame({"peptidoform": [peptidoform] * n_rows, "aa_scores": [[0.9] * n_scores] * n_rows})

    def test_a_few_bad_rows_are_dropped(self, settings):
        peptidoform = Peptidoform(SINGLE_MOD)
        n = settings.get_length_peptidoform_with_nterm(peptidoform)
        frame = self._frame(200, n)
        frame.loc[0, "aa_scores"] = [0.9] * (n - 3)
        assert len(settings.drop_unscorable_rows(frame)) == 199

    def test_wholesale_misalignment_raises(self, settings):
        frame = self._frame(200, 4)
        with pytest.raises(ValueError, match="could not be lined up with the peptidoform tokens"):
            settings.drop_unscorable_rows(frame)

    def test_the_refusal_explains_itself(self, settings, caplog):
        """The submitter has to be told what is wrong, not just that scoring stopped."""
        frame = self._frame(200, 4)
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                settings.drop_unscorable_rows(frame)
        assert "do not correspond at all" in caplog.text
        assert "one score per residue" in caplog.text

    def test_the_threshold_is_tunable(self, settings):
        """Exposed so a module can relax it without editing the check."""
        peptidoform = Peptidoform(SINGLE_MOD)
        n = settings.get_length_peptidoform_with_nterm(peptidoform)
        frame = self._frame(10, n)
        frame.loc[0, "aa_scores"] = [0.9] * (n - 3)  # 10% unscorable
        with pytest.raises(ValueError):
            settings.drop_unscorable_rows(frame)
        settings.max_unscorable_fraction = 0.5
        assert len(settings.drop_unscorable_rows(frame)) == 9
