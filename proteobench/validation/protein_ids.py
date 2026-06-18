"""
Protein-identifier extraction helpers for submission validation.

ProteoBench tool outputs store protein identifiers in the standardized
``Proteins`` column. The representation is not fully normalized across tools:

* a single protein may be a UniProt-style triplet such as ``sp|P49327|FAS_HUMAN``
  (the ``|`` separates database/accession/entry-name), a bare accession such as
  ``P49327``, or an isoform such as ``P49327-2``;
* multiple proteins (protein groups) are joined with ``;`` (e.g. MaxQuant) or
  ``,`` (e.g. the FragPipe loader combines ``Protein`` and ``Mapped Proteins``).

These helpers split protein-group strings into individual proteins and extract
the candidate identifiers (accession, entry name, isoform base) used to match
against a FASTA-derived accession set. They are deliberately generic so the
core validator does not embed tool-specific assumptions.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Set

#: Default separators used to split a protein-group string into individual proteins.
#: The ``|`` character is intentionally excluded because it is a *within-protein*
#: separator in UniProt identifiers (``db|accession|entryname``).
DEFAULT_GROUP_SEPARATORS = (";", ",")

#: Matches a UniProt-style ``db|accession|entryname`` token.
_UNIPROT_TRIPLET = re.compile(r"^(?:sp|tr|up)\|([^|]+)\|(\S+)$", re.IGNORECASE)

#: Matches a trailing isoform suffix such as ``-2`` on an accession.
_ISOFORM_SUFFIX = re.compile(r"-\d+$")


def split_protein_groups(value: str, separators: Iterable[str] = DEFAULT_GROUP_SEPARATORS) -> List[str]:
    """
    Split a protein-group cell into individual protein tokens.

    Parameters
    ----------
    value : str
        The raw value of a ``Proteins`` cell (may contain several proteins).
    separators : iterable of str, optional
        Characters that separate proteins within a group. Defaults to
        :data:`DEFAULT_GROUP_SEPARATORS` (``;`` and ``,``).

    Returns
    -------
    list of str
        Stripped, non-empty individual protein tokens.
    """
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []

    seps = [s for s in separators if s]
    if not seps:
        tokens = [text]
    else:
        pattern = "|".join(re.escape(s) for s in seps)
        tokens = re.split(pattern, text)

    return [t.strip() for t in tokens if t and t.strip()]


def extract_identifiers(protein_token: str) -> Set[str]:
    """
    Extract candidate identifiers from a single protein token.

    For a UniProt triplet such as ``sp|P49327|FAS_HUMAN`` this returns the
    accession (``P49327``), the entry name (``FAS_HUMAN``), and (for isoforms)
    the isoform base accession. For a bare accession it returns the accession
    and its isoform base. For any other token it returns the token unchanged.

    Parameters
    ----------
    protein_token : str
        A single protein identifier (one element of a protein group).

    Returns
    -------
    set of str
        Candidate identifiers usable for FASTA membership testing.
    """
    if protein_token is None:
        return set()
    token = str(protein_token).strip()
    if not token:
        return set()

    identifiers: Set[str] = {token}

    triplet = _UNIPROT_TRIPLET.match(token)
    if triplet:
        accession, entry_name = triplet.group(1), triplet.group(2)
        identifiers.add(accession)
        identifiers.add(entry_name)
        base = _ISOFORM_SUFFIX.sub("", accession)
        if base != accession:
            identifiers.add(base)
    elif "|" in token:
        # Unknown ``a|b|c`` shape: keep every part as a candidate.
        for part in token.split("|"):
            part = part.strip()
            if part:
                identifiers.add(part)
    else:
        base = _ISOFORM_SUFFIX.sub("", token)
        if base != token:
            identifiers.add(base)

    return identifiers


def is_decoy_or_contaminant(
    protein_token: str,
    contaminant_flag: str = None,
    decoy_prefixes: Iterable[str] = (),
) -> bool:
    """
    Determine whether a protein token is a decoy or contaminant marker.

    The check is case-insensitive and matches the contaminant flag as a
    substring (mirroring ParseSettings contaminant detection) and the decoy
    markers as case-insensitive prefixes.

    Parameters
    ----------
    protein_token : str
        A single protein identifier.
    contaminant_flag : str, optional
        Substring marking contaminant proteins (from the tool parse settings,
        e.g. ``"Cont_"``). ``None`` disables contaminant detection.
    decoy_prefixes : iterable of str, optional
        Prefixes marking decoy proteins (e.g. ``"rev_"``, ``"DECOY_"``).

    Returns
    -------
    bool
        ``True`` if the token is a decoy or contaminant identifier.
    """
    if protein_token is None:
        return False
    token = str(protein_token).strip()
    if not token:
        return False

    lowered = token.lower()

    if contaminant_flag and str(contaminant_flag).lower() in lowered:
        return True

    for prefix in decoy_prefixes:
        if prefix and lowered.startswith(str(prefix).lower()):
            return True

    return False
