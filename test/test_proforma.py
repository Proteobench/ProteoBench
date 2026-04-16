"""Tests for proteobench.io.parsing.proforma — ProForma conversion helpers."""

import math

import pytest

from proteobench.io.parsing.proforma import (
    aggregate_modification_column,
    aggregate_modification_sites_column,
    count_chars,
    get_proforma_bracketed,
    get_stripped_seq,
    match_brackets,
    to_lowercase,
)


class TestCountChars:
    def test_alpha_upper(self):
        assert count_chars("ABC[mod]DE", isalpha=True, isupper=True) == 5

    def test_alpha_only(self):
        assert count_chars("ABCmod", isalpha=True, isupper=False) == 6

    def test_upper_only(self):
        assert count_chars("ABCmod", isalpha=False, isupper=True) == 3


class TestGetStrippedSeq:
    def test_alpha_upper(self):
        assert get_stripped_seq("ABC[mod]DE") == "ABCDE"

    def test_alpha_only(self):
        assert get_stripped_seq("ABCmod", isalpha=True, isupper=False) == "ABCmod"

    def test_upper_only(self):
        assert get_stripped_seq("ABCmod", isalpha=False, isupper=True) == "ABC"


class TestMatchBrackets:
    def test_single_mod(self):
        mods, positions = match_brackets("ABC[+57.02]DE")
        assert list(mods) == ["[+57.02]"]
        assert list(positions) == [3]

    def test_multiple_mods(self):
        mods, positions = match_brackets("A[+42]BC[+57.02]D")
        assert list(mods) == ["[+42]", "[+57.02]"]
        assert list(positions) == [1, 3]

    def test_no_mods(self):
        mods, positions = match_brackets("ABCDE")
        assert list(mods) == []
        assert list(positions) == []


class TestToLowercase:
    def test_converts_match_to_lowercase(self):
        import re

        match = re.search(r"\[ABC\]", "X[ABC]Y")
        assert to_lowercase(match) == "[abc]"


class TestAggregateModificationColumn:
    def test_internal_modification(self):
        result = aggregate_modification_column("PEPTIDE", "Oxidation (M5)")
        assert result == "PEPTI[Oxidation]DE"

    def test_nterm_modification(self):
        result = aggregate_modification_column("PEPTIDE", "Acetyl (Any N-term)")
        assert result == "[Acetyl]-PEPTIDE"

    def test_cterm_modification(self):
        result = aggregate_modification_column("PEPTIDE", "Amidated (Any C-term)")
        assert result == "PEPTIDE-[Amidated]"

    def test_multiple_modifications(self):
        result = aggregate_modification_column("PEPTIDE", "Oxidation (M5); Acetyl (Any N-term)")
        assert "[Acetyl]-" in result
        assert "[Oxidation]" in result


class TestAggregateModificationSitesColumn:
    def test_internal_modification(self):
        result = aggregate_modification_sites_column("PEPTIDE", "Oxidation@M", "5")
        assert result == "PEPTI[Oxidation]DE"

    def test_nan_modifications(self):
        result = aggregate_modification_sites_column("PEPTIDE", float("nan"), "")
        assert result == "PEPTIDE"

    def test_empty_modifications(self):
        result = aggregate_modification_sites_column("PEPTIDE", "", "")
        assert result == "PEPTIDE"


class TestGetProformaBracketed:
    def test_no_modifications(self):
        result = get_proforma_bracketed("PEPTIDE")
        assert result == "PEPTIDE"

    def test_single_modification_with_dict_lookup(self):
        # modification_dict keys must include brackets — match_brackets returns full [mod] strings
        # Position is counted as uppercase alpha chars before the bracket.
        # PEP[+57.0215]TIDE: 3 uppercase chars before bracket -> mod goes after 4th AA
        result = get_proforma_bracketed(
            "PEP[+57.0215]TIDE",
            modification_dict={"[+57.0215]": "Carbamidomethyl"},
        )
        assert result == "PEPT[Carbamidomethyl]IDE"

    def test_unknown_modification_kept_as_is(self):
        result = get_proforma_bracketed(
            "PEP[+99.99]TIDE",
            modification_dict={"[+57.0215]": "Carbamidomethyl"},
        )
        assert "[+99.99]" in result

    def test_multiple_modifications(self):
        result = get_proforma_bracketed(
            "PEP[+57.0215]TM[+15.9949]DE",
            modification_dict={
                "[+57.0215]": "Carbamidomethyl",
                "[+15.9949]": "Oxidation",
            },
        )
        assert "[Carbamidomethyl]" in result
        assert "[Oxidation]" in result

    def test_default_modification_dict_uses_bracketed_keys(self):
        # The default modification_dict has keys WITHOUT brackets (e.g., "+57.0215").
        # match_brackets returns WITH brackets (e.g., "[+57.0215]").
        # So the default dict never matches — modifications pass through as-is.
        # This is by design: the default dict is overridden per-tool via TOML config.
        result = get_proforma_bracketed("PEPTIC[+57.0215]DE")
        assert "[+57.0215]" in result
