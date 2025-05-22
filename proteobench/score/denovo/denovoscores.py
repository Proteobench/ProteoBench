"""
Module containing the DenovoScores class.
"""

from psm_utils import Peptidoform
from typing import List, Tuple
import pandas as pd
import numpy as np

class DenovoScores:
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

    def generate_intermediate(self, standard_format: pd.DataFrame) -> pd.DataFrame:
        #TODO: Evaluate which PSMs match, and which don't and return new table

        # Add match type label (exact, mass, mismatch) and the amino acid-level evaluations
        standard_format['match_dict'] = standard_format.apply(
            lambda x: self.evaluate_match(
                ground_truth=x['peptidoform_gt'],
                de_novo=x['peptidoform_dn']
            ),
            axis=1
        )
        standard_format['match_type'] = standard_format['match_dict'].apply(lambda x: x['match_type'])
        standard_format['aa_matches_dn'] = standard_format['match_dict'].apply(lambda x: x['aa_matches_dn'])
        standard_format['aa_matches_gt'] = standard_format['match_dict'].apply(lambda x: x['aa_matches_gt'])
        standard_format['pep_match'] = standard_format['match_dict'].apply(lambda x: x['pep_match'])
        _ = standard_format.pop('match_dict')
        return standard_format

    def evaluate_match(self, ground_truth: Peptidoform, de_novo: Peptidoform):
        """
        Return the match type between two peptide sequences.
        """
        gt = self.convert_peptidoform(ground_truth)
        dn = self.convert_peptidoform(de_novo)

        if ground_truth == de_novo:
            return {
                'match_type': 'exact',
                'aa_matches_gt': np.full(len(gt), True),
                'aa_matches_dn': np.full(len(dn), True),
                'pep_match': True
            }
        
        aa_matches, pep_match, (aa_matches_1, aa_matches_2) = self.aa_match(
            gt,
            dn,
        )
        if pep_match:
            return {
                'match_type': 'mass',
                'aa_matches_gt': aa_matches_1,
                'aa_matches_dn': aa_matches_2,
                'pep_match': pep_match
            }
        else:
            return {
                'match_type': 'mismatch',
                'aa_matches_gt': aa_matches_1,
                'aa_matches_dn': aa_matches_2,
                'pep_match': pep_match
            }

    def aa_match(
        self,
        peptide1: List[str],
        peptide2: List[str],
        cum_mass_threshold: float = 50,
        ind_mass_threshold: float = 20,
    ) -> Tuple[np.ndarray, bool, Tuple[np.ndarray]]:
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
            Mass threshold in Dalton to accept cumulative mass-matching amino acid
            sequences.
        ind_mass_threshold : float
            Mass threshold in Dalton to accept individual mass-matching amino acids.

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
        aa_matches, pep_match, (aa_matches_1, aa_matches_2) = self.aa_match_prefix(
            peptide1, peptide2, cum_mass_threshold, ind_mass_threshold
        )

        # No need to evaluate the suffixes if the sequences already fully match.
        if pep_match:
            return aa_matches, pep_match, (aa_matches_1, aa_matches_2)

        # Find longest mass-matching suffix.
        i1, i2 = len(peptide1) - 1, len(peptide2) - 1
        i_stop = np.argwhere(~aa_matches)[0]
        cum_mass1, cum_mass2 = 0.0, 0.0 
        
        while i1 >= i_stop and i2 >= i_stop:
            aa_mass1 = self.get_token_mass(peptide1[i1])
            aa_mass2 = self.get_token_mass(peptide2[i2])
            tol_suffix = abs(self.mass_diff(cum_mass1 + aa_mass1, cum_mass2 + aa_mass2, False))
            tol_aa = abs(self.mass_diff(aa_mass1, aa_mass2, False))

            if (tol_suffix < cum_mass_threshold):

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

        return aa_matches, aa_matches.all(), (aa_matches_1, aa_matches_2)

    def aa_match_prefix(
        self,
        peptide1: List[str],
        peptide2: List[str],
        cum_mass_threshold: float = 50,
        ind_mass_threshold: float = 20,
    ) -> Tuple[np.ndarray, bool, Tuple[np.ndarray]]:
        """
        Find the matching prefix amino acids between two peptide sequences.

        Parameters
        ----------
        peptide1 : List[str]
            The first tokenized peptide sequence to be compared.
        peptide2 : List[str]
            The second tokenized peptide sequence to be compared.
        cum_mass_threshold : float
            Mass threshold in Dalton to accept cumulative mass-matching amino acid
            sequences.
        ind_mass_threshold : float
            Mass threshold in Dalton to accept individual mass-matching amino acids.

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
        aa_matches_1 = np.zeros(len(peptide1), np.bool_)
        aa_matches_2 = np.zeros(len(peptide2), np.bool_)

        # Find longest mass-matching prefix.
        i1, i2, cum_mass1, cum_mass2 = 0, 0, 0.0, 0.0
        while i1 < len(peptide1) and i2 < len(peptide2):
            aa_mass1 = self.get_token_mass(peptide1[i1])
            aa_mass2 = self.get_token_mass(peptide2[i2])
            tol_prefix = abs(self.mass_diff(cum_mass1 + aa_mass1, cum_mass2 + aa_mass2, False))
            tol = abs(self.mass_diff(aa_mass1, aa_mass2, False))
            if (tol_prefix < cum_mass_threshold):
                match = (
                    tol < ind_mass_threshold
                )
                aa_matches[max(i1, i2)] = match
                aa_matches_1[i1] = match
                aa_matches_2[i2] = match

                i1, i2 = i1 + 1, i2 + 1
                cum_mass1, cum_mass2 = cum_mass1 + aa_mass1, cum_mass2 + aa_mass2

            elif cum_mass2 + aa_mass2 > cum_mass1 + aa_mass1:
                i1, cum_mass1 = i1 + 1, cum_mass1 + aa_mass1
            else:
                i2, cum_mass2 = i2 + 1, cum_mass2 + aa_mass2
        return aa_matches, aa_matches.all(), (aa_matches_1, aa_matches_2)


    def convert_peptidoform(self, peptidoform: Peptidoform):
        out = []
        n_mod = peptidoform.properties["n_term"]
        if n_mod is None:
            n_mod = [None]

        # If there is an N-terminal mod, this is seperately tokenized.
        else:
            out.append(("", n_mod))

        for i, aa_mod in enumerate(peptidoform):
            aa, mod = aa_mod
            if mod is None:
                mod = [mod]

            out.append((aa, mod))
        return out
    
    def get_token_mass(
        self,
        token: tuple
    ) -> float:
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
    
    def calculate_prc(
        self,
        scores_correct,
        scores_all,
        total_predicted,
        threshold=None
    ):
        if threshold is None:
            c = len(scores_correct)
            ci = len(scores_all)
        else:
            c = sum([score > threshold for score in scores_correct])
            ci = sum([score > threshold for score in scores_all])
        u = total_predicted-ci

        # precision
        precision = c/ci

        # recall (This is an alternative definition and the line will stop at x=y)
        recall = c/total_predicted

        # coverage
        coverage = ci/total_predicted

        return precision, recall, coverage

    def get_prc_curve(self, t, total_predicted):

        prs = []
        recs = []
        covs = []

        for threshold in np.linspace(t.score.max(), t.score.min()):

            if np.isnan(threshold):
                continue
            
            pr, rec, cov = self.calculate_prc(
                scores_correct=t[t.match].score.to_numpy(),
                scores_all=t.score.to_numpy(),
                total_predicted=total_predicted,
                threshold=threshold
            )
            prs.append(pr)
            recs.append(rec)
            covs.append(cov)

        return pd.DataFrame(
            {'precision': prs,
            'recall': recs,
            'coverage': covs}
        )