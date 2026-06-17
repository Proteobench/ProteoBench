"""
Streamlit glue for the submission-validation layer.

This module bridges the framework-agnostic core validator
(:mod:`proteobench.validation`) and the Streamlit submission flow. It:

* re-derives the standardized result DataFrame from the already-parsed input
  DataFrame by reusing the existing parser (no duplicated tool logic);
* downloads and caches the module reference FASTA;
* runs :func:`proteobench.validation.validate_submission`;
* renders the resulting report in a curator- and user-friendly way.

All network access and Streamlit calls live here, keeping the core validation
library free of UI and I/O dependencies.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import streamlit as st

from proteobench.io.parsing.convert_to_intermediate import ParseSettingsBuilder
from proteobench.validation import (
    FastaReference,
    ModuleValidationConfig,
    Severity,
    ValidationReport,
    validate_submission,
)


@st.cache_data(show_spinner="Downloading reference FASTA for validation ...")
def _load_fasta_reference(fasta_url: str, fasta_filename: Optional[str]) -> FastaReference:
    """
    Download and parse the module reference FASTA (cached).

    Parameters
    ----------
    fasta_url : str
        URL of the reference FASTA / zip / gzip resource.
    fasta_filename : str, optional
        Preferred FASTA member name when the resource is an archive.

    Returns
    -------
    FastaReference
        Reference protein identifiers.
    """
    return FastaReference.from_url(fasta_url, member_filename=fasta_filename)


def _build_standard_dataframe(ionmodule: Any, input_format: str, input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Re-derive the standardized result DataFrame by reusing the module parser.

    Parameters
    ----------
    ionmodule : Any
        The benchmarking module instance (provides ``parse_settings_dir`` and ``module_id``).
    input_format : str
        The selected software tool.
    input_df : pandas.DataFrame
        The raw parsed tool output (as stored in session state).

    Returns
    -------
    pandas.DataFrame
        The standardized result DataFrame.
    """
    parser = ParseSettingsBuilder(
        parse_settings_dir=ionmodule.parse_settings_dir,
        module_id=ionmodule.module_id,
    ).build_parser(input_format)
    standard_df, _ = parser.convert_to_standard_format(input_df)
    return standard_df


def _resolve_input_df(variables):
    """
    Fetch the parsed input DataFrame from session state for validation.

    Parameters
    ----------
    variables : Any
        The module's ``Variables`` dataclass instance (session-state keys).

    Returns
    -------
    pandas.DataFrame or None
        The submission input DataFrame, or ``None`` if unavailable.
    """
    input_df = st.session_state.get(variables.input_df_submission)
    if input_df is None:
        input_df = st.session_state.get(variables.input_df)
    return input_df


def _build_config(ionmodule, input_format: str) -> ModuleValidationConfig:
    """
    Build the module validation config, falling back to defaults on failure.

    Parameters
    ----------
    ionmodule : Any
        The benchmarking module instance.
    input_format : str
        The selected software tool.

    Returns
    -------
    ModuleValidationConfig
        The resolved configuration (never raises).
    """
    try:
        return ModuleValidationConfig.from_parse_settings(
            parse_settings_dir=ionmodule.parse_settings_dir,
            module_id=ionmodule.module_id,
            input_format=input_format,
        )
    except Exception:  # noqa: BLE001
        return ModuleValidationConfig()


def _acquire_fasta(config: ModuleValidationConfig, report: ValidationReport):
    """
    Obtain the reference FASTA, degrading to a report message on any problem.

    Parameters
    ----------
    config : ModuleValidationConfig
        The module configuration (provides ``fasta_url`` / ``fasta_filename``).
    report : ValidationReport
        Report to which a warning/info is added when no FASTA is available.

    Returns
    -------
    FastaReference or None
        The reference, or ``None`` when not configured or not downloadable.
    """
    if not config.fasta_url:
        report.add_info(
            "no_fasta_configured",
            "No reference FASTA is configured for this module ([reference_database] in "
            "module_settings.toml); protein-identifier validation was skipped.",
            "protein_ids",
        )
        return None
    try:
        return _load_fasta_reference(config.fasta_url, config.fasta_filename)
    except Exception as exc:  # noqa: BLE001
        report.add_warning(
            "fasta_unavailable",
            f"Could not download or parse the reference FASTA ({type(exc).__name__}: {exc}); "
            "protein-identifier validation was skipped.",
            "protein_ids",
            field=config.fasta_url,
        )
        return None


def run_submission_validation(variables, ionmodule, user_input, params) -> ValidationReport:
    """
    Validate a submission and return the structured report.

    Designed to be fault-tolerant: any infrastructure problem (missing input,
    parser failure, FASTA download failure) is converted into a warning so that
    validation never crashes the submission flow. Only genuine consistency
    problems produce errors.

    Parameters
    ----------
    variables : Any
        The module's ``Variables`` dataclass instance (session-state keys).
    ionmodule : Any
        The benchmarking module instance.
    user_input : dict
        The submission's user input (provides ``"input_format"``).
    params : Any
        The parsed/edited :class:`ProteoBenchParameters` to be submitted.

    Returns
    -------
    ValidationReport
        The aggregated validation report.
    """
    report = ValidationReport()
    input_format = user_input.get("input_format")

    input_df = _resolve_input_df(variables)
    if input_df is None:
        report.add_warning(
            "no_input_dataframe",
            "Could not run submission validation because the parsed result data was not available in the session.",
            "input",
        )
        return report

    # Re-derive the standardized DataFrame (reuses existing parsing; no duplication).
    try:
        standard_df = _build_standard_dataframe(ionmodule, input_format, input_df)
    except Exception as exc:  # noqa: BLE001 - never block submission on a validation infra error
        report.add_warning(
            "standardization_failed",
            f"Could not re-standardize the results for validation ({type(exc).__name__}: {exc}); "
            "protein/charge/length checks were skipped.",
            "input",
        )
        return report

    config = _build_config(ionmodule, input_format)
    fasta = _acquire_fasta(config, report)

    try:
        core_report = validate_submission(
            standard_df,
            parameters=params,
            fasta=fasta,
            config=config,
            input_format=input_format,
        )
        report.extend(core_report.issues)
    except Exception as exc:  # noqa: BLE001 - never block submission on a validation infra error
        report.add_warning(
            "validation_failed",
            f"Submission validation could not be completed ({type(exc).__name__}: {exc}); "
            "no automated consistency checks were applied.",
            "input",
        )
    return report


def _render_issue(issue) -> None:
    """
    Render a single validation issue with its details.

    Parameters
    ----------
    issue : ValidationIssue
        The issue to render.
    """
    header = f"**{issue.message}**"
    if issue.severity == Severity.ERROR:
        st.error(header, icon="🚫")
    elif issue.severity == Severity.WARNING:
        st.warning(header, icon="⚠️")
    else:
        st.info(header, icon="ℹ️")

    details = []
    if issue.expected is not None:
        details.append(f"- Expected: `{issue.expected}`")
    if issue.observed is not None:
        details.append(f"- Observed: `{issue.observed}`")
    if issue.examples:
        shown = ", ".join(f"`{e}`" for e in issue.examples)
        details.append(f"- Examples: {shown}")
    if details:
        st.markdown("\n".join(details))


def render_validation_report(report: ValidationReport) -> None:
    """
    Render a full validation report in the Streamlit UI.

    The checks never block submission; the report is shown so the submitter can
    review the findings, which are also included in the pull-request description.

    Parameters
    ----------
    report : ValidationReport
        The report to display.
    """
    n_flagged = len(report.errors) + len(report.warnings)
    n_info = len(report.infos)

    st.subheader("Submission checks")
    if n_flagged == 0:
        st.success("All automated submission checks passed.", icon="✅")
    else:
        st.info(
            f"We flagged {n_flagged} point(s) to review below. You can still submit your results, and "
            "these notes will be included in the pull request for the reviewers.",
            icon="📝",
        )

    for issue in report.errors:
        _render_issue(issue)
    for issue in report.warnings:
        _render_issue(issue)

    if report.infos:
        with st.expander(f"More details ({n_info})"):
            for issue in report.infos:
                _render_issue(issue)
