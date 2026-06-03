"""
Validation checks, profiles, and the profile registry.

This module is the extensibility surface of the validation layer. It models
validation as two composable pieces:

* a :class:`Check` wraps a single ``ctx -> list[ValidationIssue]`` function with
  a stable name and description;
* a :class:`ValidationProfile` is an ordered list of checks that applies to one
  category of module.

Profiles are looked up by name in a module-level registry. A module declares
which profile it uses (via ``[validation].profile`` in ``module_settings.toml``,
or by inference from its parser class); the orchestrator then runs that
profile's checks. Adding a new module of an existing category requires no code.
Adding a genuinely new category requires only registering a new profile here (or
from third-party code via :func:`register_profile`), without touching the
orchestrator.

Checks are reusable across profiles: for example ``run_consistency`` is shared
by both the quant and de novo profiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from proteobench.validation.checks import (
    check_charge_range,
    check_enzyme,
    check_fdr_psm,
    check_mass_tolerances,
    check_max_modifications,
    check_modifications,
    check_peptide_length,
    check_protein_ids,
    check_run_consistency,
)
from proteobench.validation.context import ValidationContext
from proteobench.validation.report import ValidationIssue, ValidationReport

#: Type alias for a check function: takes a context, returns a list of issues.
CheckFunc = Callable[[ValidationContext], List[ValidationIssue]]


@dataclass
class Check:
    """
    A single, named validation check.

    Attributes
    ----------
    name : str
        Stable identifier used in fallback error messages and progress display.
    func : callable
        A function ``ctx -> list[ValidationIssue]``.
    description : str, optional
        Human-readable description of what the check verifies.
    """

    name: str
    func: CheckFunc
    description: str = ""

    def run(self, ctx: ValidationContext) -> List[ValidationIssue]:
        """
        Execute the check against a validation context.

        Parameters
        ----------
        ctx : ValidationContext
            The inputs available to the check.

        Returns
        -------
        list of ValidationIssue
            Issues produced by the check (possibly empty).
        """
        return self.func(ctx)


@dataclass
class ValidationProfile:
    """
    An ordered set of checks that applies to one category of module.

    Attributes
    ----------
    name : str
        Unique profile name (the routing key declared by modules).
    checks : list of Check
        Checks to run, in order.
    description : str, optional
        Human-readable description of the profile.
    """

    name: str
    checks: List[Check] = field(default_factory=list)
    description: str = ""

    @property
    def check_names(self) -> List[str]:
        """
        Return the names of the checks in this profile.

        Returns
        -------
        list of str
            The ordered check names.
        """
        return [check.name for check in self.checks]


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

_PROFILES: Dict[str, ValidationProfile] = {}


def register_profile(profile: ValidationProfile, overwrite: bool = False) -> None:
    """
    Register a validation profile under its name.

    Parameters
    ----------
    profile : ValidationProfile
        The profile to register.
    overwrite : bool, optional
        If ``False`` (default), registering a name that already exists raises.
        Set ``True`` to replace an existing profile.

    Raises
    ------
    ValueError
        If a profile with the same name is already registered and
        ``overwrite`` is ``False``.
    """
    if profile.name in _PROFILES and not overwrite:
        raise ValueError(
            f"A validation profile named '{profile.name}' is already registered. " "Pass overwrite=True to replace it."
        )
    _PROFILES[profile.name] = profile


def unregister_profile(name: str) -> None:
    """
    Remove a profile from the registry if present.

    Parameters
    ----------
    name : str
        Name of the profile to remove.
    """
    _PROFILES.pop(name, None)


def get_profile(name: str) -> Optional[ValidationProfile]:
    """
    Look up a registered profile by name.

    Parameters
    ----------
    name : str
        Profile name.

    Returns
    -------
    ValidationProfile or None
        The registered profile, or ``None`` if no profile has that name (or if
        ``name`` is not a string).
    """
    if not isinstance(name, str):
        return None
    return _PROFILES.get(name)


def available_profiles() -> List[str]:
    """
    List the names of all registered profiles.

    Returns
    -------
    list of str
        Sorted profile names.
    """
    return sorted(_PROFILES)


# --------------------------------------------------------------------------- #
# Check adapters
#
# Trivial pass-throughs that simply forward context fields to the underlying
# pure check functions in ``checks.py`` are defined inline as lambdas in the
# profile definitions below. Checks that need extra orchestration logic (such
# as deciding whether a reference is available) are defined as named functions
# here.
# --------------------------------------------------------------------------- #


def _protein_ids_check(ctx: ValidationContext) -> List[ValidationIssue]:
    """
    Validate protein identifiers against the reference FASTA, if available.

    Parameters
    ----------
    ctx : ValidationContext
        The validation context (uses ``fasta``, ``standard_df``, ``config``).

    Returns
    -------
    list of ValidationIssue
        Protein-ID issues, or an info message if no FASTA reference is available.
    """
    if ctx.fasta is not None and len(ctx.fasta) > 0:
        return check_protein_ids(ctx.standard_df, ctx.fasta, ctx.config)
    report = ValidationReport()
    report.add_info(
        "no_fasta_reference",
        "No reference FASTA was available; protein-identifier validation was skipped.",
        "protein_ids",
    )
    return report.issues


def _denovo_pending_check(ctx: ValidationContext) -> List[ValidationIssue]:
    """
    Emit an informational notice that de novo checks are not yet implemented.

    Parameters
    ----------
    ctx : ValidationContext
        The validation context (unused; present for the uniform signature).

    Returns
    -------
    list of ValidationIssue
        A single info issue.
    """
    report = ValidationReport()
    report.add_info(
        "denovo_validation_pending",
        "De novo content checks are not yet implemented. Quant checks (protein IDs, charge, "
        "peptide length) do not apply to this module type. Implement de novo checks and add "
        "them to the 'denovo' profile in proteobench/validation/profiles.py.",
        "input",
    )
    return report.issues


# --------------------------------------------------------------------------- #
# Built-in profiles
# --------------------------------------------------------------------------- #

QUANT_LFQ_PROFILE = ValidationProfile(
    name="quant_lfq",
    description="LFQ quantification modules (HYE/PYE): protein IDs, charge, peptide length, enzyme, mods.",
    checks=[
        Check("protein_ids", _protein_ids_check, "Protein identifiers present in the reference FASTA."),
        Check(
            "charge_range",
            lambda ctx: check_charge_range(ctx.standard_df, ctx.parameters, ctx.config),
            "Precursor charges within the searched charge range.",
        ),
        Check(
            "peptide_length",
            lambda ctx: check_peptide_length(ctx.standard_df, ctx.parameters, ctx.config),
            "Peptide lengths within the searched length range.",
        ),
        Check(
            "enzyme",
            lambda ctx: check_enzyme(ctx.standard_df, ctx.parameters, ctx.config),
            "Trypsin-family missed-cleavage heuristic (warning only).",
        ),
        Check(
            "modifications",
            lambda ctx: check_modifications(ctx.standard_df, ctx.parameters, ctx.config),
            "Observed modifications declared in the parameter file (warning only).",
        ),
        Check(
            "max_modifications",
            lambda ctx: check_max_modifications(ctx.standard_df, ctx.parameters, ctx.config),
            "Number of modifications per peptidoform within max_mods (warning only).",
        ),
        Check(
            "mass_tolerances",
            lambda ctx: check_mass_tolerances(ctx.standard_df, ctx.parameters, ctx.config),
            "Precursor/fragment mass tolerances are present and plausible (warning only).",
        ),
        Check(
            "fdr_psm",
            lambda ctx: check_fdr_psm(ctx.standard_df, ctx.parameters, ctx.config),
            "PSM-level FDR within the valid range and recommended maximum (warning only).",
        ),
        Check(
            "run_consistency",
            lambda ctx: check_run_consistency(ctx.standard_df, ctx.parameters, ctx.input_format, ctx.config),
            "Parameter file matches the submitted run (software identity).",
        ),
    ],
)

DENOVO_PROFILE = ValidationProfile(
    name="denovo",
    description="De novo sequencing modules. Reuses run-consistency; content checks are pending.",
    checks=[
        Check(
            "run_consistency",
            lambda ctx: check_run_consistency(ctx.standard_df, ctx.parameters, ctx.input_format, ctx.config),
            "Parameter file matches the submitted run (software identity).",
        ),
        Check("denovo_pending", _denovo_pending_check, "Placeholder for future de novo content checks."),
    ],
)

register_profile(QUANT_LFQ_PROFILE, overwrite=True)
register_profile(DENOVO_PROFILE, overwrite=True)
