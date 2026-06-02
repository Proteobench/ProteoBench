"""
Central submission-validation API.

:func:`validate_submission` runs the individual checks against a standardized
result DataFrame and the parsed parameters, returning a single structured
:class:`~proteobench.validation.report.ValidationReport`. The caller decides
what to do with the report (typically: block public submission when
``report.has_errors`` is true, but allow it through with warnings).

The function is framework-agnostic and performs no I/O: the reference FASTA is
supplied as an already-built :class:`~proteobench.validation.fasta.FastaReference`
(or ``None`` to skip protein-identifier validation). Front ends are responsible
for obtaining the standardized DataFrame (by reusing the existing parser) and
the FASTA reference (by reading the module configuration).
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from proteobench.validation.checks import (
    check_charge_range,
    check_enzyme,
    check_modifications,
    check_peptide_length,
    check_protein_ids,
    check_run_consistency,
)
from proteobench.validation.config import ModuleValidationConfig
from proteobench.validation.fasta import FastaReference
from proteobench.validation.report import ValidationReport


def validate_submission(
    standard_df: pd.DataFrame,
    parameters: Any = None,
    fasta: Optional[FastaReference] = None,
    config: Optional[ModuleValidationConfig] = None,
    input_format: Optional[str] = None,
) -> ValidationReport:
    """
    Validate a benchmark submission and return a structured report.

    Runs, in order: protein-identifier validation against the reference FASTA,
    precursor-charge range, peptide-length range, enzyme/missed-cleavage
    heuristic, modification compatibility, and run consistency. Each check is
    fault-tolerant: a check that raises an unexpected exception is converted to
    a warning so that validation itself never crashes the submission flow.

    Parameters
    ----------
    standard_df : pandas.DataFrame
        The standardized result DataFrame (output of
        ``ParseSettingsQuant.convert_to_standard_format``), containing at least
        the ``Proteins``, ``Sequence``, and ``Charge`` columns.
    parameters : Any, optional
        Parsed parameters (a :class:`ProteoBenchParameters` or any object with
        the same attributes). If ``None``, parameter-dependent checks are
        skipped with warnings.
    fasta : FastaReference, optional
        Reference protein identifiers. If ``None``, protein-identifier
        validation is skipped with an info message.
    config : ModuleValidationConfig, optional
        Module validation configuration. Defaults to a generic configuration.
    input_format : str, optional
        The selected software tool, used for run-consistency checks.

    Returns
    -------
    ValidationReport
        The aggregated validation report.
    """
    config = config or ModuleValidationConfig()
    report = ValidationReport()

    if not isinstance(standard_df, pd.DataFrame) or standard_df.empty:
        report.add_error(
            "empty_results",
            "The standardized results are empty; nothing could be validated.",
            "input",
        )
        return report

    # Protein identifiers vs FASTA.
    if fasta is not None and len(fasta) > 0:
        _run_check(report, lambda: check_protein_ids(standard_df, fasta, config), "protein_ids")
    else:
        report.add_info(
            "no_fasta_reference",
            "No reference FASTA was available; protein-identifier validation was skipped.",
            "protein_ids",
        )

    # Parameter-dependent checks.
    if parameters is None:
        report.add_warning(
            "no_parameters",
            "No parsed parameters were provided; parameter-based validation was skipped.",
            "parameters",
        )
    else:
        _run_check(report, lambda: check_charge_range(standard_df, parameters, config), "charge_range")
        _run_check(report, lambda: check_peptide_length(standard_df, parameters, config), "peptide_length")
        _run_check(report, lambda: check_enzyme(standard_df, parameters, config), "enzyme")
        _run_check(report, lambda: check_modifications(standard_df, parameters, config), "modifications")
        _run_check(
            report,
            lambda: check_run_consistency(standard_df, parameters, input_format, config),
            "run_consistency",
        )

    return report


def _run_check(report: ValidationReport, check_callable, check_name: str) -> None:
    """
    Run a single check and absorb unexpected failures as warnings.

    Parameters
    ----------
    report : ValidationReport
        The report to extend with the check's issues.
    check_callable : callable
        A zero-argument callable returning a list of issues.
    check_name : str
        Name of the check, used in the fallback warning.
    """
    try:
        report.extend(check_callable())
    except Exception as exc:  # noqa: BLE001 - validation must never crash the flow
        report.add_warning(
            "check_failed",
            f"The '{check_name}' validation check could not be completed ({type(exc).__name__}: {exc}).",
            check_name,
        )
