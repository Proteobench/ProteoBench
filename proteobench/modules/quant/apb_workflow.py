"""Compose APB parsing and HYE/HY scoring for a quantitative upload."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from apb2.api import ParseRuleCompiler
from apb_proteobench.api import ProteoBenchAnalysisResult, ProteoBenchAnalyzer
from apb_proteobench.calculation.intermediate import align_runs
from apb_proteobench.calculation.metrics import PROTEOBENCH_SOURCE_REVISION
from apb_proteobench.configuration.load import load_packaged_module
from apb_proteobench.integration import PRIMARY_LAYER, ScoredLayerResult, extract_layer
from apb_proteobench.io.result_performance import SubmissionContent, content_hash

from proteobench import __version__

_SOFTWARE_HINTS = {
    "Custom": "pb_custom",
    "ProteoBench Custom": "pb_custom",
    "FragPipe (DIA-NN quant)": "DIA-NN",
}
_SEARCH_FIELDS = (
    "search_engine",
    "search_engine_version",
    "ident_fdr_psm",
    "ident_fdr_peptide",
    "ident_fdr_protein",
    "enable_match_between_runs",
    "precursor_mass_tolerance",
    "fragment_mass_tolerance",
    "enzyme",
    "allowed_miscleavages",
    "min_peptide_length",
    "max_peptide_length",
)
_SUMMARY_FIELDS = (
    "median_abs_epsilon_global",
    "mean_abs_epsilon_global",
    "median_abs_epsilon_eq_species",
    "mean_abs_epsilon_eq_species",
    "median_abs_epsilon_precision_global",
    "mean_abs_epsilon_precision_global",
    "median_abs_epsilon_precision_eq_species",
    "mean_abs_epsilon_precision_eq_species",
    "nr_feature",
)


@dataclass(frozen=True, slots=True)
class APBQuantAnalysis:
    """A scored APB result and its existing ProteoBench plot table."""

    result: ProteoBenchAnalysisResult
    software: str

    @property
    def selected_layer(self) -> ScoredLayerResult:
        """Return the sole primary layer scored for one upload."""
        if len(self.result.layers) != 1:
            raise ValueError(f"Expected one APB primary layer, got {len(self.result.layers)}")
        return next(iter(self.result.layers.values()))

    @property
    def intermediate(self) -> pd.DataFrame:
        """Project completed APB diagnostics to the current plot/CSV columns."""
        return self.selected_layer.analysis.diagnostics.legacy

    @property
    def content_hash(self) -> str:
        """Return the APB ProteoBench scientific upload identity."""
        selected = self.selected_layer
        extracted = extract_layer(self.result.parsed, self.result.configuration, selected.layer_name)
        source = extracted.calculation
        if not isinstance(source.matrix, np.ndarray):
            raise TypeError("APB2 layer extraction did not produce a dense matrix")
        design = align_runs(source.observations, self.result.configuration)
        settings = self.result.configuration.model_dump(mode="json", exclude={"samples"})
        settings["source_revision"] = PROTEOBENCH_SOURCE_REVISION
        settings["diagnostic_method"] = selected.analysis.diagnostic_method
        settings["scoring_method"] = selected.analysis.scoring_method
        return content_hash(
            SubmissionContent(
                matrix=source.matrix,
                feature_ids=source.feature_ids,
                reported_proteins=source.reported_proteins,
                raw_files=design.raw_files,
                conditions=tuple(design.conditions),
                settings=settings,
                mapper_sha256=selected.analysis.diagnostics.protein_mapping.accession_mapper.sha256,
            )
        )

    def datapoint(
        self,
        *,
        input_format: str,
        user_input: Mapping[str, object],
        cutoff: int = 3,
    ) -> pd.Series:
        """Project APB scores to the existing temporary plot/submission fields."""
        scores = self.selected_layer.analysis.scores.model_dump(mode="json")
        cutoff_scores = scores["results"].get(str(cutoff))
        if cutoff_scores is None:
            raise ValueError(f"APB scores have no cutoff {cutoff}")
        for field in _SUMMARY_FIELDS:
            scores[field] = cutoff_scores[field]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        document = {
            **{field: user_input.get(field) for field in _SEARCH_FIELDS},
            **scores,
            "id": f"{input_format}_{timestamp}",
            "software_name": input_format,
            "software_version": user_input.get("software_version") or "",
            "intermediate_hash": self.content_hash,
            "is_temporary": True,
            "old_new": "new",
            "comments": user_input.get("comments_for_plotting") or "",
            "proteobench_version": __version__,
        }
        return pd.Series(document)


def analyze_quant_upload(source: Path, *, software: str, module: str) -> APBQuantAnalysis:
    """Parse a raw result using the named producer and score one quant module.

    Search parameters are not required at upload time. APB2 raises when the
    producer hint and result columns cannot select a scientifically sound rule.
    """
    software = _SOFTWARE_HINTS.get(software, software)
    loaded = load_packaged_module(module)
    compiler = ParseRuleCompiler.from_software(
        source,
        software=software,
        requested_levels=(loaded.settings.general.level,),
    )
    parsed = compiler.compile().parse()
    result = ProteoBenchAnalyzer(loaded, selection=PRIMARY_LAYER).analyze(parsed)
    return APBQuantAnalysis(result=result, software=compiler.detection.software)
