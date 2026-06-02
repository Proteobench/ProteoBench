"""
FASTA / reference-database parsing for submission validation.

:class:`FastaReference` builds the set of accepted protein identifiers from a
FASTA file. It parses common UniProt-style headers (``sp|P49327|FAS_HUMAN``,
``tr|...|...``) as well as bare accession-like headers, indexing both the
accession and the entry name so that result protein identifiers can be matched
regardless of which form a tool reports.

The class can be built from raw text, a local path (plain, ``.gz``, or ``.zip``),
in-memory bytes, or an explicit iterable of identifiers. Downloading from a URL
is supported via :meth:`FastaReference.from_url`; the actual network call is
performed lazily so that importing this module never requires network access.
"""

from __future__ import annotations

import gzip
import io
import os
import zipfile
from typing import Iterable, Optional, Set

from proteobench.validation.protein_ids import extract_identifiers

#: File extensions recognised as FASTA when picking a member from an archive.
_FASTA_EXTENSIONS = (".fasta", ".fa", ".faa", ".fas")


def _looks_like_zip(data: bytes) -> bool:
    """
    Heuristically determine whether a byte string is a ZIP archive.

    Parameters
    ----------
    data : bytes
        Raw bytes to inspect.

    Returns
    -------
    bool
        ``True`` if the bytes start with the ZIP magic number.
    """
    return data[:2] == b"PK"


def _looks_like_gzip(data: bytes) -> bool:
    """
    Heuristically determine whether a byte string is gzip-compressed.

    Parameters
    ----------
    data : bytes
        Raw bytes to inspect.

    Returns
    -------
    bool
        ``True`` if the bytes start with the gzip magic number.
    """
    return data[:2] == b"\x1f\x8b"


def _pick_fasta_member(zf: zipfile.ZipFile, member_filename: Optional[str]) -> str:
    """
    Choose the FASTA member to read from a ZIP archive.

    Parameters
    ----------
    zf : zipfile.ZipFile
        Open ZIP archive.
    member_filename : str, optional
        Preferred member name. If not found, the first member with a FASTA
        extension is used.

    Returns
    -------
    str
        Name of the member to read.

    Raises
    ------
    ValueError
        If no suitable FASTA member can be found.
    """
    names = zf.namelist()
    if member_filename:
        for name in names:
            if os.path.basename(name) == member_filename or name == member_filename:
                return name
    for name in names:
        if name.lower().endswith(_FASTA_EXTENSIONS):
            return name
    raise ValueError(f"No FASTA member found in archive (members: {names}).")


def parse_fasta_header(header: str) -> Set[str]:
    """
    Parse a single FASTA header line into candidate identifiers.

    Parameters
    ----------
    header : str
        A FASTA header line, with or without the leading ``>``.

    Returns
    -------
    set of str
        Candidate identifiers (accession, entry name, isoform base, ...).
    """
    text = header.lstrip(">").strip()
    if not text:
        return set()
    first_token = text.split()[0]
    return extract_identifiers(first_token)


class FastaReference:
    """
    Set of protein identifiers derived from a FASTA / reference database.

    Parameters
    ----------
    identifiers : iterable of str, optional
        Pre-computed identifiers to seed the reference with.
    """

    def __init__(self, identifiers: Optional[Iterable[str]] = None):
        self._ids: Set[str] = set()
        if identifiers:
            for identifier in identifiers:
                if identifier:
                    self._ids.add(str(identifier).strip())
        self._ids_ci: Set[str] = {i.lower() for i in self._ids}

    def __len__(self) -> int:
        """
        Return the number of indexed identifiers.

        Returns
        -------
        int
            Count of unique identifiers in the reference.
        """
        return len(self._ids)

    @property
    def identifiers(self) -> Set[str]:
        """
        Return all indexed identifiers.

        Returns
        -------
        set of str
            The identifier set (accessions and entry names).
        """
        return set(self._ids)

    def contains(self, identifier: str) -> bool:
        """
        Test whether an identifier is present (case-insensitive).

        Parameters
        ----------
        identifier : str
            Identifier to test.

        Returns
        -------
        bool
            ``True`` if the identifier is in the reference.
        """
        if identifier is None:
            return False
        return str(identifier).strip().lower() in self._ids_ci

    def contains_any(self, identifiers: Iterable[str]) -> bool:
        """
        Test whether any of several identifiers is present.

        Parameters
        ----------
        identifiers : iterable of str
            Candidate identifiers for a single protein.

        Returns
        -------
        bool
            ``True`` if at least one candidate is in the reference.
        """
        return any(self.contains(identifier) for identifier in identifiers)

    @classmethod
    def from_text(cls, text: str) -> "FastaReference":
        """
        Build a reference from raw FASTA text.

        Parameters
        ----------
        text : str
            FASTA content (one or more records).

        Returns
        -------
        FastaReference
            Reference indexing every header's identifiers.
        """
        ids: Set[str] = set()
        for line in text.splitlines():
            if line.startswith(">"):
                ids.update(parse_fasta_header(line))
        return cls(ids)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        source_name: Optional[str] = None,
        member_filename: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> "FastaReference":
        """
        Build a reference from in-memory bytes (plain, gzip, or zip).

        Parameters
        ----------
        data : bytes
            Raw file content.
        source_name : str, optional
            Original file name or URL, used to detect the compression type.
        member_filename : str, optional
            Preferred FASTA member name when ``data`` is a ZIP archive.
        encoding : str, optional
            Text encoding used to decode the FASTA content. Default ``"utf-8"``.

        Returns
        -------
        FastaReference
            Reference indexing every header's identifiers.
        """
        name = (source_name or "").lower()

        if name.endswith(".zip") or _looks_like_zip(data):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                member = _pick_fasta_member(zf, member_filename)
                text = zf.read(member).decode(encoding, errors="replace")
        elif name.endswith(".gz") or _looks_like_gzip(data):
            text = gzip.decompress(data).decode(encoding, errors="replace")
        else:
            text = data.decode(encoding, errors="replace")

        return cls.from_text(text)

    @classmethod
    def from_path(cls, path: str, member_filename: Optional[str] = None) -> "FastaReference":
        """
        Build a reference from a local file path (plain, ``.gz``, or ``.zip``).

        Parameters
        ----------
        path : str
            Path to the FASTA, gzip, or zip file.
        member_filename : str, optional
            Preferred FASTA member name when ``path`` is a ZIP archive.

        Returns
        -------
        FastaReference
            Reference indexing every header's identifiers.
        """
        with open(path, "rb") as handle:
            data = handle.read()
        return cls.from_bytes(data, source_name=path, member_filename=member_filename)

    @classmethod
    def from_url(
        cls,
        url: str,
        member_filename: Optional[str] = None,
        timeout: int = 60,
    ) -> "FastaReference":
        """
        Build a reference by downloading a FASTA / zip / gzip from a URL.

        ``requests`` is imported lazily so that importing this module does not
        require network access.

        Parameters
        ----------
        url : str
            URL of the FASTA, gzip, or zip resource.
        member_filename : str, optional
            Preferred FASTA member name when the resource is a ZIP archive.
        timeout : int, optional
            Request timeout in seconds. Default ``60``.

        Returns
        -------
        FastaReference
            Reference indexing every header's identifiers.
        """
        import requests

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return cls.from_bytes(response.content, source_name=url, member_filename=member_filename)

    @classmethod
    def from_identifiers(cls, identifiers: Iterable[str]) -> "FastaReference":
        """
        Build a reference directly from an iterable of identifiers.

        Parameters
        ----------
        identifiers : iterable of str
            Identifiers to index (e.g. accessions extracted elsewhere).

        Returns
        -------
        FastaReference
            Reference indexing the supplied identifiers.
        """
        return cls(identifiers)
