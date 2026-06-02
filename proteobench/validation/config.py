"""
Module-level validation configuration.

:class:`ModuleValidationConfig` collects the small amount of per-module
information the validator needs that is not part of the standardized result
DataFrame or the parsed parameters: the standardized column names, the
protein-group separators, the contaminant flag and decoy prefixes used to skip
non-target identifiers, and the reference FASTA location.

The reference FASTA is read from an optional ``[reference_database]`` section in
the module's ``module_settings.toml`` (the same per-module settings file that
already holds ``[species_expected_ratio]`` and ``[general]``). This keeps the
reference next to the species composition that defines each module, and avoids
hard-coding paths inside the validator.

Example ``module_settings.toml`` section::

    [reference_database]
    "fasta_url" = "https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Tuple

import toml

from proteobench.validation.protein_ids import DEFAULT_GROUP_SEPARATORS

#: Common decoy-identifier prefixes. The ParseSettings configuration marks
#: decoys via a boolean ``Reverse`` column rather than an accession prefix, so
#: these defaults provide a tool-agnostic fallback for skipping decoy proteins.
DEFAULT_DECOY_PREFIXES = ("rev_", "rev__", "decoy_", "decoy", "reverse_", "##")


@dataclass
class ModuleValidationConfig:
    """
    Per-module configuration for submission validation.

    Attributes
    ----------
    protein_column : str, optional
        Column holding protein identifiers in the standardized DataFrame.
        Default ``"Proteins"``.
    sequence_column : str, optional
        Column holding the (plain) peptide sequence. Default ``"Sequence"``.
    charge_column : str, optional
        Column holding the precursor charge. Default ``"Charge"``.
    proforma_column : str, optional
        Column holding the ProForma modified sequence. Default ``"proforma"``.
    contaminant_column : str, optional
        Boolean column flagging contaminant rows. Default ``"contaminant"``.
    contaminant_flag : str, optional
        Substring marking contaminant proteins (from the tool parse settings,
        e.g. ``"Cont_"``).
    decoy_prefixes : tuple of str, optional
        Prefixes marking decoy proteins. Defaults to :data:`DEFAULT_DECOY_PREFIXES`.
    protein_group_separators : tuple of str, optional
        Separators used to split protein groups. Defaults to
        :data:`~proteobench.validation.protein_ids.DEFAULT_GROUP_SEPARATORS`.
    fasta_url : str, optional
        URL of the reference FASTA / zip / gzip for the module.
    fasta_filename : str, optional
        Preferred FASTA member name when the resource is an archive.
    species_flags : tuple of str, optional
        Species names configured for the module (e.g. ``("YEAST", "ECOLI", "HUMAN")``),
        derived from the tool's species mapper. Currently informational.
    """

    protein_column: str = "Proteins"
    sequence_column: str = "Sequence"
    charge_column: str = "Charge"
    proforma_column: str = "proforma"
    contaminant_column: str = "contaminant"
    contaminant_flag: Optional[str] = None
    decoy_prefixes: Tuple[str, ...] = DEFAULT_DECOY_PREFIXES
    protein_group_separators: Tuple[str, ...] = tuple(DEFAULT_GROUP_SEPARATORS)
    fasta_url: Optional[str] = None
    fasta_filename: Optional[str] = None
    species_flags: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_parse_settings(
        cls,
        parse_settings_dir: str,
        module_id: str,
        input_format: str,
    ) -> "ModuleValidationConfig":
        """
        Build a config from the existing parse settings of a module/tool.

        This reuses :class:`~proteobench.io.parsing.parse_settings.ParseSettingsBuilder`
        to read the contaminant flag and species flags for the selected tool,
        and reads the optional ``[reference_database]`` section from the
        module's ``module_settings.toml``.

        Parameters
        ----------
        parse_settings_dir : str
            Directory containing the module's parse settings (the module's
            ``parse_settings_dir`` attribute).
        module_id : str
            The module identifier (e.g. ``"quant_lfq_DDA_ion_QExactive"``).
        input_format : str
            The selected software tool (e.g. ``"MaxQuant"``).

        Returns
        -------
        ModuleValidationConfig
            Configuration populated from the parse settings. Falls back to the
            defaults for any value that cannot be read.
        """
        # Imported here to avoid a heavy import at module load time.
        from proteobench.io.parsing.parse_settings import ParseSettingsBuilder

        config = cls()

        builder = ParseSettingsBuilder(parse_settings_dir=parse_settings_dir, module_id=module_id)

        try:
            parser = builder.build_parser(input_format)
            config.contaminant_flag = getattr(parser, "contaminant_flag", None)
            species = parser.species_dict() if hasattr(parser, "species_dict") else {}
            config.species_flags = tuple(species.values())
        except Exception:
            # Validation must never crash because of a parser-construction issue;
            # fall back to defaults (contaminant rows are already filtered upstream).
            pass

        reference = {}
        try:
            module_settings = toml.load(builder.PARSE_SETTINGS_FILES_MODULE)
            reference = module_settings.get("reference_database", {}) or {}
        except Exception:
            reference = {}

        config.fasta_url = reference.get("fasta_url")
        config.fasta_filename = reference.get("fasta_filename")

        return config

    @staticmethod
    def read_reference_database(parse_settings_dir: str) -> dict:
        """
        Read the ``[reference_database]`` section of a module's settings.

        Parameters
        ----------
        parse_settings_dir : str
            Directory containing the module's ``module_settings.toml``.

        Returns
        -------
        dict
            The ``[reference_database]`` table, or an empty dict if absent.
        """
        path = os.path.join(parse_settings_dir, "module_settings.toml")
        try:
            module_settings = toml.load(path)
        except Exception:
            return {}
        return module_settings.get("reference_database", {}) or {}
