"""
This module provides functionality for storing the de novo metrics.
"""

from __future__ import annotations

import dataclasses
import hashlib
import logging
from collections import ChainMap, defaultdict
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from typing import Any, Dict, List

import numpy as np
import pandas as pd

import proteobench


def calculate_prc(scores_correct, scores_all, n_spectra, threshold=None):
    if threshold is None:
        c = len(scores_correct)
        ci = len(scores_all)
    else:
        c = sum([score > threshold for score in scores_correct])
        ci = sum([score > threshold for score in scores_all])

    u = n_spectra - ci

    # precision
    precision = c / ci

    # recall (This is an alternative definition and the line will stop at x=y)
    recall = c / n_spectra

    # coverage
    coverage = ci / n_spectra

    return {"precision": precision, "recall": recall, "coverage": coverage}


def get_prc_curve(t, n_spectra):
    prs = []
    recs = []
    covs = []

    for threshold in np.linspace(t.score.max(), t.score.min()):
        if np.isnan(threshold):
            continue

        prc_dict = calculate_prc(
            scores_correct=t[t.match].score.to_numpy(),
            scores_all=t.score.to_numpy(),
            n_spectra=n_spectra,
            threshold=threshold,
        )
        pr, rec, cov = prc_dict["precision"], prc_dict["recall"], prc_dict["coverage"]
        prs.append(pr)
        recs.append(rec)
        covs.append(cov)

    return pd.DataFrame({"precision": prs, "recall": recs, "coverage": covs})


def collapse_aa_scores(df: pd.DataFrame, evaluation_type: str):
    df_aa = {}

    if evaluation_type == "mass":
        df_aa["aa_score"] = list(chain(*df["aa_scores"].tolist()))
        df_aa["aa_match"] = list(chain(*df["aa_matches_dn"].tolist()))
    elif evaluation_type == "exact":
        df_aa["aa_score"] = list(chain(*df["aa_scores"].tolist()))
        df_aa["aa_match"] = list(chain(*df["aa_exact_dn"].tolist()))
    else:
        raise Exception("Evaluation type should be mass or exact, but {} was provided.".format(evaluation_type))

    return pd.DataFrame(df_aa)


@dataclass
class DenovoDatapoint:
    """
    A data structure used to store the results of a benchmark run.

    Attributes:
        id (str): Unique identifier for the benchmark run.
        software_name (str): Name of the software used in the benchmark.
        software_version (str): Version of the software.
        search_engine (str): Name of the search engine used.
        search_engine_version (str): Version of the search engine.
        ident_fdr_psm (float): False discovery rate for PSMs.
        ident_fdr_peptide (float): False discovery rate for peptides.
        ident_fdr_protein (float): False discovery rate for proteins.
        enable_match_between_runs (bool): Whether matching between runs is enabled.
        precursor_mass_tolerance (str): Mass tolerance for precursor ions.
        fragment_mass_tolerance (str): Mass tolerance for fragment ions.
        enzyme (str): Enzyme used for digestion.
        allowed_miscleavages (int): Number of allowed miscleavages.
        min_peptide_length (int): Minimum peptide length.
        max_peptide_length (int): Maximum peptide length.
        is_temporary (bool): Whether the data is temporary.
        intermediate_hash (str): Hash of the intermediate result.
        results (dict): A dictionary of metrics for the benchmark run.
        median_abs_epsilon (float): Median absolute epsilon value for the benchmark.
        mean_abs_epsilon (float): Mean absolute epsilon value for the benchmark.
        nr_prec (int): Number of precursors identified.
        comments (str): Any additional comments.
        proteobench_version (str): Version of the Proteobench tool used.
    """

    id: str = None
    software_name: str = None
    software_version: int = 0
    checkpoint: str = None
    n_beams: int = None
    n_peaks: int = None
    precursor_mass_tolerance: str = None
    min_peptide_length: int = 0
    max_peptide_length: int = 0
    min_mz: int = 0
    max_mz: int = 50000
    min_intensity: int = 0
    max_intensity: int = 1
    tokens: str = None
    min_precursor_charge: int = 1
    max_precursor_charge: int = None
    remove_precursor_tol: str = None
    isotope_error_range: str = None
    decoding_strategy: str = None
    is_temporary: bool = True
    intermediate_hash: str = ""
    results: dict = None
    # Add other elements here such as PR lists
    precision: float = 0
    recall: float = 0
    comments: str = ""
    proteobench_version: str = ""

    def generate_id(self) -> None:
        """
        Generate a unique ID for the benchmark run by combining the software name and a timestamp.

        This ID is used to uniquely identify each run of the benchmark.
        """
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = "_".join([self.software_name, str(time_stamp)])
        logging.info(f"Assigned the following ID to this run: {self.id}")

    @staticmethod
    def generate_datapoint(
        intermediate: pd.DataFrame,
        input_format: str,
        user_input: dict,
        subset_columns_hash: List[str] = ["spectrum_id", "peptide_str", "score"],
        level: str = "peptide",
        evaluation_type: str = "mass",
        # Maybe add here aa/peptide precision
        # And also type of match required (exact/mass-based)
    ) -> pd.Series:
        """
        Generate a Datapoint object containing metadata and results from the benchmark run.
        """
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        if "comments_for_plotting" not in user_input.keys():
            user_input["comments_for_plotting"] = ""

        try:
            user_input = defaultdict(
                user_input.default_factory,  # Preserve the default factory
                {key: ("" if value is None else value) for key, value in user_input.items()},
            )
        except AttributeError:
            user_input = {key: ("" if value is None else value) for key, value in user_input.items()}

        intermediate["peptide_str"] = intermediate["peptidoform"].apply(lambda x: str(x))
        new_hash = hashlib.sha1(
            pd.util.hash_pandas_object(intermediate.loc[:, subset_columns_hash], index=True).values.tobytes()
        ).hexdigest()
        _ = intermediate.pop("peptide_str")

        result_datapoint = DenovoDatapoint(
            id=input_format + "_" + user_input["software_version"] + "_" + formatted_datetime,
            software_name=input_format,
            software_version=user_input["software_version"],
            checkpoint=user_input["checkpoint"],
            n_beams=user_input["n_beams"],
            n_peaks=user_input["n_peaks"],
            precursor_mass_tolerance=user_input["precursor_mass_tolerance"],
            min_peptide_length=user_input["min_peptide_length"],
            max_peptide_length=user_input["max_peptide_length"],
            min_mz=user_input["min_mz"],
            max_mz=user_input["max_mz"],
            min_intensity=user_input["min_intensity"],
            max_intensity=user_input["max_intensity"],
            tokens=user_input["tokens"],
            min_precursor_charge=user_input["min_precursor_charge"],
            max_precursor_charge=user_input["max_precursor_charge"],
            remove_precursor_tol=user_input["remove_precursor_tol"],
            isotope_error_range=user_input["isotope_error_range"],
            decoding_strategy=user_input["decoding_strategy"],
            intermediate_hash=new_hash,
            comments=user_input["comments_for_plotting"],
            proteobench_version=proteobench.__version__,
        )

        result_datapoint.generate_id()

        results = {"peptide": {}, "aa": {}}
        for l in ["peptide", "aa"]:
            for e_type in ["exact", "mass"]:
                results[l][e_type] = DenovoDatapoint.get_metrics(
                    self=DenovoDatapoint(), df=intermediate, level=l, evaluation=e_type
                )

        results["in_depth"] = DenovoDatapoint.get_indepth_metrics(self=DenovoDatapoint(), df=intermediate)
        result_datapoint.results = results
        result_datapoint.precision = result_datapoint.results[level][evaluation_type]["precision"]
        result_datapoint.recall = result_datapoint.results[level][evaluation_type]["recall"]

        results_series = pd.Series(dataclasses.asdict(result_datapoint))
        return results_series

    def get_metrics(self, df: pd.DataFrame, level: str, evaluation: str):
        """
        Compute various statistical metrics from the provided DataFrame for the benchmark.
        """

        if evaluation == "mass":
            evaluation_list = ["mass", "exact"]
        elif evaluation == "exact":
            evaluation_list = ["exact"]
        else:
            raise Exception("Only `exact` and `mass` evaluation types are supported. Should never happen.")

        if level == "peptide":
            n = len(df)
            df_filtered = df.dropna(subset="peptidoform")
            scores_correct = df_filtered.loc[df_filtered["match_type"].isin(evaluation_list), "score"].tolist()
            scores_all = df_filtered["score"].tolist()

        elif level == "aa":
            n_aa = df["aa_matches_gt"].apply(len).sum()
            df_filtered = df.dropna(subset="peptidoform")
            df_aa = collapse_aa_scores(df_filtered, evaluation_type=evaluation)
            scores_correct = df_aa.loc[df_aa["aa_match"], "aa_score"].tolist()
            scores_all = df_aa["aa_score"].tolist()
            n = n_aa

        else:
            raise Exception(
                "Only `aa` and `peptide` levels for accuracy calculation are supported. Should never happen."
            )

        res = calculate_prc(scores_correct=scores_correct, scores_all=scores_all, n_spectra=n, threshold=None)
        return res

    def get_indepth_metrics(self, df: pd.DataFrame):
        extra_metrics = {}

        extra_metrics["PTM"] = self.get_ptm_metrics(df)
        extra_metrics["Spectrum"] = self.get_spectrum_metrics(df)
        extra_metrics["Species"] = self.get_species_metrics(df)

        return extra_metrics

    def get_ptm_metrics(self, df: pd.DataFrame):
        mod_counts = {}
        mod_labels_gt = {
            "M-Oxidation": "M[UNIMOD:35]",
            "Q-Deamidation": "Q[UNIMOD:7]",
            "N-Deamidation": "N[UNIMOD:7]",
            "N-term Acetylation": "[UNIMOD:1]-",
            "N-term Carbamylation": "[UNIMOD:5]-",
            "N-term Ammonia-loss": "[UNIMOD:385]-",
        }
        mod_labels_dn = {
            "M-Oxidation (denovo)": "M[UNIMOD:35]",
            "Q-Deamidation (denovo)": "Q[UNIMOD:7]",
            "N-Deamidation (denovo)": "N[UNIMOD:7]",
            "N-term Acetylation (denovo)": "[UNIMOD:1]-",
            "N-term Carbamylation (denovo)": "[UNIMOD:5]-",
            "N-term Ammonia-loss (denovo)": "[UNIMOD:385]-",
        }

        # Init the mod_counts
        mod_counts = {
            mod_label: {"counts_gt": 0, "correct_gt": 0, "counts_dn": 0, "correct_dn": 0}
            for mod_label in list(mod_labels_gt.keys())
        }

        # On ground-truth
        for mod_label, unimod_tag in mod_labels_gt.items():
            mod_count = 0
            correct = 0
            for i, row in df[df[mod_label]].iterrows():

                mod_count, correct = self.evaluate_ptm(
                    mod_label=mod_label,
                    mod_tag=unimod_tag,
                    peptidoform=row["peptidoform_ground_truth"],
                    match_array=row["aa_exact_gt"],
                )
                mod_counts[mod_label]["counts_gt"] += mod_count
                mod_counts[mod_label]["correct_gt"] += correct

        # On predicted
        for mod_label, unimod_tag in mod_labels_dn.items():
            df_filtered = df.dropna()  # Due to no predictions for certain spectra
            mod_count = 0
            correct = 0
            for i, row in df_filtered[df_filtered[mod_label]].iterrows():

                mod_count, correct = self.evaluate_ptm(
                    mod_label=mod_label,
                    mod_tag=unimod_tag,
                    peptidoform=row["peptidoform"],
                    match_array=row["aa_exact_dn"],
                )
                mod_counts[mod_label.split("(denovo)")[0].strip()]["counts_dn"] += mod_count
                mod_counts[mod_label.split("(denovo)")[0].strip()]["correct_dn"] += correct
        return mod_counts

    @staticmethod
    def evaluate_ptm(mod_label, mod_tag, peptidoform, match_array):
        mod_count = 0
        correct = 0
        if mod_label.startswith("N-term"):
            mod_count += 1
            if match_array[0]:
                correct += 1

        else:
            mod_count += peptidoform.modified_sequence.count(mod_tag)
            parsed_seq = peptidoform.parsed_sequence
            # N-term mod is seperatly tokenized and thus seperatly evaluated (aa_match list is longer than peptide length)
            if isinstance(peptidoform.properties["n_term"], list):
                parsed_seq = [(None, None)] + parsed_seq

            assert len(parsed_seq) == len(match_array)
            for match_bool, aa in zip(match_array, parsed_seq):
                if isinstance(aa[1], list) and "{}[UNIMOD:{}]".format(aa[0], aa[1][0].id) == mod_tag and match_bool:
                    correct += 1
        return mod_count, correct

    @staticmethod
    def record_proportions_to_results_feature(
        series: pd.Series, counts: dict, min_el: int = 1, max_el: int = 30, all_elements=None
    ) -> dict:
        data = {}

        if isinstance(all_elements, list):
            iteration = all_elements
        else:
            iteration = range(min_el, max_el + 1)

        for i in iteration:
            try:
                proportions = series[i]

                try:
                    exact = proportions["exact"]
                except KeyError:
                    exact = 0.0

                try:
                    mass_based = 1 - proportions["mismatch"]
                except:
                    mass_based = 1.0

            except KeyError as e:
                exact = None
                mass_based = None

            if isinstance(i, float) and np.isnan(i):
                continue

            try:
                count_subset = counts[i]
            except:
                count_subset = 0

            data[i] = {"exact": exact, "mass": mass_based, "n_spectra": count_subset}
        return data

    def get_spectrum_metrics(self, df: pd.DataFrame):

        results = {}
        intermediate = df.dropna()

        # Missing fragmentation sites
        series = intermediate.groupby("missing_frag_sites")["match_type"].value_counts(normalize=True)
        counts = intermediate.groupby("missing_frag_sites").count()["match_type"].to_dict()
        results["Missing Fragmentation Sites"] = self.record_proportions_to_results_feature(
            series, counts, min_el=0, max_el=30
        )

        # Peptide length
        series = intermediate.groupby("peptide_length")["match_type"].value_counts(normalize=True)
        counts = intermediate.groupby("peptide_length").count()["match_type"].to_dict()
        results["Peptide Length"] = self.record_proportions_to_results_feature(series, counts, min_el=5, max_el=30)

        # Explained intensity
        intermediate_selection = intermediate[["explained_by_pct", "match_type"]].copy()
        intermediate_selection["intensity_binned"] = pd.Series(
            pd.cut(intermediate_selection["explained_by_pct"].tolist(), bins=np.arange(0, 1, 0.03))
        ).astype(str)
        indices = intermediate_selection["intensity_binned"].sort_values().drop_duplicates().tolist()
        series = intermediate_selection.groupby("intensity_binned").match_type.value_counts(normalize=True)
        counts = intermediate_selection.groupby("intensity_binned").count()["match_type"].to_dict()
        series.name = "percentage"
        results["% Explained Intensity"] = self.record_proportions_to_results_feature(
            series, counts, all_elements=indices
        )

        # Cosine similarity
        # results['cosine'] = {
        #     'exact': intermediate[intermediate['match_type']=='exact'],
        #     'mass': intermediate[intermediate['match_type'].isin(['exact', 'mass'])]
        # }

        return results

    def get_species_metrics(self, df: pd.DataFrame):

        species = [
            "Solanum-lycopersicum",
            "Mus-musculus",
            "Bacillus-subtilis",
            "Apis-mellifera",
            "Vigna-mungo",
            "Methanosarcina-mazei",
            "Candidatus-endoloripes",
            "H.-sapiens",
            "Saccharomyces-cerevisiae",
        ]

        series = df.groupby("collection")["match_type"].value_counts(normalize=True)
        counts = df.groupby("collection").count()["match_type"].to_dict()
        species_result = self.record_proportions_to_results_feature(series, counts, all_elements=species)
        return species_result
