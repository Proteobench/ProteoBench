"""
Individual validation checks operating on the standardized result DataFrame.

Every check is a pure function that takes the standardized DataFrame, the
parsed :class:`~proteobench.io.params.ProteoBenchParameters` (or any object with
the same attributes), and a :class:`~proteobench.validation.config.ModuleValidationConfig`,
and returns a list of :class:`~proteobench.validation.report.ValidationIssue`.

The checks are deliberately generic: they read the standardized columns
(``Proteins``, ``Sequence``, ``Charge``, ``proforma``) and the parameter
attributes, never tool-specific result columns. Missing or unparsed parameters
yield warnings rather than errors, so a submission is never blocked merely
because a value could not be parsed.

Documented limitations and intentionally skipped checks:

* **Enzyme specificity**: a missed-cleavage heuristic is implemented for common
  C-terminal cleaving enzymes (trypsin, trypsin/P, Lys-C, Arg-C, Glu-C,
  chymotrypsin) and only as a *warning*. It ignores protein N-/C-termini and
  ragged ends (resolving those would need the reference protein sequences), and
  N-terminal cleavers (Asp-N, Lys-N) are skipped.
* **Modifications**: cross-tool modification representations are not normalized
  (human-readable names, UniMod accessions, and raw masses all occur). Only
  human-readable modification names observed in the ``proforma`` column are
  compared, as warnings; mass-only / UniMod-only tokens are skipped. The
  maximum-modifications count includes any fixed modifications written into the
  sequence, so it is an upper bound (warning only).
* **Mass tolerances**: there is no per-result tolerance to compare against, so
  the precursor/fragment tolerances are only sanity-checked (present, numeric,
  positive, within a plausible range), as warnings.
* **PSM FDR**: validated against the valid ``[0, 1]`` range and the benchmark's
  recommended maximum (configurable), as warnings.
* **Run identity**: ``ProteoBenchParameters`` does not expose raw-file, sample,
  or experiment identifiers, so result-vs-parameter run matching is limited to
  software identity. This is reported as info.
"""

from __future__ import annotations

import re
from typing import Any, List, Optional

import numpy as np
import pandas as pd

from proteobench.validation.config import ModuleValidationConfig
from proteobench.validation.fasta import FastaReference
from proteobench.validation.protein_ids import extract_identifiers, is_decoy_or_contaminant, split_protein_groups
from proteobench.validation.report import ValidationIssue, ValidationReport

#: Maximum number of example offending protein identifiers to report.
MAX_PROTEIN_EXAMPLES = 20

#: Maximum number of example offending rows to report for other checks.
MAX_ROW_EXAMPLES = 10

#: Matches a bracketed modification label inside a ProForma string.
_PROFORMA_MOD = re.compile(r"\[([^\]]+)\]")

#: C-terminal cleavage rules per normalized enzyme name: a tuple of
#: (residues the enzyme cleaves after, whether it cleaves when proline follows).
#: A value of ``None`` marks an N-terminal cleaver, for which the simple
#: internal-site count does not apply (skipped with an info message).
#: The rules follow the MaxQuant built-in enzyme defaults (e.g. Glu-C cleaves
#: after D and E). Because the missed-cleavage check is warning-only, these are
#: convention-dependent heuristics, not authoritative cleavage definitions.
_ENZYME_CLEAVAGE_RULES = {
    "trypsin": ("KR", False),
    "trypsin/p": ("KR", True),
    "lysc": ("K", True),
    "argc": ("R", False),
    "gluc": ("DE", True),
    "chymotrypsin": ("FYWL", False),
    "lysn": None,
    "aspn": None,
}

#: Plausibility ceilings for mass-tolerance sanity checks.
_MAX_PLAUSIBLE_PPM = 1000.0
_MAX_PLAUSIBLE_DALTON = 10.0

#: Matches a signed number (including scientific notation) and an optional unit
#: in a tolerance string such as ``"[-20.0 ppm, 20.0 ppm]"`` or ``"2e-3 Da"``.
_TOLERANCE_TOKEN = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(ppm|da|th|mmu|amu)?", re.IGNORECASE)


def _normalize_enzyme(name: str) -> str:
    """
    Normalize an enzyme name for cleavage-rule lookup.

    Lower-cases the name and removes spaces, underscores, and hyphens so that
    ``"Lys-C"``, ``"lys_c"``, and ``"LysC"`` all map to ``"lysc"`` (the slash in
    ``"Trypsin/P"`` is preserved).

    Parameters
    ----------
    name : str
        The raw enzyme name.

    Returns
    -------
    str
        The normalized enzyme key.
    """
    text = str(name).strip().lower()
    for char in (" ", "_", "-"):
        text = text.replace(char, "")
    return text


def _is_missing(value: Any) -> bool:
    """
    Determine whether a parameter value should be treated as "not provided".

    Treats ``None``, ``np.nan``, and the literal strings ``"None"``/``"nan"``/``""``
    as missing (matching how :class:`ProteoBenchParameters` represents absent values).

    Parameters
    ----------
    value : Any
        The value to test.

    Returns
    -------
    bool
        ``True`` if the value is missing.
    """
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "none", "nan"}:
        return True
    return False


def _as_int(value: Any) -> Optional[int]:
    """
    Coerce a value to ``int`` if possible.

    Parameters
    ----------
    value : Any
        The value to coerce.

    Returns
    -------
    int or None
        The integer value, or ``None`` if it is missing or not convertible.
    """
    if _is_missing(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> Optional[float]:
    """
    Coerce a value to ``float`` if possible.

    Parameters
    ----------
    value : Any
        The value to coerce.

    Returns
    -------
    float or None
        The float value, or ``None`` if it is missing or not convertible.
    """
    if _is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_range(minimum: Optional[int], maximum: Optional[int]) -> str:
    """
    Format an inclusive numeric range for display.

    Parameters
    ----------
    minimum : int or None
        Lower bound (``None`` means unbounded).
    maximum : int or None
        Upper bound (``None`` means unbounded).

    Returns
    -------
    str
        A string such as ``"[2, 4]"`` or ``"[2, unbounded]"``.
    """
    low = "unbounded" if minimum is None else str(minimum)
    high = "unbounded" if maximum is None else str(maximum)
    return f"[{low}, {high}]"


def _identifier_series(df: pd.DataFrame, config: ModuleValidationConfig) -> Optional[pd.Series]:
    """
    Pick the best per-row identifier column for example reporting.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    pandas.Series or None
        A series of human-readable row identifiers, or ``None`` if unavailable.
    """
    for column in ("precursor ion", "peptidoform", config.sequence_column):
        if column in df.columns:
            return df[column].astype(str)
    return None


def check_protein_ids(
    df: pd.DataFrame,
    fasta: FastaReference,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Validate protein identifiers against the reference FASTA accession set.

    Splits protein groups, skips decoy and contaminant identifiers, and reports
    as an error any remaining identifier that is not found in the reference.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    fasta : FastaReference
        Reference protein identifiers.
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Issues describing missing protein identifiers (or an info confirming all
        identifiers were found).
    """
    report = ValidationReport()

    if config.protein_column not in df.columns:
        report.add_warning(
            "protein_column_missing",
            f"Protein column '{config.protein_column}' not found in the standardized results; "
            "protein-identifier validation was skipped.",
            "protein_ids",
            field=config.protein_column,
        )
        return report.issues

    # Collect unique, target (non-decoy / non-contaminant) protein tokens.
    target_tokens: set = set()
    for cell in df[config.protein_column].dropna().unique():
        for token in split_protein_groups(cell, config.protein_group_separators):
            if is_decoy_or_contaminant(token, config.contaminant_flag, config.decoy_prefixes):
                continue
            target_tokens.add(token)

    if not target_tokens:
        report.add_warning(
            "no_protein_ids",
            "No target protein identifiers were found in the results (all empty, decoy, or contaminant).",
            "protein_ids",
            field=config.protein_column,
        )
        return report.issues

    missing = [token for token in target_tokens if not fasta.contains_any(extract_identifiers(token))]

    n_unique = len(target_tokens)
    n_missing = len(missing)
    n_found = n_unique - n_missing

    if n_missing > 0:
        examples = sorted(missing)[:MAX_PROTEIN_EXAMPLES]
        report.add_error(
            "protein_not_in_fasta",
            f"{n_missing} of {n_unique} unique protein identifiers are not present in the reference "
            f"database ({n_found} found). These are non-decoy, non-contaminant identifiers and likely "
            "indicate the wrong FASTA was used or proteins outside the benchmark.",
            "protein_ids",
            field=config.protein_column,
            observed={"n_unique": n_unique, "n_found": n_found, "n_missing": n_missing},
            expected="all identifiers present in the module reference database",
            examples=examples,
        )
    else:
        report.add_info(
            "protein_ids_ok",
            f"All {n_unique} unique protein identifiers were found in the reference database.",
            "protein_ids",
            field=config.protein_column,
            observed={"n_unique": n_unique, "n_found": n_found, "n_missing": 0},
        )

    return report.issues


def check_charge_range(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Validate that observed precursor charges fall within the parsed charge range.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    params : Any
        Parsed parameters (object with ``min_precursor_charge`` /
        ``max_precursor_charge`` attributes).
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Issues describing out-of-range charges, or warnings when the constraint
        or column is unavailable.
    """
    report = ValidationReport()
    check = "charge_range"

    min_charge = _as_int(getattr(params, "min_precursor_charge", None))
    max_charge = _as_int(getattr(params, "max_precursor_charge", None))

    if min_charge is None and max_charge is None:
        report.add_warning(
            "charge_range_not_parsed",
            "Could not validate precursor charge because no minimum/maximum charge constraint "
            "was parsed from the parameter file.",
            check,
            field="precursor_charge",
        )
        return report.issues

    if config.charge_column not in df.columns:
        report.add_warning(
            "charge_column_missing",
            f"Charge column '{config.charge_column}' not found in the standardized results; "
            "charge-range validation was skipped.",
            check,
            field=config.charge_column,
        )
        return report.issues

    charges = pd.to_numeric(df[config.charge_column], errors="coerce")
    valid = charges.notna()

    mask = pd.Series(False, index=df.index)
    if min_charge is not None:
        mask = mask | (valid & (charges < min_charge))
    if max_charge is not None:
        mask = mask | (valid & (charges > max_charge))

    n_offending = int(mask.sum())
    if n_offending > 0:
        offending_charges = sorted({int(c) for c in charges[mask].dropna().unique()})
        identifiers = _identifier_series(df, config)
        if identifiers is not None:
            examples = identifiers[mask].unique().tolist()[:MAX_ROW_EXAMPLES]
        else:
            examples = offending_charges[:MAX_ROW_EXAMPLES]
        report.add_error(
            "charge_out_of_range",
            f"{n_offending} result row(s) have a precursor charge outside the searched range "
            f"{_format_range(min_charge, max_charge)} (observed charges: {offending_charges}).",
            check,
            field=config.charge_column,
            observed=offending_charges,
            expected=_format_range(min_charge, max_charge),
            examples=examples,
        )

    return report.issues


def check_peptide_length(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Validate that peptide lengths fall within the parsed peptide-length range.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    params : Any
        Parsed parameters (object with ``min_peptide_length`` /
        ``max_peptide_length`` attributes).
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Issues describing out-of-range peptide lengths, or warnings when the
        constraint or column is unavailable.
    """
    report = ValidationReport()
    check = "peptide_length"

    min_len = _as_int(getattr(params, "min_peptide_length", None))
    max_len = _as_int(getattr(params, "max_peptide_length", None))

    if min_len is None and max_len is None:
        report.add_warning(
            "peptide_length_not_parsed",
            "Could not validate peptide length because no minimum/maximum peptide-length "
            "constraint was parsed from the parameter file.",
            check,
            field="peptide_length",
        )
        return report.issues

    if config.sequence_column not in df.columns:
        report.add_warning(
            "sequence_column_missing",
            f"Sequence column '{config.sequence_column}' not found in the standardized results; "
            "peptide-length validation was skipped.",
            check,
            field=config.sequence_column,
        )
        return report.issues

    sequences = df[config.sequence_column].astype(str)
    lengths = sequences.str.count(r"[A-Za-z]")

    mask = pd.Series(False, index=df.index)
    if min_len is not None:
        mask = mask | (lengths < min_len)
    if max_len is not None:
        mask = mask | (lengths > max_len)

    n_offending = int(mask.sum())
    if n_offending > 0:
        examples = sequences[mask].unique().tolist()[:MAX_ROW_EXAMPLES]
        offending_lengths = sorted({int(length) for length in lengths[mask].unique()})
        report.add_error(
            "peptide_length_out_of_range",
            f"{n_offending} result row(s) have a peptide length outside the searched range "
            f"{_format_range(min_len, max_len)} (observed lengths: {offending_lengths}).",
            check,
            field=config.sequence_column,
            observed=offending_lengths,
            expected=_format_range(min_len, max_len),
            examples=examples,
        )

    return report.issues


def _count_missed_cleavages(sequence: str, residues: str, cleave_before_proline: bool) -> int:
    """
    Count internal missed cleavages for a C-terminal cleaving enzyme.

    A missed cleavage is an internal cleavage residue (one not at the
    C-terminus). For proline-restricted enzymes a cleavage residue immediately
    followed by ``P`` does not count.

    Parameters
    ----------
    sequence : str
        Peptide sequence (plain amino-acid letters).
    residues : str
        Residues the enzyme cleaves C-terminal to (e.g. ``"KR"`` for trypsin).
    cleave_before_proline : bool
        ``True`` if the enzyme still cleaves when proline follows the residue.

    Returns
    -------
    int
        Number of internal missed cleavages.
    """
    seq = "".join(ch for ch in str(sequence) if ch.isalpha()).upper()
    if len(seq) < 2:
        return 0
    residue_set = set(residues)
    count = 0
    for i in range(len(seq) - 1):
        if seq[i] in residue_set and (cleave_before_proline or seq[i + 1] != "P"):
            count += 1
    return count


def check_enzyme(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Best-effort enzyme/specificity check (missed cleavages, warning only).

    Supports common C-terminal cleaving enzymes via :data:`_ENZYME_CLEAVAGE_RULES`
    (trypsin, trypsin/P, Lys-C, Arg-C, Glu-C, chymotrypsin). For each unique
    peptide it counts internal cleavage residues and warns when more peptides
    than allowed exceed ``allowed_miscleavages``. This is a heuristic: it ignores
    ragged termini and protein ends, so it can only be a warning. N-terminal
    cleavers (Asp-N, Lys-N) and unknown enzymes are reported as info (skipped).

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    params : Any
        Parsed parameters (object with ``enzyme``, ``semi_enzymatic``,
        ``allowed_miscleavages`` attributes).
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Warnings for peptides exceeding the allowed missed cleavages, or
        info/warning describing why the check was skipped.
    """
    report = ValidationReport()
    check = "enzyme"

    enzyme = getattr(params, "enzyme", None)
    if _is_missing(enzyme):
        report.add_warning(
            "enzyme_not_parsed",
            "Could not validate enzyme specificity because no enzyme was parsed from the parameter file.",
            check,
            field="enzyme",
        )
        return report.issues

    normalized = _normalize_enzyme(enzyme)
    if normalized not in _ENZYME_CLEAVAGE_RULES:
        report.add_info(
            "enzyme_check_unsupported",
            f"Enzyme-specificity validation is not implemented for enzyme '{enzyme}'; check skipped.",
            check,
            field="enzyme",
            observed=enzyme,
        )
        return report.issues

    rule = _ENZYME_CLEAVAGE_RULES[normalized]
    if rule is None:
        report.add_info(
            "enzyme_check_unsupported",
            f"Enzyme '{enzyme}' cleaves N-terminal to its residue; the missed-cleavage heuristic "
            "does not apply and the check was skipped.",
            check,
            field="enzyme",
            observed=enzyme,
        )
        return report.issues
    residues, cleave_before_proline = rule

    if bool(getattr(params, "semi_enzymatic", False)) is True:
        report.add_info(
            "enzyme_semi_skipped",
            "Semi-enzymatic search detected; the missed-cleavage heuristic was skipped.",
            check,
            field="semi_enzymatic",
        )
        return report.issues

    allowed = _as_int(getattr(params, "allowed_miscleavages", None))
    if allowed is None:
        report.add_warning(
            "miscleavages_not_parsed",
            "Could not validate missed cleavages because 'allowed_miscleavages' was not parsed "
            "from the parameter file.",
            check,
            field="allowed_miscleavages",
        )
        return report.issues

    if config.sequence_column not in df.columns:
        report.add_warning(
            "sequence_column_missing",
            f"Sequence column '{config.sequence_column}' not found; missed-cleavage check skipped.",
            check,
            field=config.sequence_column,
        )
        return report.issues

    sequences = df[config.sequence_column].astype(str)
    unique_sequences = pd.Series(sequences.unique())
    missed = unique_sequences.apply(lambda s: _count_missed_cleavages(s, residues, cleave_before_proline))
    offending = unique_sequences[missed > allowed]

    if len(offending) > 0:
        examples = [f"{seq} ({_count_missed_cleavages(seq, residues, cleave_before_proline)} MC)" for seq in offending][
            :MAX_ROW_EXAMPLES
        ]
        report.add_warning(
            "missed_cleavages_exceeded",
            f"{len(offending)} unique peptide sequence(s) appear to exceed the allowed missed "
            f"cleavages ({allowed}) for {enzyme}. This is a heuristic (ignores ragged termini and "
            "protein ends); review before submitting.",
            check,
            field="allowed_miscleavages",
            observed=f"{len(offending)} sequences with > {allowed} internal cleavage sites",
            expected=f"<= {allowed} internal missed cleavages",
            examples=examples,
        )

    return report.issues


def check_modifications(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Best-effort modification compatibility check (warnings only).

    Compares human-readable modification names observed in the ``proforma``
    column against the parsed fixed/variable modification settings. Mass-only
    and UniMod-only modification tokens are not compared because their
    representation is not normalized across tools.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    params : Any
        Parsed parameters (object with ``fixed_mods`` / ``variable_mods``).
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Warnings for observed modification names not found in the declared
        settings, or a warning/info describing why the check was limited.
    """
    report = ValidationReport()
    check = "modifications"

    if config.proforma_column not in df.columns:
        report.add_info(
            "modifications_no_proforma",
            f"No '{config.proforma_column}' column in the results; modification validation was skipped.",
            check,
            field=config.proforma_column,
        )
        return report.issues

    observed: set = set()
    for value in df[config.proforma_column].dropna().astype(str).unique():
        for match in _PROFORMA_MOD.findall(value):
            observed.add(match.strip())

    if not observed:
        report.add_info(
            "modifications_none_observed",
            "No modifications were observed in the results; nothing to validate.",
            check,
        )
        return report.issues

    fixed_mods = getattr(params, "fixed_mods", None)
    variable_mods = getattr(params, "variable_mods", None)

    declared_parts = []
    for value in (fixed_mods, variable_mods):
        if not _is_missing(value):
            declared_parts.append(str(value))
    declared_text = " ".join(declared_parts).lower()

    if not declared_text:
        report.add_warning(
            "modifications_not_parsed",
            "Could not validate modifications because no fixed/variable modification settings were "
            "parsed from the parameter file.",
            check,
            field="variable_mods",
            observed=sorted(observed)[:MAX_ROW_EXAMPLES],
        )
        return report.issues

    # Only compare clean, human-readable modification names; skip mass/UniMod tokens.
    unmatched = []
    for token in sorted(observed):
        name = token.replace(" ", "")
        if len(name) < 3 or not name.isalpha():
            continue
        if name.lower() not in declared_text:
            unmatched.append(token)

    if unmatched:
        report.add_warning(
            "modification_not_declared",
            f"{len(unmatched)} observed modification name(s) were not found in the declared "
            "fixed/variable modifications. Modification names differ across tools, so this is a "
            "heuristic; review before submitting.",
            check,
            field="variable_mods",
            observed=unmatched[:MAX_ROW_EXAMPLES],
            expected="modifications declared in the parameter file",
            examples=unmatched[:MAX_ROW_EXAMPLES],
        )

    return report.issues


def check_run_consistency(
    df: pd.DataFrame,
    params: Any,
    input_format: Optional[str],
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Check that the parameter file matches the submitted run, where feasible.

    Only software identity can be compared, because
    :class:`ProteoBenchParameters` does not expose raw-file, sample, or
    experiment identifiers. A mismatch in software identity is reported as an
    error; the unavailable run-level matching is reported as info.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame (unused for software identity but kept
        for signature consistency and future extension).
    params : Any
        Parsed parameters (object with ``software_name`` / ``software_version``).
    input_format : str or None
        The selected software tool used to parse the results.
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Issues describing software-identity mismatches and the documented
        limitation on run-level matching.
    """
    report = ValidationReport()
    check = "run_consistency"

    software_name = getattr(params, "software_name", None)
    if input_format and not _is_missing(software_name):
        if str(software_name).strip().lower() != str(input_format).strip().lower():
            report.add_error(
                "software_mismatch",
                f"The parameter file reports software '{software_name}', but the results were "
                f"submitted as '{input_format}'. The parameter file may belong to a different run.",
                check,
                field="software_name",
                observed=software_name,
                expected=input_format,
            )

    if _is_missing(getattr(params, "software_version", None)):
        report.add_info(
            "software_version_missing",
            "The software version could not be parsed from the parameter file.",
            check,
            field="software_version",
        )

    report.add_info(
        "run_identity_limited",
        "Run-level matching (raw-file, sample, or experiment names) is not available because the "
        "parsed parameters do not expose these identifiers; only software identity was checked.",
        check,
    )

    return report.issues


def check_max_modifications(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Check that no peptide carries more modifications than allowed (warning only).

    Counts the bracketed modifications in each ``proforma`` string and warns
    when more than ``max_mods`` are present. This is a heuristic: the count
    includes any fixed modifications written into the sequence, so it is an
    upper bound on the number of variable modifications.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame.
    params : Any
        Parsed parameters (object with a ``max_mods`` attribute).
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        A warning for peptides exceeding ``max_mods``, or a warning/info
        describing why the check was skipped.
    """
    report = ValidationReport()
    check = "max_modifications"

    max_mods = _as_int(getattr(params, "max_mods", None))
    if max_mods is None:
        report.add_warning(
            "max_mods_not_parsed",
            "Could not validate the maximum number of modifications because 'max_mods' was not "
            "parsed from the parameter file.",
            check,
            field="max_mods",
        )
        return report.issues

    if config.proforma_column not in df.columns:
        report.add_info(
            "max_mods_no_proforma",
            f"No '{config.proforma_column}' column in the results; the maximum-modifications check was skipped.",
            check,
            field=config.proforma_column,
        )
        return report.issues

    proforma = df[config.proforma_column].dropna().astype(str)
    unique_proforma = pd.Series(proforma.unique())
    mod_counts = unique_proforma.apply(lambda s: len(_PROFORMA_MOD.findall(s)))
    offending = unique_proforma[mod_counts > max_mods]

    if len(offending) > 0:
        examples = [f"{seq} ({len(_PROFORMA_MOD.findall(seq))} mods)" for seq in offending][:MAX_ROW_EXAMPLES]
        report.add_warning(
            "max_modifications_exceeded",
            f"{len(offending)} unique peptidoform(s) carry more than the allowed {max_mods} "
            "modification(s). The count includes any fixed modifications present in the sequence, "
            "so it is an upper bound; review before submitting.",
            check,
            field="max_mods",
            observed=f"{len(offending)} peptidoforms with > {max_mods} modifications",
            expected=f"<= {max_mods} modifications per peptidoform",
            examples=examples,
        )

    return report.issues


def _parse_tolerance(text: Any) -> tuple:
    """
    Parse a tolerance string into a magnitude and unit.

    Handles bracketed signed ranges such as ``"[-20.0 ppm, 20.0 ppm]"`` by
    returning the largest absolute magnitude and the (lower-cased) unit.

    Parameters
    ----------
    text : Any
        The tolerance value (typically a formatted string).

    Returns
    -------
    tuple
        ``(magnitude, unit)`` where ``magnitude`` is a float (or ``None`` if no
        number could be parsed) and ``unit`` is a lower-case string or ``None``.
    """
    if _is_missing(text):
        return None, None
    magnitudes = []
    unit = None
    for number, parsed_unit in _TOLERANCE_TOKEN.findall(str(text)):
        try:
            magnitudes.append(abs(float(number)))
        except ValueError:
            continue
        if parsed_unit:
            unit = parsed_unit.lower()
    if not magnitudes:
        return None, None
    return max(magnitudes), unit


def _check_one_tolerance(report: ValidationReport, value: Any, label: str, field: str) -> None:
    """
    Sanity-check a single mass-tolerance value and append any issue.

    Parameters
    ----------
    report : ValidationReport
        Report to append issues to.
    value : Any
        The tolerance value from the parameters.
    label : str
        Human-readable label (e.g. ``"precursor mass tolerance"``).
    field : str
        The parameter field name (used in the issue ``field`` and codes).
    """
    check = "mass_tolerance"
    if _is_missing(value):
        report.add_warning(
            f"{field}_not_parsed",
            f"Could not validate the {label} because it was not parsed from the parameter file.",
            check,
            field=field,
        )
        return

    magnitude, unit = _parse_tolerance(value)
    if magnitude is None:
        report.add_warning(
            f"{field}_unparsable",
            f"The {label} ('{value}') could not be interpreted as a numeric tolerance.",
            check,
            field=field,
            observed=value,
        )
        return

    if magnitude <= 0:
        report.add_warning(
            f"{field}_non_positive",
            f"The {label} ('{value}') is zero or negative, which is not a valid search tolerance.",
            check,
            field=field,
            observed=value,
        )
        return

    if unit == "ppm":
        ceiling = _MAX_PLAUSIBLE_PPM
    elif unit in {"da", "th", "amu"}:
        ceiling = _MAX_PLAUSIBLE_DALTON
    elif unit == "mmu":
        # 1 mmu = 1e-3 Da, so the Dalton ceiling becomes 1000x larger in mmu.
        ceiling = _MAX_PLAUSIBLE_DALTON * 1000
    else:
        ceiling = None

    if ceiling is not None and magnitude > ceiling:
        report.add_warning(
            f"{field}_implausible",
            f"The {label} ('{value}') is unusually large and may indicate a mis-parsed value; "
            "review before submitting.",
            check,
            field=field,
            observed=value,
            expected=f"<= {ceiling:g} {unit}",
        )


def check_mass_tolerances(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Sanity-check the precursor and fragment mass tolerances (warning only).

    There is no per-result tolerance to compare against, so this validates that
    the parsed ``precursor_mass_tolerance`` and ``fragment_mass_tolerance`` are
    present, numeric, positive, and within a plausible range. Mis-parsed or
    nonsensical values are flagged as warnings.

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame (unused; kept for signature consistency).
    params : Any
        Parsed parameters (object with ``precursor_mass_tolerance`` /
        ``fragment_mass_tolerance`` attributes).
    config : ModuleValidationConfig
        Module validation configuration.

    Returns
    -------
    list of ValidationIssue
        Warnings for missing, unparsable, or implausible tolerances.
    """
    report = ValidationReport()
    _check_one_tolerance(
        report,
        getattr(params, "precursor_mass_tolerance", None),
        "precursor mass tolerance",
        "precursor_mass_tolerance",
    )
    _check_one_tolerance(
        report, getattr(params, "fragment_mass_tolerance", None), "fragment mass tolerance", "fragment_mass_tolerance"
    )
    return report.issues


def check_fdr_psm(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Sanity-check the PSM-level FDR (warning only).

    Validates that ``ident_fdr_psm`` is present, within ``[0, 1]``, and not
    above the benchmark's recommended maximum
    (:attr:`ModuleValidationConfig.recommended_max_fdr_psm`, default 0.01).

    Parameters
    ----------
    df : pandas.DataFrame
        The standardized result DataFrame (unused; kept for signature consistency).
    params : Any
        Parsed parameters (object with an ``ident_fdr_psm`` attribute).
    config : ModuleValidationConfig
        Module validation configuration (provides ``recommended_max_fdr_psm``).

    Returns
    -------
    list of ValidationIssue
        Warnings for a missing, out-of-range, or above-recommended PSM FDR.
    """
    report = ValidationReport()
    check = "fdr"

    fdr = _as_float(getattr(params, "ident_fdr_psm", None))
    if fdr is None:
        report.add_warning(
            "fdr_psm_not_parsed",
            "Could not validate the PSM FDR because 'ident_fdr_psm' was not parsed from the parameter file.",
            check,
            field="ident_fdr_psm",
        )
        return report.issues

    if fdr < 0 or fdr > 1:
        report.add_warning(
            "fdr_psm_out_of_range",
            f"The PSM FDR ({fdr}) is outside the valid range [0, 1]; the value may be mis-parsed.",
            check,
            field="ident_fdr_psm",
            observed=fdr,
            expected="[0, 1]",
        )
        return report.issues

    recommended = getattr(config, "recommended_max_fdr_psm", None)
    if recommended is not None and fdr > recommended:
        report.add_warning(
            "fdr_psm_above_recommended",
            f"The PSM FDR ({fdr}) is higher than the recommended maximum of {recommended} for this benchmark.",
            check,
            field="ident_fdr_psm",
            observed=fdr,
            expected=f"<= {recommended}",
        )

    return report.issues
