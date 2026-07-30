"""
Best-effort matching of sample/run names against a set of expected names.

Used to reconcile user-authored sample names (currently only PEAKS requires
users to type sample names manually before export) against the names declared
in a module's TOML ``condition_mapper``. Matching is opt-in per tool (see
``ParseSettingsQuant``) and only auto-applies a correction when it is
unambiguous, to avoid silently mis-assigning a sample to the wrong condition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Tuple

_TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9]+")


def _tokenize(name: str) -> List[str]:
    """Split a name into lower-cased alphanumeric tokens."""
    return [t for t in _TOKEN_SPLIT.split(name.lower()) if t]


@dataclass
class RunNameMatch:
    """A single confident, auto-applied name correction."""

    observed: str
    expected: str
    score: float


@dataclass
class RunNameMatchResult:
    """
    Outcome of matching a set of observed names against a set of expected names.

    Attributes
    ----------
    matches : list of RunNameMatch
        Confident, unambiguous corrections to auto-apply.
    unmatched_expected : list of str
        Expected names that could not be confidently resolved.
    unmatched_observed : list of str
        Observed names left over after matching.
    near_misses : dict
        For each unmatched expected name, up to 3 closest observed candidates
        (with their score), included even below the auto-apply threshold, for
        building an actionable error message.
    """

    matches: List[RunNameMatch] = field(default_factory=list)
    unmatched_expected: List[str] = field(default_factory=list)
    unmatched_observed: List[str] = field(default_factory=list)
    near_misses: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)


def match_run_names(
    observed: Iterable[str],
    expected: Iterable[str],
    cutoff: float = 0.6,
    margin: float = 0.1,
) -> RunNameMatchResult:
    """
    Match observed names against expected names, auto-accepting only confident pairs.

    Names are compared token-wise (split on non-alphanumeric runs, lower-cased)
    rather than as raw strings: names that share a long common template (e.g.
    ``Condition_A_Sample_Alpha_01`` vs. ``_02``) can differ by a single token
    yet still score above 0.9 on raw character similarity for the *wrong* pair,
    which is not a safe margin. Token-wise scoring concentrates the difference
    into whole tokens, giving a much clearer separation between the correct
    match and the next-best candidate.

    A pair is only auto-matched when its score is at least ``cutoff`` **and**
    beats the runner-up score for both its row and its column by at least
    ``margin`` (computed from the full pairwise matrix) — i.e. it must be an
    unambiguous best match on both sides, not just the best available.

    Parameters
    ----------
    observed : iterable of str
        Names actually found (e.g. uploaded column headers) that did not
        already exact-match an expected name.
    expected : iterable of str
        Expected names (e.g. TOML ``condition_mapper`` keys) not already
        satisfied by an exact match.
    cutoff : float, optional
        Minimum token-similarity score to consider a pair at all (default 0.6).
    margin : float, optional
        Minimum lead over the runner-up score required to accept a pair as
        unambiguous (default 0.1).

    Returns
    -------
    RunNameMatchResult
        The confident matches plus diagnostics for anything left unresolved.
    """
    observed = list(observed)
    expected = list(expected)
    result = RunNameMatchResult()

    if not observed or not expected:
        result.unmatched_expected = list(expected)
        result.unmatched_observed = list(observed)
        for exp in expected:
            result.near_misses[exp] = []
        return result

    tokens_observed = {o: _tokenize(o) for o in observed}
    tokens_expected = {e: _tokenize(e) for e in expected}

    scores = {
        (o, e): SequenceMatcher(None, tokens_observed[o], tokens_expected[e]).ratio()
        for o in observed
        for e in expected
    }

    matched_observed = set()
    matched_expected = set()
    for (o, e), score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
        if o in matched_observed or e in matched_expected:
            continue
        if score < cutoff:
            continue
        epsilon = 1e-9
        row_runner_up = max((scores[(o, e2)] for e2 in expected if e2 != e), default=0.0)
        col_runner_up = max((scores[(o2, e)] for o2 in observed if o2 != o), default=0.0)
        if score - row_runner_up < margin - epsilon or score - col_runner_up < margin - epsilon:
            continue
        result.matches.append(RunNameMatch(observed=o, expected=e, score=score))
        matched_observed.add(o)
        matched_expected.add(e)

    result.unmatched_expected = [e for e in expected if e not in matched_expected]
    result.unmatched_observed = [o for o in observed if o not in matched_observed]

    for exp in result.unmatched_expected:
        candidates = sorted(
            ((o, scores[(o, exp)]) for o in observed if o not in matched_observed),
            key=lambda pair: pair[1],
            reverse=True,
        )
        result.near_misses[exp] = candidates[:3]

    return result
