import pytest

from proteobench.io.parsing.run_name_matching import match_run_names

EXPECTED_DIAPASEF = [
    "LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_01 Normalized Area",
    "LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_02 Normalized Area",
    "LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_03 Normalized Area",
    "LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_01 Normalized Area",
    "LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_02 Normalized Area",
    "LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_03 Normalized Area",
]

OBSERVED_DIAPASEF_TYPO = [name.replace("_ttSCP_", "_timstofSCP_") for name in EXPECTED_DIAPASEF]


class TestMatchRunNames:
    def test_identical_names_resolve_with_perfect_score(self):
        # match_run_names() itself is a generic matcher; callers (e.g.
        # ParseSettingsQuant._resolve_run_names) are responsible for excluding
        # already-exact matches from the pools before calling it.
        result = match_run_names(EXPECTED_DIAPASEF, EXPECTED_DIAPASEF)
        assert result.unmatched_expected == []
        assert result.unmatched_observed == []
        assert all(m.score == 1.0 for m in result.matches)

    def test_real_world_typo_resolves_all_pairs_correctly(self):
        result = match_run_names(OBSERVED_DIAPASEF_TYPO, EXPECTED_DIAPASEF)
        assert result.unmatched_expected == []
        assert result.unmatched_observed == []
        assert len(result.matches) == 6
        matched = {m.observed: m.expected for m in result.matches}
        for observed, expected in zip(OBSERVED_DIAPASEF_TYPO, EXPECTED_DIAPASEF):
            assert matched[observed] == expected

    def test_ambiguous_candidates_are_not_auto_matched(self):
        # Two observed names equidistant from a single expected name: neither
        # should be silently picked.
        expected = ["Condition_A_Sample_01"]
        observed = ["Condition_A_Sample_0X", "Condition_A_Sample_0Y"]
        result = match_run_names(observed, expected)
        assert result.matches == []
        assert result.unmatched_expected == expected

    def test_unrelated_name_is_not_matched(self):
        result = match_run_names(["sample_X99_rep7.raw"], EXPECTED_DIAPASEF[:1])
        assert result.matches == []
        assert result.unmatched_expected == EXPECTED_DIAPASEF[:1]
        assert result.unmatched_observed == ["sample_X99_rep7.raw"]

    def test_near_misses_reported_even_below_cutoff(self):
        result = match_run_names(["sample_X99_rep7.raw"], EXPECTED_DIAPASEF[:1])
        near = result.near_misses[EXPECTED_DIAPASEF[0]]
        assert near
        assert near[0][0] == "sample_X99_rep7.raw"

    def test_empty_pools(self):
        result = match_run_names([], ["expected_name"])
        assert result.unmatched_expected == ["expected_name"]
        assert result.matches == []
