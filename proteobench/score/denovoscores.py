"""
Module containing the DenovoScores class.
"""

from typing import List, Tuple, Optional

import os
import numpy as np
import pandas as pd
from psm_utils import Peptidoform

import requests
from bs4 import BeautifulSoup
import gzip
from pathlib import Path
from proteobench.score.score_base import ScoreBase

PEPTIDE_SETS_URL = "https://proteobench.cubimed.rub.de/datasets/module_data/de_novo_peptide_sets"
PEPTIDE_SETS_DIR_SERVER = "/mnt/data/proteobench/module_data/"
PEPTIDE_SETS_DIR_LOCAL_DENOVO = os.path.join(
    Path(__file__).resolve().parent, "io_parse_settings", "denovo", "DDA", "HCD", "peptide_sets"
)

# Ambiguity toggle combinations for exact-mode matching. Keys double as the column-name
# suffix used in the intermediate dataframe ("" = baseline, unsuffixed columns).
AMBIGUITY_COMBOS = {
    "": {"allow_il": False, "allow_deamidation": False},
    "_il": {"allow_il": True, "allow_deamidation": False},
    "_deam": {"allow_il": False, "allow_deamidation": True},
    "_both": {"allow_il": True, "allow_deamidation": True},
}


def get_ambiguity_suffix(allow_il: bool, allow_deamidation: bool) -> str:
    """
    Return the intermediate-dataframe column suffix for a given ambiguity toggle state.

    Parameters
    ----------
    allow_il : bool
        Whether I/L are treated as equivalent in exact-mode matching.
    allow_deamidation : bool
        Whether deamidated Q/N are treated as equivalent to E/D in exact-mode matching.

    Returns
    -------
    str
        The matching key in `AMBIGUITY_COMBOS` ("", "_il", "_deam", or "_both").
    """
    for suffix, flags in AMBIGUITY_COMBOS.items():
        if flags["allow_il"] == allow_il and flags["allow_deamidation"] == allow_deamidation:
            return suffix
    raise ValueError(f"No known ambiguity combination for allow_il={allow_il}, allow_deamidation={allow_deamidation}")


class DenovoScores(ScoreBase):
    """
    Class for computing de novo scores.

    Parameters
    ----------
    """

    def __init__(self):
        self.AA_MASSES = {
            "": 0.0,
            "G": 57.021463719204,
            "A": 71.037113783,
            "S": 87.03202840226,
            "P": 97.052763846796,
            "V": 99.068413910592,
            "T": 101.047678466056,
            "C": 103.00918495654,
            "L": 113.084063974388,
            "I": 113.084063974388,
            "N": 114.042927438408,
            "D": 115.02694302152,
            "Q": 128.058577502204,
            "K": 128.094963010536,
            "E": 129.04259308531599,
            "M": 131.040485084132,
            "H": 137.058911855296,
            "F": 147.068413910592,
            "R": 156.10111101903598,
            "Y": 163.06332852985201,
            "W": 186.07931294673998,
        }
        # UNIMOD accessions (as `.id`, an int) for the two deamidation modifications
        # tracked elsewhere in the module, mapped to the residue they're isobaric with.
        # Deamidated Q (+0.98402 Da) is isobaric with E; deamidated N is isobaric with D.
        self.DEAMIDATION_ISOBARS = {
            ("Q", 7): "E",
            ("N", 7): "D",
        }

    def generate_intermediate(self, filtered_df: pd.DataFrame, replicate_to_raw=None) -> pd.DataFrame:
        # TODO: Evaluate which PSMs match, and which don't and return new table

        # Tokenize each row's peptidoforms once, not once per ambiguity combination --
        # `convert_peptidoform` doesn't depend on the toggles, so re-running it 4x per row
        # (once per entry in AMBIGUITY_COMBOS below) was pure waste. Extracting the two
        # peptidoform columns to plain lists once also means the per-combo loop below runs
        # as plain Python, not `.apply(axis=1)` (which boxes every row into its own `Series`
        # just to pull two values back out of it).
        ground_truths = filtered_df["peptidoform_ground_truth"].tolist()
        de_novos = filtered_df["peptidoform"].tolist()
        gt_tokens_list = [self.convert_peptidoform(gt) for gt in ground_truths]
        dn_tokens_list = [self.convert_peptidoform(dn) for dn in de_novos]

        # Add match type label (exact, mass, mismatch) and the amino acid-level evaluations,
        # once per ambiguity toggle combination. `aa_matches_*`/`pep_match` are mass-based and
        # therefore identical across all combinations, so they're only stored for the baseline
        # ("") combination; `match_type`/`aa_exact_*` do depend on the toggles and are stored
        # per combination, suffixed accordingly (baseline keeps the original, unsuffixed names).
        for suffix, flags in AMBIGUITY_COMBOS.items():
            match_dicts = [
                self.evaluate_match_tokenized(gt, dn, gt_tokens, dn_tokens, **flags)
                for gt, dn, gt_tokens, dn_tokens in zip(ground_truths, de_novos, gt_tokens_list, dn_tokens_list)
            ]
            # One DataFrame construction instead of 3-6 separate `.apply(lambda x: x["key"])`
            # passes over the whole column to pull each field out of the dicts above.
            match_df = pd.DataFrame(match_dicts, index=filtered_df.index)
            filtered_df[f"match_type{suffix}"] = match_df["match_type"]
            filtered_df[f"aa_exact_gt{suffix}"] = match_df["aa_exact_gt"]
            filtered_df[f"aa_exact_dn{suffix}"] = match_df["aa_exact_dn"]
            if suffix == "":
                filtered_df["aa_matches_gt"] = match_df["aa_matches_gt"]
                filtered_df["aa_matches_dn"] = match_df["aa_matches_dn"]
                filtered_df["pep_match"] = match_df["pep_match"]

        species_sets = self.load_species_sets()
        filtered_df = self.add_fasta_category(df=filtered_df, species_sets=species_sets)

        return filtered_df

    def load_species_sets(self, path: Optional[str] = None) -> dict[str, set]:
        from proteobench.utils.server_io import download_file

        def _has_peptide_sets(directory: str) -> bool:
            """A directory counts as usable if it exists and already has at least one species file."""
            directory_path = Path(directory)
            return directory_path.is_dir() and any(directory_path.glob("*.txt.gz"))

        def _list_remote_peptide_set_files(url: str) -> list[str]:
            """Parse the server's directory listing for available peptide set filenames."""
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return [link["href"] for link in soup.find_all("a", href=True) if link["href"].endswith(".txt.gz")]

        def _download_peptide_sets(url: str, local_dir: str) -> None:
            """Download every peptide set file listed at the server URL into local_dir."""
            os.makedirs(local_dir, exist_ok=True)
            filenames = _list_remote_peptide_set_files(url)
            if not filenames:
                raise RuntimeError(f"No peptide set files found at {url}")
            for filename in filenames:
                local_path = os.path.join(local_dir, filename)
                if not os.path.isfile(local_path):
                    download_file(f"{url.rstrip('/')}/{filename}", local_path)

        if path is not None:
            source_dir = path
        elif _has_peptide_sets(PEPTIDE_SETS_DIR_SERVER):
            source_dir = PEPTIDE_SETS_DIR_SERVER
        elif _has_peptide_sets(PEPTIDE_SETS_DIR_LOCAL_DENOVO):
            source_dir = PEPTIDE_SETS_DIR_LOCAL_DENOVO
        else:
            _download_peptide_sets(PEPTIDE_SETS_URL, PEPTIDE_SETS_DIR_LOCAL_DENOVO)
            source_dir = PEPTIDE_SETS_DIR_LOCAL_DENOVO

        species_sets = {}
        for peptide_set_path in Path(source_dir).glob("*.txt.gz"):
            species_name = peptide_set_path.name.removesuffix(".txt.gz")
            with gzip.open(peptide_set_path, "rt") as f:
                species_sets[species_name] = set(f.read().splitlines())
        return species_sets

    def evaluate_match(
        self,
        ground_truth: Peptidoform,
        de_novo: Peptidoform,
        allow_il: bool = False,
        allow_deamidation: bool = False,
    ):
        """
        Return the match type between two peptide sequences.

        Parameters
        ----------
        allow_il : bool
            Treat I and L as equivalent when deciding per-residue and whole-peptide
            exactness (mass-based matching is unaffected: I/L are already isomeric).
        allow_deamidation : bool
            Treat deamidated Q/N as equivalent to E/D when deciding exactness
            (mass-based matching is unaffected: they're already isobaric).
        """
        gt_tokens = self.convert_peptidoform(ground_truth)
        dn_tokens = self.convert_peptidoform(de_novo)
        return self.evaluate_match_tokenized(
            ground_truth, de_novo, gt_tokens, dn_tokens, allow_il=allow_il, allow_deamidation=allow_deamidation
        )

    def evaluate_match_tokenized(
        self,
        ground_truth: Peptidoform,
        de_novo: Peptidoform,
        gt_tokens,
        dn_tokens,
        allow_il: bool = False,
        allow_deamidation: bool = False,
    ):
        """
        Same as `evaluate_match`, but takes already-tokenized peptidoforms (the output of
        `convert_peptidoform`) instead of tokenizing internally. Tokenization doesn't depend
        on the ambiguity toggles, so a caller comparing the same pair under multiple
        combinations (as `generate_intermediate` does, once per entry in `AMBIGUITY_COMBOS`)
        can tokenize once and reuse the result across all of them, rather than re-tokenizing
        on every combination. `evaluate_match` is a thin wrapper around this for callers
        comparing a single pair once.

        Parameters
        ----------
        gt_tokens, dn_tokens
            `convert_peptidoform(ground_truth)` / `convert_peptidoform(de_novo)`.
        allow_il : bool
            Treat I and L as equivalent when deciding per-residue and whole-peptide
            exactness (mass-based matching is unaffected: I/L are already isomeric).
        allow_deamidation : bool
            Treat deamidated Q/N as equivalent to E/D when deciding exactness
            (mass-based matching is unaffected: they're already isobaric).
        """
        if dn_tokens is None:
            return {
                "match_type": "mismatch",
                "aa_matches_gt": np.full(len(gt_tokens), False),
                "aa_matches_dn": np.full(len(gt_tokens), False),
                "aa_exact_gt": np.full(len(gt_tokens), False),
                "aa_exact_dn": np.full(len(gt_tokens), False),
                "pep_match": False,
            }

        if ground_truth == de_novo:
            return {
                "match_type": "exact",
                "aa_matches_gt": np.full(len(gt_tokens), True),
                "aa_matches_dn": np.full(len(dn_tokens), True),
                "aa_exact_gt": np.full(len(gt_tokens), True),
                "aa_exact_dn": np.full(len(dn_tokens), True),
                "pep_match": True,
            }

        aa_matches, pep_match, (aa_matches_1, aa_matches_2), (exact_match_1, exact_match_2) = self.aa_match(
            gt_tokens,
            dn_tokens,
            allow_il=allow_il,
            allow_deamidation=allow_deamidation,
        )
        if not pep_match:
            return {
                "match_type": "mismatch",
                "aa_matches_gt": aa_matches_1,
                "aa_matches_dn": aa_matches_2,
                "aa_exact_gt": exact_match_1,
                "aa_exact_dn": exact_match_2,
                "pep_match": pep_match,
            }

        # Full mass-based alignment reached. If every aligned residue is also identity-equal
        # under the active ambiguity toggles, this is an exact match rather than a mass-only one.
        is_fully_exact = bool(exact_match_1.all()) and bool(exact_match_2.all())
        return {
            "match_type": "exact" if is_fully_exact else "mass",
            "aa_matches_gt": aa_matches_1,
            "aa_matches_dn": aa_matches_2,
            "aa_exact_gt": exact_match_1,
            "aa_exact_dn": exact_match_2,
            "pep_match": pep_match,
        }

    def aa_match(
        self,
        peptide1: List[str],
        peptide2: List[str],
        cum_mass_threshold: float = 50,
        ind_mass_threshold: float = 20,
        allow_il: bool = False,
        allow_deamidation: bool = False,
    ) -> Tuple[np.ndarray, bool, Tuple[np.ndarray], Tuple[np.ndarray]]:
        """
        Find the matching prefix and suffix amino acids between two peptide
        sequences.

        Parameters
        ----------
        peptide1 : List[str]
            The first tokenized peptide sequence to be compared.
        peptide2 : List[str]
            The second tokenized peptide sequence to be compared.
        cum_mass_threshold : float
            Mass threshold in ppm to accept cumulative mass-matching amino acid
            sequences.
        ind_mass_threshold : float
            Mass threshold in ppm to accept individual mass-matching amino acids.
        allow_il : bool
            Treat I and L as identical when computing the per-residue exact-match flags.
        allow_deamidation : bool
            Treat deamidated Q/N as identical to E/D when computing the per-residue
            exact-match flags.

        Returns
        -------
        aa_matches : np.ndarray of length max(len(peptide1), len(peptide2))
            Boolean flag indicating whether each paired-up amino acid matches across
            both peptide sequences.
        pep_match : bool
            Boolean flag to indicate whether the two peptide sequences fully match.
        per_seq_aa_matches : Tuple[np.ndarray]
            TODO.
        """
        # Find longest mass-matching prefix.
        aa_matches, pep_match, (aa_matches_1, aa_matches_2), (aa_exact_1, aa_exact_2) = self.aa_match_prefix(
            peptide1,
            peptide2,
            cum_mass_threshold,
            ind_mass_threshold,
            allow_il=allow_il,
            allow_deamidation=allow_deamidation,
        )

        # No need to evaluate the suffixes if the sequences already fully match.
        if pep_match:
            return aa_matches, pep_match, (aa_matches_1, aa_matches_2), (aa_exact_1, aa_exact_2)

        # Find longest mass-matching suffix.
        i1, i2 = len(peptide1) - 1, len(peptide2) - 1
        i_stop = np.argwhere(~aa_matches)[0]
        cum_mass1, cum_mass2 = 0.0, 0.0

        while i1 >= i_stop and i2 >= i_stop:
            # Exact (identity, subject to the ambiguity toggles) -- the prefix walk records
            # this for every position it visits; the suffix walk must do the same, or any
            # position resolved only here silently keeps its initialized `False` regardless
            # of whether it's actually an identity match.
            aa_str1 = self.get_token_str(peptide1[i1], allow_il=allow_il, allow_deamidation=allow_deamidation)
            aa_str2 = self.get_token_str(peptide2[i2], allow_il=allow_il, allow_deamidation=allow_deamidation)
            exact_match = aa_str1 == aa_str2
            aa_exact_1[i1] = exact_match
            aa_exact_2[i2] = exact_match

            aa_mass1 = self.get_token_mass(peptide1[i1])
            aa_mass2 = self.get_token_mass(peptide2[i2])
            tol_suffix = abs(self.mass_diff(cum_mass1 + aa_mass1, cum_mass2 + aa_mass2, False))
            tol_aa = abs(self.mass_diff(aa_mass1, aa_mass2, False))

            if tol_suffix < cum_mass_threshold:
                match = tol_aa < ind_mass_threshold
                aa_matches[max(i1, i2)] = match
                aa_matches_1[i1] = match
                aa_matches_2[i2] = match

                i1, i2 = i1 - 1, i2 - 1
                cum_mass1, cum_mass2 = cum_mass1 + aa_mass1, cum_mass2 + aa_mass2

            elif cum_mass2 + aa_mass2 > cum_mass1 + aa_mass1:
                i1, cum_mass1 = i1 - 1, cum_mass1 + aa_mass1
            else:
                i2, cum_mass2 = i2 - 1, cum_mass2 + aa_mass2

        return aa_matches, aa_matches.all(), (aa_matches_1, aa_matches_2), (aa_exact_1, aa_exact_2)

    def aa_match_prefix(
        self,
        peptide1: List[str],
        peptide2: List[str],
        cum_mass_threshold: float = 50,
        ind_mass_threshold: float = 20,
        allow_il: bool = False,
        allow_deamidation: bool = False,
    ) -> Tuple[np.ndarray, bool, Tuple[np.ndarray], Tuple[np.ndarray]]:
        """
        Find the matching prefix amino acids between two peptide sequences.

        Parameters
        ----------
        peptide1 : List[str]
            The first tokenized peptide sequence to be compared.
        peptide2 : List[str]
            The second tokenized peptide sequence to be compared.
        cum_mass_threshold : float
            Mass threshold in ppm to accept cumulative mass-matching amino acid
            sequences.
        ind_mass_threshold : float
            Mass threshold in ppm to accept individual mass-matching amino acids.
        allow_il : bool
            Treat I and L as identical when computing the per-residue exact-match flags.
        allow_deamidation : bool
            Treat deamidated Q/N as identical to E/D when computing the per-residue
            exact-match flags.

        Returns
        -------
        aa_matches : np.ndarray of length max(len(peptide1), len(peptide2))
            Boolean flag indicating whether each paired-up amino acid matches across
            both peptide sequences.
        pep_match : bool
            Boolean flag to indicate whether the two peptide sequences fully match.
        per_seq_aa_matches : Tuple[np.ndarray]
            TODO.
        """
        aa_matches = np.zeros(max(len(peptide1), len(peptide2)), np.bool_)

        aa_exact_1 = np.zeros(len(peptide1), np.bool_)
        aa_exact_2 = np.zeros(len(peptide2), np.bool_)
        aa_matches_1 = np.zeros(len(peptide1), np.bool_)
        aa_matches_2 = np.zeros(len(peptide2), np.bool_)

        # Find longest mass-matching prefix.
        i1, i2, cum_mass1, cum_mass2 = 0, 0, 0.0, 0.0
        while i1 < len(peptide1) and i2 < len(peptide2):
            # Exact (identity, subject to the ambiguity toggles)
            aa_str1 = self.get_token_str(peptide1[i1], allow_il=allow_il, allow_deamidation=allow_deamidation)
            aa_str2 = self.get_token_str(peptide2[i2], allow_il=allow_il, allow_deamidation=allow_deamidation)
            exact_match = aa_str1 == aa_str2
            aa_exact_1[i1] = exact_match
            aa_exact_2[i2] = exact_match

            # mass-based
            aa_mass1 = self.get_token_mass(peptide1[i1])
            aa_mass2 = self.get_token_mass(peptide2[i2])
            tol_prefix = abs(self.mass_diff(cum_mass1 + aa_mass1, cum_mass2 + aa_mass2, False))
            tol = abs(self.mass_diff(aa_mass1, aa_mass2, False))
            if tol_prefix < cum_mass_threshold:
                match = tol < ind_mass_threshold
                aa_matches[max(i1, i2)] = match
                aa_matches_1[i1] = match
                aa_matches_2[i2] = match

                i1, i2 = i1 + 1, i2 + 1
                cum_mass1, cum_mass2 = cum_mass1 + aa_mass1, cum_mass2 + aa_mass2

            elif cum_mass2 + aa_mass2 > cum_mass1 + aa_mass1:
                i1, cum_mass1 = i1 + 1, cum_mass1 + aa_mass1
            else:
                i2, cum_mass2 = i2 + 1, cum_mass2 + aa_mass2
        return aa_matches, aa_matches.all(), (aa_matches_1, aa_matches_2), (aa_exact_1, aa_exact_2)

    def convert_peptidoform(self, peptidoform: Peptidoform):
        if not isinstance(peptidoform, Peptidoform):
            return None

        out = []
        n_mod = peptidoform.properties["n_term"]
        if n_mod is None or len(n_mod) == 0:
            n_mod = [None]

        # If there is an N-terminal mod, this is separately tokenized.
        else:
            out.append(("", n_mod))

        for i, aa_mod in enumerate(peptidoform):
            aa, mod = aa_mod
            if mod is None:
                mod = [mod]

            out.append((aa, mod))
        return out

    def get_token_mass(self, token: tuple) -> float:
        """
        Convert the amino acid to a mass while considering modifications as well.
        """
        aa, mods = token
        mass = self.AA_MASSES[aa]
        for mod in mods:
            if mod is None:
                continue
            mass += mod.mass
        return mass

    def get_token_str(self, token: tuple, allow_il: bool = False, allow_deamidation: bool = False) -> str:
        """
        Convert the amino acid to string format including the modification if present.

        Parameters
        ----------
        allow_il : bool
            If True, I and L are rendered as the same canonical letter, so tokens that
            differ only by I/L compare equal.
        allow_deamidation : bool
            If True, a deamidated Q or N (UNIMOD:7) is rendered as its isobaric partner
            (E or D respectively) with the modification stripped, so it compares equal
            to a plain, unmodified E or D token.
        """
        aa, mods = token
        mods = [mod for mod in mods if mod is not None]

        if allow_deamidation and len(mods) == 1 and (aa, mods[0].id) in self.DEAMIDATION_ISOBARS:
            return self.DEAMIDATION_ISOBARS[(aa, mods[0].id)]

        if allow_il and aa in ("I", "L"):
            aa = "L"

        token_str = aa
        for mod in mods:
            token_str += "[{}]".format(mod.value)
        return token_str

    def mass_diff(self, mz1, mz2, mode_is_da):
        """
        Calculate the mass difference(s).

        Parameters
        ----------
        mz1
            First m/z value(s).
        mz2
            Second m/z value(s).
        mode_is_da : bool
            Mass difference in Dalton (True) or in ppm (False).

        Returns
        -------
            The mass difference(s) between the given m/z values.
        """
        return mz1 - mz2 if mode_is_da else (mz1 - mz2) / mz2 * 10**6

    def add_fasta_category(
        self, df: pd.DataFrame, species_sets: dict[str, set[str]], min_length: int = 8
    ) -> pd.DataFrame:
        def normalize_for_fasta_match(peptidoform: Peptidoform) -> Optional[str]:
            if isinstance(peptidoform, Peptidoform):
                return peptidoform.sequence.replace("I", "L")
            return None

        df = df.copy()
        df["bare"] = df["peptidoform"].map(normalize_for_fasta_match)
        df["category"] = "not_in_fasta"

        # Exact matching taken from IL allowed str matching
        df.loc[df["match_type_il"] == "exact", "category"] = "correct"

        incorrect = df.loc[~(df["category"] == "correct")]
        for species, idx in incorrect.groupby("collection").groups.items():
            peptide_set = species_sets.get(species, set())
            bare = df.loc[idx, "bare"]
            long_enough = bare.str.len() >= min_length
            match = bare.isin(peptide_set) & long_enough
            df.loc[idx[match], "category"] = "in_fasta"
        return df
