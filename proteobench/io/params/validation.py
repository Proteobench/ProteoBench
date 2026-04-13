"""
Validation functions for ProteoBench parameter files and search results.

These functions check whether the parameter file settings are consistent
with the actual search results (charge ranges, peptide lengths, etc.)
and whether the FASTA file used appears to be an approved ProteoBench FASTA.
"""

from __future__ import annotations

import logging
import os
import re
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Patterns that approved ProteoBench FASTA filenames should contain
APPROVED_FASTA_PATTERNS = [
    "ProteoBenchFASTA",
    "BenchmarkFASTA",
]

# Species flags expected to be present in results when the correct FASTA is used
DEFAULT_EXPECTED_SPECIES = ["HUMAN", "YEAST", "ECOLI"]


def check_charge_range(
    params,
    intermediate_df: pd.DataFrame,
    precursor_ion_column: str = "precursor ion",
) -> List[str]:
    """
    Check that the charge states in search results are within the range
    specified in the parameter file.

    Parses charges from the precursor ion column (format: ``peptide/charge``)
    and compares them against ``params.min_precursor_charge`` and
    ``params.max_precursor_charge``.

    Parameters
    ----------
    params : ProteoBenchParameters
        The parsed parameter file parameters.
    intermediate_df : pd.DataFrame
        The intermediate metric structure from the benchmarking run.
        Must contain a column with precursor ions in ``peptide/charge`` format.
    precursor_ion_column : str, optional
        Name of the column containing precursor ion identifiers.
        Defaults to ``"precursor ion"``.

    Returns
    -------
    List[str]
        A list of warning messages. Empty if no inconsistencies were found.
    """
    warnings = []

    if precursor_ion_column not in intermediate_df.columns:
        logger.debug(
            "Column '%s' not found in intermediate data; skipping charge range check.",
            precursor_ion_column,
        )
        return warnings

    charges = _extract_charges_from_precursor_ions(intermediate_df[precursor_ion_column])
    if charges.empty:
        return warnings

    actual_min = int(charges.min())
    actual_max = int(charges.max())

    min_charge = _to_int_or_none(getattr(params, "min_precursor_charge", None))
    max_charge = _to_int_or_none(getattr(params, "max_precursor_charge", None))

    if min_charge is not None and actual_min < min_charge:
        warnings.append(
            f"Minimum charge in search results ({actual_min}) is lower than "
            f"the minimum precursor charge in the parameter file ({min_charge}). "
            "Please verify that the correct parameter file was uploaded."
        )

    if max_charge is not None and actual_max > max_charge:
        warnings.append(
            f"Maximum charge in search results ({actual_max}) is higher than "
            f"the maximum precursor charge in the parameter file ({max_charge}). "
            "Please verify that the correct parameter file was uploaded."
        )

    return warnings


def check_peptide_length_range(
    params,
    intermediate_df: pd.DataFrame,
    precursor_ion_column: str = "precursor ion",
    peptidoform_column: str = "peptidoform",
) -> List[str]:
    """
    Check that the peptide lengths in the search results are within the range
    specified in the parameter file.

    For ion-level modules, peptide sequence is parsed from the precursor ion
    column (format: ``peptide/charge``).  For peptidoform-level modules the
    ``peptidoform`` column is used instead.

    Parameters
    ----------
    params : ProteoBenchParameters
        The parsed parameter file parameters.
    intermediate_df : pd.DataFrame
        The intermediate metric structure from the benchmarking run.
    precursor_ion_column : str, optional
        Name of the column containing precursor ion identifiers
        (``peptide/charge`` format).  Defaults to ``"precursor ion"``.
    peptidoform_column : str, optional
        Name of the column containing peptidoform identifiers.
        Defaults to ``"peptidoform"``.

    Returns
    -------
    List[str]
        A list of warning messages. Empty if no inconsistencies were found.
    """
    warnings = []

    peptide_lengths = None

    if precursor_ion_column in intermediate_df.columns:
        sequences = _extract_sequences_from_precursor_ions(intermediate_df[precursor_ion_column])
        if not sequences.empty:
            peptide_lengths = sequences.apply(len)
    elif peptidoform_column in intermediate_df.columns:
        # For peptidoform-level modules use the peptidoform column
        peptide_lengths = intermediate_df[peptidoform_column].dropna().apply(
            _peptide_length_from_peptidoform
        )

    if peptide_lengths is None or peptide_lengths.empty:
        return warnings

    actual_min = int(peptide_lengths.min())
    actual_max = int(peptide_lengths.max())

    min_length = _to_int_or_none(getattr(params, "min_peptide_length", None))
    max_length = _to_int_or_none(getattr(params, "max_peptide_length", None))

    if min_length is not None and actual_min < min_length:
        warnings.append(
            f"Minimum peptide length in search results ({actual_min}) is shorter than "
            f"the minimum peptide length in the parameter file ({min_length}). "
            "Please verify that the correct parameter file was uploaded."
        )

    if max_length is not None and actual_max > max_length:
        warnings.append(
            f"Maximum peptide length in search results ({actual_max}) is longer than "
            f"the maximum peptide length in the parameter file ({max_length}). "
            "Please verify that the correct parameter file was uploaded."
        )

    return warnings


def check_fasta_from_params(
    params,
    approved_patterns: Optional[List[str]] = None,
) -> List[str]:
    """
    Check whether the FASTA database referenced in the parameter file is an
    approved ProteoBench FASTA.

    The FASTA path stored in ``params.fasta_database`` (if present) is checked
    against the list of approved filename patterns.

    Parameters
    ----------
    params : ProteoBenchParameters
        The parsed parameter file parameters.  The attribute ``fasta_database``
        must be set for this check to run.
    approved_patterns : list of str, optional
        List of substrings that an approved FASTA filename should contain.
        Defaults to :data:`APPROVED_FASTA_PATTERNS`.

    Returns
    -------
    List[str]
        A list of warning messages. Empty if no issues were found.
    """
    warnings = []

    if approved_patterns is None:
        approved_patterns = APPROVED_FASTA_PATTERNS

    fasta_db = getattr(params, "fasta_database", None)
    if not fasta_db:
        return warnings

    fasta_filename = os.path.basename(fasta_db.replace("\\", "/"))
    if not any(pattern in fasta_filename for pattern in approved_patterns):
        warnings.append(
            f"The FASTA database referenced in the parameter file "
            f"('{fasta_filename}') does not appear to be an approved "
            f"ProteoBench FASTA. "
            f"Expected the filename to contain one of: {approved_patterns}. "
            "Please verify that you used the correct FASTA file."
        )

    return warnings


def check_fasta_from_results(
    intermediate_df: pd.DataFrame,
    expected_species: Optional[List[str]] = None,
) -> List[str]:
    """
    Check that the search results contain proteins from all expected species,
    which indicates that the correct mixed-species ProteoBench FASTA was used.

    Parameters
    ----------
    intermediate_df : pd.DataFrame
        The intermediate metric structure from the benchmarking run.
        Should contain boolean species flag columns (e.g., ``HUMAN``,
        ``YEAST``, ``ECOLI``).
    expected_species : list of str, optional
        Names of the species columns expected to have at least one ``True``
        value.  Defaults to :data:`DEFAULT_EXPECTED_SPECIES`.

    Returns
    -------
    List[str]
        A list of warning messages. Empty if no issues were found.
    """
    warnings = []

    if expected_species is None:
        expected_species = DEFAULT_EXPECTED_SPECIES

    for species in expected_species:
        if species not in intermediate_df.columns:
            continue
        if not intermediate_df[species].any():
            warnings.append(
                f"No {species} proteins were found in the search results. "
                "This may indicate that the wrong FASTA database was used. "
                "Please verify that you used the ProteoBench mixed-species FASTA."
            )

    return warnings


def validate_all(
    params,
    intermediate_df: pd.DataFrame,
    expected_species: Optional[List[str]] = None,
    approved_fasta_patterns: Optional[List[str]] = None,
    precursor_ion_column: str = "precursor ion",
    peptidoform_column: str = "peptidoform",
) -> List[str]:
    """
    Run all parameter-file and FASTA validation checks and return a combined
    list of warning messages.

    Parameters
    ----------
    params : ProteoBenchParameters
        The parsed parameter file parameters.
    intermediate_df : pd.DataFrame
        The intermediate metric structure from the benchmarking run.
    expected_species : list of str, optional
        Species expected to be present in the results.
        Defaults to :data:`DEFAULT_EXPECTED_SPECIES`.
    approved_fasta_patterns : list of str, optional
        Substrings that an approved FASTA filename should contain.
        Defaults to :data:`APPROVED_FASTA_PATTERNS`.
    precursor_ion_column : str, optional
        Column with precursor ion identifiers in ``peptide/charge`` format.
        Defaults to ``"precursor ion"``.
    peptidoform_column : str, optional
        Column with peptidoform identifiers (peptidoform-level modules).
        Defaults to ``"peptidoform"``.

    Returns
    -------
    List[str]
        A combined list of all warning messages from all checks.
    """
    all_warnings: List[str] = []

    all_warnings.extend(
        check_charge_range(
            params,
            intermediate_df,
            precursor_ion_column=precursor_ion_column,
        )
    )
    all_warnings.extend(
        check_peptide_length_range(
            params,
            intermediate_df,
            precursor_ion_column=precursor_ion_column,
            peptidoform_column=peptidoform_column,
        )
    )
    all_warnings.extend(
        check_fasta_from_params(params, approved_patterns=approved_fasta_patterns)
    )
    all_warnings.extend(
        check_fasta_from_results(intermediate_df, expected_species=expected_species)
    )

    return all_warnings


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_charges_from_precursor_ions(precursor_ions: pd.Series) -> pd.Series:
    """
    Extract integer charge values from a series of ``peptide/charge`` strings.
    """
    charges = precursor_ions.dropna().apply(_parse_charge_from_ion)
    return charges.dropna().astype(int)


def _extract_sequences_from_precursor_ions(precursor_ions: pd.Series) -> pd.Series:
    """
    Extract plain amino-acid sequences from a series of ``peptide/charge``
    strings (dropping modifications and the trailing charge suffix).
    """
    sequences = precursor_ions.dropna().apply(_parse_sequence_from_ion)
    return sequences.dropna()


def _parse_charge_from_ion(ion: str) -> Optional[int]:
    """
    Return the integer charge from a ``peptide/charge`` string, or ``None``
    if the string does not match the expected format.
    """
    if not isinstance(ion, str):
        return None
    parts = ion.rsplit("/", 1)
    if len(parts) == 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return None


def _parse_sequence_from_ion(ion: str) -> Optional[str]:
    """
    Return the bare amino-acid sequence from a ``peptide/charge`` string.

    Strips ProForma-style modification annotations (e.g. ``[Oxidation]`` or
    ``(ox)``) and the trailing ``/charge`` suffix, then returns the residue
    string.  Returns ``None`` if the input does not match.
    """
    if not isinstance(ion, str):
        return None
    sequence_part = ion.rsplit("/", 1)[0]
    # Remove ProForma bracketed modifications: [...]
    sequence_part = re.sub(r"\[.*?\]", "", sequence_part)
    # Remove parenthesised modifications: (...)
    sequence_part = re.sub(r"\(.*?\)", "", sequence_part)
    # Remove any leading/trailing non-AA characters (e.g. "-")
    sequence_part = re.sub(r"[^A-Za-z]", "", sequence_part)
    return sequence_part if sequence_part else None


def _to_int_or_none(value) -> Optional[int]:
    """
    Convert *value* to ``int``, returning ``None`` for falsy / non-numeric
    values.
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _peptide_length_from_peptidoform(peptidoform: str) -> int:
    """
    Return the number of residues in a peptidoform string.

    Strips ProForma-style modification annotations (``[...]`` and ``(...)``),
    leading/trailing ``-`` terminators, and any other non-alphabetic characters,
    then returns the length of the remaining string.
    """
    seq = str(peptidoform)
    seq = re.sub(r"\[.*?\]|\(.*?\)", "", seq)
    seq = re.sub(r"[^A-Za-z]", "", seq)
    return len(seq)
