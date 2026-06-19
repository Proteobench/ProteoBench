"""
Submission-validation layer for ProteoBench.

This package validates uploaded benchmark submissions before a public datapoint
is created. It checks that the standardized results and parsed parameters are
internally consistent and consistent with the module reference database, and
returns a structured :class:`ValidationReport` (overall status plus per-issue
severity, machine-readable code, message, field, observed/expected values, and
example offending rows).

The layer is generic and registry-driven. Each module maps to a *validation
profile* (a named, ordered set of checks). Adding a new module of an existing
category requires only configuration; adding a new category requires only
registering a new profile via :func:`register_profile`.

Typical use::

    from proteobench.validation import validate_submission, FastaReference, ModuleValidationConfig

    config = ModuleValidationConfig.from_parse_settings(parse_settings_dir, module_id, input_format)
    fasta = FastaReference.from_url(config.fasta_url, member_filename=config.fasta_filename)
    report = validate_submission(standard_df, parameters=params, fasta=fasta, config=config,
                                 input_format=input_format)
    if report.has_errors:
        ...  # block public submission

Registering a custom profile::

    from proteobench.validation import Check, ValidationProfile, register_profile

    register_profile(ValidationProfile(
        name="my_module",
        checks=[Check("my_check", my_check_func, "what it does")],
    ))
"""

from proteobench.validation.config import ModuleValidationConfig
from proteobench.validation.context import ValidationContext
from proteobench.validation.exceptions import SubmissionValidationError
from proteobench.validation.fasta import FastaReference
from proteobench.validation.profiles import (
    Check,
    ValidationProfile,
    available_profiles,
    get_profile,
    register_profile,
    unregister_profile,
)
from proteobench.validation.report import Severity, ValidationIssue, ValidationReport
from proteobench.validation.validator import validate_submission

__all__ = [
    "validate_submission",
    "ValidationReport",
    "ValidationIssue",
    "Severity",
    "ValidationContext",
    "FastaReference",
    "ModuleValidationConfig",
    "SubmissionValidationError",
    "Check",
    "ValidationProfile",
    "register_profile",
    "unregister_profile",
    "get_profile",
    "available_profiles",
]
