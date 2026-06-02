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

Documented limitations / skipped checks
----------------------------------------
* **Enzyme specificity**: only a trypsin-family missed-cleavage heuristic is
  implemented, and only as a *warning*. Full specificity validation would need
  the reference protein sequences (to resolve protein N-/C-termini and ragged
  ends) and per-enzyme cleavage rules, which are out of scope here.
* **Modifications**: cross-tool modification representations are not normalized
  (human-readable names, UniMod accessions, and raw masses all occur). Only
  human-readable modification names observed in the ``proforma`` column are
  compared, as warnings; mass-only / UniMod-only tokens are skipped.
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


def _count_tryptic_missed_cleavages(sequence: str, cleave_before_proline: bool) -> int:
    """
    Count internal tryptic missed cleavages in a peptide sequence.

    A missed cleavage is an internal ``K``/``R`` (not the C-terminal residue).
    For standard trypsin, a ``K``/``R`` immediately followed by ``P`` does not
    count.

    Parameters
    ----------
    sequence : str
        Peptide sequence (plain amino-acid letters).
    cleave_before_proline : bool
        ``True`` for Trypsin/P (cleaves before proline), ``False`` for standard
        trypsin (proline-restricted).

    Returns
    -------
    int
        Number of internal missed cleavages.
    """
    seq = "".join(ch for ch in str(sequence) if ch.isalpha()).upper()
    if len(seq) < 2:
        return 0
    count = 0
    for i in range(len(seq) - 1):
        if seq[i] in ("K", "R"):
            if cleave_before_proline or seq[i + 1] != "P":
                count += 1
    return count


def check_enzyme(
    df: pd.DataFrame,
    params: Any,
    config: ModuleValidationConfig,
) -> List[ValidationIssue]:
    """
    Best-effort enzyme/specificity check (trypsin-family missed cleavages).

    Implemented only for trypsin-family enzymes and only as a warning, because
    a strict check requires the reference protein sequences and per-enzyme
    cleavage rules. Other enzymes are reported as an info (skipped).

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

    enzyme_str = str(enzyme).strip().lower()
    # Match the trypsin family by prefix so that e.g. "Chymotrypsin" is excluded.
    if not enzyme_str.startswith("trypsin"):
        report.add_info(
            "enzyme_check_unsupported",
            f"Enzyme-specificity validation is not implemented for enzyme '{enzyme}'; check skipped.",
            check,
            field="enzyme",
            observed=enzyme,
        )
        return report.issues

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

    cleave_before_proline = "/p" in enzyme_str
    sequences = df[config.sequence_column].astype(str)
    unique_sequences = pd.Series(sequences.unique())
    missed = unique_sequences.apply(lambda s: _count_tryptic_missed_cleavages(s, cleave_before_proline))
    offending = unique_sequences[missed > allowed]

    if len(offending) > 0:
        examples = [f"{seq} ({_count_tryptic_missed_cleavages(seq, cleave_before_proline)} MC)" for seq in offending][
            :MAX_ROW_EXAMPLES
        ]
        report.add_warning(
            "missed_cleavages_exceeded",
            f"{len(offending)} unique peptide sequence(s) appear to exceed the allowed missed "
            f"cleavages ({allowed}) for {enzyme}. This is a heuristic (ignores ragged termini and "
            "protein ends); review before submitting.",
            check,
            field="allowed_miscleavages",
            observed=f"{len(offending)} sequences with > {allowed} internal K/R",
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
