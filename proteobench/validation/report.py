"""
Structured validation report objects for ProteoBench submission validation.

This module defines the data model returned by the validation layer
(:func:`proteobench.validation.validator.validate_submission`). The report is a
plain, framework-agnostic container so that it can be produced in the core
library and rendered by any front end (Streamlit, notebooks, CLI).

Classes
-------
Severity
    Enumeration of issue severities (error, warning, info).
ValidationIssue
    A single machine- and human-readable validation finding.
ValidationReport
    A collection of issues with overall pass/fail helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """
    Severity level of a validation issue.

    ``ERROR`` issues block public submission; ``WARNING`` and ``INFO`` issues
    do not.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """
    A single validation finding.

    Parameters
    ----------
    code : str
        Machine-readable issue code (stable identifier, e.g. ``"protein_not_in_fasta"``).
    severity : Severity
        Severity of the issue.
    message : str
        Human-readable description of the issue.
    check : str
        Name of the check that produced the issue (e.g. ``"protein_ids"``).
    field : str, optional
        Relevant field, file, or column name the issue refers to.
    observed : Any, optional
        Observed value (or a short summary of it).
    expected : Any, optional
        Expected value or allowed range, where applicable.
    examples : list, optional
        A small number of example offending rows or identifiers.
    """

    code: str
    severity: Severity
    message: str
    check: str
    field: Optional[str] = None
    observed: Any = None
    expected: Any = None
    examples: List[Any] = dc_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the issue to a JSON-serialisable dictionary.

        Returns
        -------
        dict
            Dictionary representation of the issue.
        """
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "check": self.check,
            "field": self.field,
            "observed": self.observed,
            "expected": self.expected,
            "examples": list(self.examples),
        }


@dataclass
class ValidationReport:
    """
    Collection of validation issues with overall status helpers.

    Parameters
    ----------
    issues : list of ValidationIssue, optional
        Issues collected during validation.
    """

    issues: List[ValidationIssue] = dc_field(default_factory=list)

    def add(
        self,
        code: str,
        severity: Severity,
        message: str,
        check: str,
        field: Optional[str] = None,
        observed: Any = None,
        expected: Any = None,
        examples: Optional[List[Any]] = None,
    ) -> "ValidationReport":
        """
        Append a new issue to the report.

        Parameters
        ----------
        code : str
            Machine-readable issue code.
        severity : Severity
            Severity of the issue.
        message : str
            Human-readable description.
        check : str
            Name of the originating check.
        field : str, optional
            Relevant field, file, or column name.
        observed : Any, optional
            Observed value.
        expected : Any, optional
            Expected value or allowed range.
        examples : list, optional
            Example offending rows or identifiers.

        Returns
        -------
        ValidationReport
            The report itself, to allow chaining.
        """
        self.issues.append(
            ValidationIssue(
                code=code,
                severity=severity,
                message=message,
                check=check,
                field=field,
                observed=observed,
                expected=expected,
                examples=list(examples) if examples else [],
            )
        )
        return self

    def add_error(self, code: str, message: str, check: str, **kwargs: Any) -> "ValidationReport":
        """
        Append an ``ERROR`` issue.

        Parameters
        ----------
        code : str
            Machine-readable issue code.
        message : str
            Human-readable description.
        check : str
            Name of the originating check.
        **kwargs : dict
            Optional ``field``, ``observed``, ``expected``, and ``examples`` values.

        Returns
        -------
        ValidationReport
            The report itself, to allow chaining.
        """
        return self.add(code, Severity.ERROR, message, check, **kwargs)

    def add_warning(self, code: str, message: str, check: str, **kwargs: Any) -> "ValidationReport":
        """
        Append a ``WARNING`` issue.

        Parameters
        ----------
        code : str
            Machine-readable issue code.
        message : str
            Human-readable description.
        check : str
            Name of the originating check.
        **kwargs : dict
            Optional ``field``, ``observed``, ``expected``, and ``examples`` values.

        Returns
        -------
        ValidationReport
            The report itself, to allow chaining.
        """
        return self.add(code, Severity.WARNING, message, check, **kwargs)

    def add_info(self, code: str, message: str, check: str, **kwargs: Any) -> "ValidationReport":
        """
        Append an ``INFO`` issue.

        Parameters
        ----------
        code : str
            Machine-readable issue code.
        message : str
            Human-readable description.
        check : str
            Name of the originating check.
        **kwargs : dict
            Optional ``field``, ``observed``, ``expected``, and ``examples`` values.

        Returns
        -------
        ValidationReport
            The report itself, to allow chaining.
        """
        return self.add(code, Severity.INFO, message, check, **kwargs)

    def extend(self, issues: List[ValidationIssue]) -> "ValidationReport":
        """
        Append several issues at once.

        Parameters
        ----------
        issues : list of ValidationIssue
            Issues to add.

        Returns
        -------
        ValidationReport
            The report itself, to allow chaining.
        """
        self.issues.extend(issues)
        return self

    @property
    def errors(self) -> List[ValidationIssue]:
        """
        Return all ``ERROR`` issues.

        Returns
        -------
        list of ValidationIssue
            The error-level issues.
        """
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """
        Return all ``WARNING`` issues.

        Returns
        -------
        list of ValidationIssue
            The warning-level issues.
        """
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
        """
        Return all ``INFO`` issues.

        Returns
        -------
        list of ValidationIssue
            The info-level issues.
        """
        return [i for i in self.issues if i.severity == Severity.INFO]

    @property
    def has_errors(self) -> bool:
        """
        Whether the report contains any ``ERROR`` issue.

        Returns
        -------
        bool
            ``True`` if at least one error is present.
        """
        return any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def passed(self) -> bool:
        """
        Overall pass status (no ``ERROR`` issues).

        Returns
        -------
        bool
            ``True`` when the submission may proceed (warnings allowed).
        """
        return not self.has_errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the report to a JSON-serialisable dictionary.

        Returns
        -------
        dict
            Dictionary with overall status and the list of issues.
        """
        return {
            "passed": self.passed,
            "n_errors": len(self.errors),
            "n_warnings": len(self.warnings),
            "n_infos": len(self.infos),
            "issues": [i.to_dict() for i in self.issues],
        }

    def summary(self, include_info: bool = False) -> str:
        """
        Build a compact Markdown summary of the report.

        Useful for embedding warnings into pull-request text or logs.

        Parameters
        ----------
        include_info : bool, optional
            Whether to include ``INFO`` issues in the summary. Default ``False``.

        Returns
        -------
        str
            Markdown-formatted summary.
        """
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"### Submission validation: {status}",
            f"- Errors: {len(self.errors)}, Warnings: {len(self.warnings)}, Info: {len(self.infos)}",
        ]

        selected = list(self.errors) + list(self.warnings)
        if include_info:
            selected += list(self.infos)

        for issue in selected:
            line = f"- **[{issue.severity.value}]** ({issue.code}) {issue.message}"
            if issue.examples:
                shown = ", ".join(str(e) for e in issue.examples[:5])
                line += f" Examples: {shown}"
            lines.append(line)

        return "\n".join(lines)

    def raise_if_errors(self) -> None:
        """
        Raise :class:`SubmissionValidationError` if any error issue is present.

        Raises
        ------
        SubmissionValidationError
            If the report contains at least one ``ERROR`` issue.
        """
        if self.has_errors:
            from proteobench.validation.exceptions import SubmissionValidationError

            raise SubmissionValidationError(self)
