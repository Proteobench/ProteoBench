"""
Central submission-validation API.

:func:`validate_submission` resolves the module's validation profile, builds a
:class:`~proteobench.validation.context.ValidationContext`, and runs the
profile's checks, returning a single structured
:class:`~proteobench.validation.report.ValidationReport`. The caller decides
what to do with the report (typically: block public submission when
``report.has_errors`` is true, but allow it through with warnings).

The orchestrator is generic: it does not know about any particular module type.
Which checks run is determined entirely by the resolved profile
(:mod:`proteobench.validation.profiles`). Adding a new module of an existing
category needs no code; adding a new category needs only a new registered
profile.

The function is framework-agnostic and performs no I/O: any reference data (a
FASTA, a ground-truth table) is supplied via the arguments / context. Front ends
are responsible for obtaining the standardized DataFrame and the reference.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from proteobench.validation.config import ModuleValidationConfig
from proteobench.validation.context import ValidationContext
from proteobench.validation.fasta import FastaReference
from proteobench.validation.profiles import Check, available_profiles, get_profile
from proteobench.validation.report import ValidationReport


def validate_submission(
    standard_df: pd.DataFrame,
    parameters: Any = None,
    fasta: Optional[FastaReference] = None,
    config: Optional[ModuleValidationConfig] = None,
    input_format: Optional[str] = None,
    profile: Optional[str] = None,
) -> ValidationReport:
    """
    Validate a benchmark submission and return a structured report.

    The set of checks run is determined by the validation profile, resolved from
    (in order): the explicit ``profile`` argument, ``config.validation_profile``,
    or the default. Each check is fault-tolerant: a check that raises an
    unexpected exception is converted to a warning so that validation itself
    never crashes the submission flow.

    Parameters
    ----------
    standard_df : pandas.DataFrame
        The standardized result DataFrame produced by the module parser.
    parameters : Any, optional
        Parsed parameters (a :class:`ProteoBenchParameters` or any object with
        the same attributes). Parameter-dependent checks degrade to warnings
        when values are missing.
    fasta : FastaReference, optional
        Reference protein identifiers, for profiles that validate against a
        sequence database.
    config : ModuleValidationConfig, optional
        Module validation configuration. Defaults to a generic configuration
        (which selects the default profile).
    input_format : str, optional
        The selected software tool, used for run-consistency checks.
    profile : str, optional
        Explicit profile name, overriding ``config.validation_profile``. Mostly
        useful for testing.

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

    profile_name = profile or config.validation_profile
    profile_obj = get_profile(profile_name)

    if profile_obj is None:
        report.add_warning(
            "unknown_validation_profile",
            f"No validation profile named '{profile_name}' is registered "
            f"(available: {available_profiles()}); no checks were run.",
            "input",
        )
        return report

    ctx = ValidationContext(
        standard_df=standard_df,
        parameters=parameters,
        config=config,
        fasta=fasta,
        input_format=input_format,
        reference=fasta,
    )

    for check in profile_obj.checks:
        _run_check(report, check, ctx)

    return report


def _run_check(report: ValidationReport, check: Check, ctx: ValidationContext) -> None:
    """
    Run a single check and absorb unexpected failures as warnings.

    Parameters
    ----------
    report : ValidationReport
        The report to extend with the check's issues.
    check : Check
        The check to run.
    ctx : ValidationContext
        The validation context passed to the check.
    """
    try:
        report.extend(check.run(ctx))
    except Exception as exc:  # noqa: BLE001 - validation must never crash the flow
        report.add_warning(
            "check_failed",
            f"The '{check.name}' validation check could not be completed ({type(exc).__name__}: {exc}).",
            check.name,
        )
