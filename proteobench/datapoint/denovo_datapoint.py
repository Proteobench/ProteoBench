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
from proteobench.datapoint.datapoint_base import DatapointBase
from proteobench.score.denovoscores import AMBIGUITY_COMBOS, get_ambiguity_suffix


def calculate_prc(scores_all, is_correct, n_spectra) -> dict:
    """
    Single-point precision/recall/coverage over every prediction (no score threshold).
    """
    is_correct = np.asarray(is_correct, dtype=bool)
    ci = len(scores_all)
    c = int(is_correct.sum())

    return {
        "precision": c / ci,
        "recall": c / n_spectra,
        "coverage": ci / n_spectra,
    }


def get_prc_curve(scores_all, is_correct, n_spectra) -> pd.DataFrame:
    """
    Full-resolution precision-vs-coverage curve, with one point per DISTINCT score value
    rather than one per prediction. Ties are common (many tools emit coarse or repeated
    confidence scores), and a threshold can never split a tied group -- either all of a
    group's predictions clear it, or none do -- so the only well-defined curve vertices are
    "coverage/precision immediately after including an entire tied-score group." Collapsing
    to those vertices also makes the within-tie ordering irrelevant to the result (the
    cumulative count after a full group is the same regardless of the arbitrary order ties
    were processed in), and, as a side effect, shrinks the curve for any tool whose scores
    are heavily quantized. Both the AUC integration and the stored/plotted curve (after
    `downsample_curve`) are derived from this same result.
    """
    scores_all = np.asarray(scores_all, dtype=float)
    is_correct = np.asarray(is_correct, dtype=bool)

    if len(scores_all) == 0:
        return pd.DataFrame({"precision": [], "coverage": []})

    order = np.argsort(-scores_all)
    sorted_scores = scores_all[order]
    sorted_correct = is_correct[order]

    rank = np.arange(1, len(scores_all) + 1)
    cum_correct = np.cumsum(sorted_correct)
    precision = cum_correct / rank
    coverage = rank / n_spectra

    # Keep only the last (highest-rank) row of each run of equal scores -- the sole point in
    # that run where "included" actually changes as the threshold crosses this score value.
    is_last_in_group = np.append(sorted_scores[:-1] != sorted_scores[1:], True)

    return pd.DataFrame({"precision": precision[is_last_in_group], "coverage": coverage[is_last_in_group]})


# Stored/plotted curves are capped at a fixed number of points, sampled at evenly-spaced
# COVERAGE values (not evenly-spaced row positions -- ties can leave the deduplicated curve's
# rows very unevenly spaced in coverage, e.g. one huge tied group followed by many distinct
# scores close together, so only sampling by coverage value itself gives a genuinely even
# spread). Capping by a fixed count, rather than a fixed stride, is what actually bounds
# storage: a stride scales with the size of the ground truth (e.g. ~780k spectra), which is
# exactly what made this unscalable across many tools' worth of curves loaded at once; a fixed
# count does not, regardless of how large the dataset or how many tools are being compared.
# AUC is always integrated over the full-resolution curve in `get_prc_curve`, before this
# runs, so downsampling only affects how many points the plotted line has, never any metric.
CURVE_STORAGE_MAX_POINTS = 500


def downsample_curve(curve: pd.DataFrame, max_points: int = CURVE_STORAGE_MAX_POINTS) -> pd.DataFrame:
    """
    Sample at most `max_points` rows of a curve at evenly-spaced coverage values, always
    including the first and last point.
    """
    if len(curve) <= max_points:
        return curve.reset_index(drop=True)

    coverage = curve["coverage"].to_numpy()
    targets = np.linspace(coverage[0], coverage[-1], max_points)
    # For each evenly-spaced target coverage, the row that was actually "current" at that
    # coverage level: the last row at or before it.
    idx = np.searchsorted(coverage, targets, side="right") - 1
    idx = np.unique(np.clip(idx, 0, len(curve) - 1))
    return curve.iloc[idx].reset_index(drop=True)


def calculate_auc(curve: pd.DataFrame) -> float:
    """
    Area under an already-computed precision-vs-coverage curve (average precision), reported
    as the "AUC" main-plot metric. Returns NaN when the curve has fewer than two points (e.g.
    a tool whose per-token scores are all identical, which happens for tools that don't
    provide real per-residue scores and get a broadcast peptide score instead).
    """
    if len(curve) < 2:
        return float("nan")
    curve = curve.sort_values("coverage")
    # np.trapezoid replaces np.trapz as of numpy 2.0 (removed outright in later numpy);
    # the project's numpy floor predates that, so pick whichever is available.
    trapezoid = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(trapezoid(curve["precision"], curve["coverage"]))


def collapse_aa_scores(df: pd.DataFrame, evaluation_type: str, exact_dn_column: str = "aa_exact_dn"):
    df_aa = {}

    if evaluation_type == "mass":
        df_aa["aa_score"] = list(chain(*df["aa_scores"].tolist()))
        df_aa["aa_match"] = list(chain(*df["aa_matches_dn"].tolist()))
    elif evaluation_type == "exact":
        df_aa["aa_score"] = list(chain(*df["aa_scores"].tolist()))
        df_aa["aa_match"] = list(chain(*df[exact_dn_column].tolist()))
    else:
        raise Exception("Evaluation type should be mass or exact, but {} was provided.".format(evaluation_type))

    return pd.DataFrame(df_aa)


@dataclass
class DenovoDatapoint(DatapointBase):
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
        nr_feature (int): Number of features identified.
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
    precision_peptide: float = 0
    precision_aa: float = 0
    recall_aa: float = 0
    recall_peptide: float = 0
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

            # Ambiguity-toggle variants (I/L, deamidated Q/N vs E/D) only affect exact-mode
            # matching -- mass mode already can't distinguish these (I/L are isomeric,
            # deamidated Q/N are isobaric with E/D), so its metrics are identical regardless
            # and aren't recomputed per combination. Precomputed here (once, at benchmarking
            # time) rather than at plot time, since only the aggregated `results` dict -- not
            # the raw intermediate dataframe -- is persisted for a submitted datapoint.
            results[l]["exact"]["ambiguity"] = {}
            for suffix, flags in AMBIGUITY_COMBOS.items():
                if not suffix:
                    continue  # baseline combination; already stored as results[l]["exact"]
                combo_key = suffix.lstrip("_")
                results[l]["exact"]["ambiguity"][combo_key] = DenovoDatapoint.get_metrics(
                    self=DenovoDatapoint(), df=intermediate, level=l, evaluation="exact", **flags
                )

        results["in_depth"] = DenovoDatapoint.get_indepth_metrics(self=DenovoDatapoint(), df=intermediate)
        result_datapoint.results = results
        result_datapoint.precision_peptide = result_datapoint.results["peptide"][evaluation_type]["precision"]
        result_datapoint.recall_peptide = result_datapoint.results["peptide"][evaluation_type]["recall"]
        result_datapoint.precision_aa = result_datapoint.results["aa"][evaluation_type]["precision"]
        result_datapoint.recall_aa = result_datapoint.results["aa"][evaluation_type]["recall"]

        results_series = pd.Series(dataclasses.asdict(result_datapoint))
        return results_series

    def get_metrics(
        self,
        df: pd.DataFrame,
        level: str,
        evaluation: str,
        allow_il: bool = False,
        allow_deamidation: bool = False,
    ):
        """
        Compute various statistical metrics from the provided DataFrame for the benchmark.

        Parameters
        ----------
        allow_il : bool
            Only meaningful when `evaluation="exact"`: read the match/exactness columns
            computed with I/L treated as equivalent. Ignored for `evaluation="mass"`,
            since mass-based matching can't distinguish I/L regardless.
        allow_deamidation : bool
            Only meaningful when `evaluation="exact"`: read the match/exactness columns
            computed with deamidated Q/N treated as equivalent to E/D. Ignored for
            `evaluation="mass"` for the same reason as `allow_il`.
        """

        if evaluation == "mass":
            evaluation_list = ["mass", "exact"]
            match_col = "match_type"
            exact_dn_column = "aa_exact_dn"
        elif evaluation == "exact":
            evaluation_list = ["exact"]
            suffix = get_ambiguity_suffix(allow_il, allow_deamidation)
            match_col = f"match_type{suffix}"
            exact_dn_column = f"aa_exact_dn{suffix}"
        else:
            raise Exception("Only `exact` and `mass` evaluation types are supported. Should never happen.")

        if level == "peptide":
            n = len(df)
            df_filtered = df.dropna(subset="peptidoform")
            scores_all = df_filtered["score"].tolist()
            is_correct = df_filtered[match_col].isin(evaluation_list).tolist()

        elif level == "aa":
            n_aa = df["aa_matches_gt"].apply(len).sum()
            df_filtered = df.dropna(subset="peptidoform")
            df_aa = collapse_aa_scores(df_filtered, evaluation_type=evaluation, exact_dn_column=exact_dn_column)
            scores_all = df_aa["aa_score"].tolist()
            is_correct = df_aa["aa_match"].tolist()
            n = n_aa

        else:
            raise Exception(
                "Only `aa` and `peptide` levels for accuracy calculation are supported. Should never happen."
            )

        res = calculate_prc(scores_all=scores_all, is_correct=is_correct, n_spectra=n)
        full_curve = get_prc_curve(scores_all=scores_all, is_correct=is_correct, n_spectra=n)
        res["auc"] = calculate_auc(full_curve)
        stored_curve = downsample_curve(full_curve)
        res["curve"] = {"coverage": stored_curve["coverage"].tolist(), "precision": stored_curve["precision"].tolist()}
        return res

    def get_indepth_metrics(self, df: pd.DataFrame):
        extra_metrics = {}

        extra_metrics["in_FASTA"] = self.get_infasta_metrics(df)
        extra_metrics["PTM"] = self.get_ptm_metrics(df)
        extra_metrics["Spectrum"] = self.get_spectrum_metrics(df)
        extra_metrics["Species"] = self.get_species_metrics(df)

        return extra_metrics

    def get_infasta_metrics(self, df: pd.DataFrame) -> dict:
        """
        Aggregate the per-PSM FASTA category (``correct`` / ``in_fasta`` / ``not_in_fasta``,
        assigned once by `DenovoScores.add_fasta_category` at the end of
        `generate_intermediate`) into counts and proportions for this single datapoint.
        Precomputed here -- like every other in-depth metric -- so multiple datapoints can be
        plotted together from their stored `results` dicts alone, without re-deriving anything
        (e.g. via a live groupby) from each datapoint's raw intermediate dataframe, which isn't
        persisted.
        """
        categories = ("correct", "in_fasta", "not_in_fasta")
        n = len(df)
        counts = df["category"].value_counts().reindex(categories, fill_value=0).astype(int).to_dict()
        proportions = {cat: (counts[cat] / n if n else float("nan")) for cat in categories}
        return {"counts": counts, "proportions": proportions, "n_spectra": n}

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
            for row in df[df[mod_label]].itertuples():
                mod_count, correct = self.evaluate_ptm(
                    mod_label=mod_label,
                    mod_tag=unimod_tag,
                    peptidoform=row.peptidoform_ground_truth,
                    match_array=row.aa_exact_gt,
                )
                mod_counts[mod_label]["counts_gt"] += mod_count
                mod_counts[mod_label]["correct_gt"] += correct

        # On predicted
        df_filtered = df.dropna()  # Due to no predictions for certain spectra
        for mod_label, unimod_tag in mod_labels_dn.items():
            mod_count = 0
            correct = 0
            for row in df_filtered[df_filtered[mod_label]].itertuples():
                mod_count, correct = self.evaluate_ptm(
                    mod_label=mod_label,
                    mod_tag=unimod_tag,
                    peptidoform=row.peptidoform,
                    match_array=row.aa_exact_dn,
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
            if isinstance(peptidoform.properties["n_term"], list) and len(peptidoform.properties["n_term"]) > 0:
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
