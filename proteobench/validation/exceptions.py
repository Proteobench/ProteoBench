"""
Exceptions for the ProteoBench submission-validation layer.

The validation layer primarily communicates through a structured
:class:`proteobench.validation.report.ValidationReport`. This exception is a
thin convenience for callers (notebooks, CLI, programmatic submission) that
prefer to fail fast instead of inspecting the report.

Classes
-------
SubmissionValidationError
    Raised when a submission fails validation with at least one error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from proteobench.validation.report import ValidationReport


class SubmissionValidationError(Exception):
    """
    Raised when a submission fails validation.

    The originating :class:`~proteobench.validation.report.ValidationReport`
    is attached as the ``report`` attribute so callers can inspect every issue.

    Parameters
    ----------
    report : ValidationReport
        The validation report that triggered the error.
    """

    def __init__(self, report: "ValidationReport"):
        self.report = report
        n_errors = len(report.errors)
        message = f"Submission validation failed with {n_errors} error(s):\n{report.summary()}"
        super().__init__(message)
