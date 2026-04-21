"""Regression test for PEAKS DIA diaPASEF parsing.

Reproduces the failure from benchmark_analysis.py where melt() receives an empty
value_vars set because:

- PEAKS output column names are ``LFQ_<sample> Normalized Area`` (cleaned by
  ``_clean_run_name`` to ``LFQ_<sample>``).
- ``[[samples]].raw_file`` entries in ``module_settings.toml`` are bare sample
  names with a numeric server-side suffix, e.g. ``ttSCP_..._Alpha_01_11494``.
- The default ``_clean_run_name`` regex cannot strip the ``LFQ_`` prefix or add
  the ``_11494`` suffix, so the two key spaces never intersect and
  ``condition_mapper`` produces no usable melt columns.

The test uses the real per-tool TOML (``parse_settings_peaks.toml``) and the
real module TOML for diaPASEF, along with a small synthesized DataFrame that
mirrors the PEAKS file header layout.
"""

import os

import pandas as pd
import pytest

from proteobench.io.parsing.convert_to_intermediate import ConverterBuilder

MODULE_ID = "quant_lfq_DIA_ion_diaPASEF"

PARSE_SETTINGS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "proteobench",
        "io",
        "parsing",
        "io_parse_settings",
        "Quant",
        "lfq",
        "DIA",
        "ion",
        "diaPASEF",
    )
)

# Bare sample names (without the _11494 / _11500 / ... server-side numeric suffixes
# that [[samples]].raw_file carries, and without PEAKS' LFQ_ prefix).
SAMPLES = [
    "ttSCP_diaPASEF_Condition_A_Sample_Alpha_01",
    "ttSCP_diaPASEF_Condition_A_Sample_Alpha_02",
    "ttSCP_diaPASEF_Condition_A_Sample_Alpha_03",
    "ttSCP_diaPASEF_Condition_B_Sample_Alpha_01",
    "ttSCP_diaPASEF_Condition_B_Sample_Alpha_02",
    "ttSCP_diaPASEF_Condition_B_Sample_Alpha_03",
]


def _build_peaks_sample_df() -> pd.DataFrame:
    """Synthesize a PEAKS DIA diaPASEF output with 3 precursors across 6 samples.

    Column naming mirrors the real file: ``LFQ_<sample> <subcolumn>`` where
    subcolumn is one of {m/z, RT mean, Normalized Area}.
    """
    base = {
        "Peptide": ["PEPTIDEA(+57.02)K", "PEPTIDEBR", "PEPTIDECK"],
        "Accession": ["PROT1_HUMAN", "PROT2_YEAST", "PROT3_ECOLI"],
        "z": [2, 3, 2],
    }
    intensities = {
        "LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_01": [1.0e6, 2.0e6, 3.0e6],
        "LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_02": [1.1e6, 2.1e6, 3.1e6],
        "LFQ_ttSCP_diaPASEF_Condition_A_Sample_Alpha_03": [1.2e6, 2.2e6, 3.2e6],
        "LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_01": [2.0e6, 1.0e6, 1.5e6],
        "LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_02": [2.1e6, 1.1e6, 1.4e6],
        "LFQ_ttSCP_diaPASEF_Condition_B_Sample_Alpha_03": [2.2e6, 1.2e6, 1.6e6],
    }
    df = pd.DataFrame(base)
    for sample_col, vals in intensities.items():
        # PEAKS writes three sub-columns per sample; the one we care about is
        # "Normalized Area". m/z and RT mean are harmless extras.
        df[f"{sample_col} m/z"] = [500.0, 600.0, 700.0]
        df[f"{sample_col} RT mean"] = [10.0, 20.0, 30.0]
        df[f"{sample_col} Normalized Area"] = vals
    return df


def test_peaks_diapasef_condition_mapper_matches_df_columns():
    """After init + column cleanup, condition_mapper keys overlap df.columns."""
    builder = ConverterBuilder(parse_settings_dir=PARSE_SETTINGS_DIR, module_id=MODULE_ID)
    converter = builder.build_parser("PEAKS")

    df = _build_peaks_sample_df()
    # Same cleanup the pipeline applies before melt (see convert_to_standard_format).
    df_cleaned_cols = [converter._clean_run_name(c) for c in df.columns]

    overlap = set(converter.condition_mapper.keys()) & set(df_cleaned_cols)
    assert overlap, (
        "condition_mapper keys don't intersect cleaned PEAKS column names.\n"
        f"  condition_mapper keys (first 3): {list(converter.condition_mapper)[:3]}\n"
        f"  cleaned df columns (first 6):    {df_cleaned_cols[:6]}"
    )


def test_peaks_diapasef_convert_to_standard_format_succeeds():
    """Full conversion runs end-to-end and produces a melted long-format df."""
    builder = ConverterBuilder(parse_settings_dir=PARSE_SETTINGS_DIR, module_id=MODULE_ID)
    converter = builder.build_parser("PEAKS")

    df = _build_peaks_sample_df()
    out = converter.convert_to_standard_format(df)

    assert "Raw file" in out.columns, "expected long-format output with 'Raw file' column"
    assert "Intensity" in out.columns
    assert "replicate" in out.columns
    assert out["replicate"].isin({"A", "B"}).all(), f"unexpected replicate values: {out['replicate'].unique()}"
    assert len(out) > 0
