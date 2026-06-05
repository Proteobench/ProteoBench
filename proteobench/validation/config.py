"""
Module-level validation configuration.

:class:`ModuleValidationConfig` collects the small amount of per-module
information the validator needs that is not part of the standardized result
DataFrame or the parsed parameters: the standardized column names, the
protein-group separators, the contaminant flag and decoy prefixes used to skip
non-target identifiers, and the reference FASTA location.

The ``validation_profile`` field selects which set of checks the orchestrator
runs. It is the name of a profile registered in
:mod:`proteobench.validation.profiles`. It is resolved (in order of precedence):

1. an explicit ``[validation].profile`` key in the module's ``module_settings.toml``
   (the declarative path: adding a new module of an existing category is config-only);
2. inferred from the module's parser class via the existing ``MODULE_TO_CLASS``
   registry (``ParseSettingsQuant`` -> ``"quant_lfq"``, ``ParseSettingsDeNovo`` -> ``"denovo"``);
3. the :data:`DEFAULT_VALIDATION_PROFILE` fallback.

A genuinely new category of module is supported by registering a new profile
in ``profiles.py`` (or from third-party code) and pointing the module at it via
the TOML key; the orchestrator itself never changes.

The reference FASTA is read from an optional ``[reference_database]`` section in
the module's ``module_settings.toml`` (beside ``[species_expected_ratio]`` and
``[general]``). Module types whose reference is not a FASTA (e.g. de novo, which
compares against a ground-truth table) simply omit ``fasta_url``.

Example ``module_settings.toml`` sections::

    [reference_database]
    "fasta_url" = "https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip"

    [validation]
    "profile" = "quant_lfq"
    # optional mass-tolerance plausibility ceilings (no default; skipped if unset):
    # "max_plausible_ppm" = 1000.0
    # "max_plausible_dalton" = 10.0
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Tuple

import toml

from proteobench.validation.protein_ids import DEFAULT_GROUP_SEPARATORS

#: Profile used when none can be resolved from config or the parser class.
DEFAULT_VALIDATION_PROFILE = "quant_lfq"

#: Maps a parser class name to the default validation profile for that family.
#: Resolution falls back to this when no ``[validation].profile`` is declared.
_PROFILE_BY_PARSER_CLASS = {
    "ParseSettingsQuant": "quant_lfq",
    "ParseSettingsDeNovo": "denovo",
}

#: Common decoy-identifier prefixes. The ParseSettings configuration marks
#: decoys via a boolean ``Reverse`` column rather than an accession prefix, so
#: these defaults provide a tool-agnostic fallback for skipping decoy proteins.
DEFAULT_DECOY_PREFIXES = ("rev_", "rev__", "decoy_", "decoy", "reverse_", "##")


def _resolve_profile(module_id: str, declared_profile: Optional[str]) -> str:
    """
    Resolve the validation profile name for a module.

    Resolution order: an explicit profile declared in ``module_settings.toml``
    wins; otherwise the profile is inferred from the module's parser class via
    the existing ``MODULE_TO_CLASS`` registry; otherwise
    :data:`DEFAULT_VALIDATION_PROFILE` is used.

    Parameters
    ----------
    module_id : str
        The module identifier.
    declared_profile : str or None
        The profile name declared in ``[validation].profile``, if any.

    Returns
    -------
    str
        The resolved profile name.
    """
    if isinstance(declared_profile, str) and declared_profile:
        return declared_profile

    try:
        from proteobench.io.parsing.parse_settings import MODULE_TO_CLASS

        parser_cls = MODULE_TO_CLASS.get(module_id)
        if parser_cls is not None:
            inferred = _PROFILE_BY_PARSER_CLASS.get(parser_cls.__name__)
            if inferred:
                return inferred
    except Exception:
        pass

    return DEFAULT_VALIDATION_PROFILE


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
    recommended_max_fdr_psm : float, optional
        Recommended maximum PSM-level FDR for the benchmark. A parsed FDR above
        this value produces a warning. Default ``0.01`` (1%). Set to ``None`` to
        disable the recommendation check.
    max_plausible_ppm : float, optional
        Plausibility ceiling for ppm mass tolerances. A parsed tolerance above
        this value produces a warning. No default (``None``); when unset, the
        implausible-value check is skipped. Set via ``[validation]`` in
        ``module_settings.toml``.
    max_plausible_dalton : float, optional
        Plausibility ceiling for absolute (Da / Th / amu) mass tolerances, scaled
        by 1000 for mmu. No default (``None``); when unset, the implausible-value
        check is skipped. Set via ``[validation]`` in ``module_settings.toml``.
    validation_profile : str, optional
        Name of the registered profile whose checks the orchestrator runs. Set
        automatically by :meth:`from_parse_settings`; defaults to
        :data:`DEFAULT_VALIDATION_PROFILE` for direct construction so that the
        existing quant behaviour is preserved.
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
    recommended_max_fdr_psm: Optional[float] = 0.01
    max_plausible_ppm: Optional[float] = None
    max_plausible_dalton: Optional[float] = None
    validation_profile: str = DEFAULT_VALIDATION_PROFILE

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
        reads the optional ``[reference_database]`` and ``[validation]`` sections
        from the module's ``module_settings.toml``, and resolves the validation
        profile.

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
        config = cls()

        # Best effort: read the contaminant flag and species from the tool parser.
        # Wrapped defensively so validation never crashes on a parser issue.
        try:
            from proteobench.io.parsing.parse_settings import ParseSettingsBuilder

            builder = ParseSettingsBuilder(parse_settings_dir=parse_settings_dir, module_id=module_id)
            parser = builder.build_parser(input_format)
            config.contaminant_flag = getattr(parser, "contaminant_flag", None)
            species = parser.species_dict() if hasattr(parser, "species_dict") else {}
            config.species_flags = tuple(species.values())
        except Exception:
            pass

        # Read the module settings directly from disk (independent of the parser)
        # so the reference and profile resolve even if the parser cannot be built.
        module_settings = {}
        try:
            module_settings = toml.load(os.path.join(parse_settings_dir, "module_settings.toml"))
        except Exception:
            module_settings = {}

        reference = module_settings.get("reference_database", {}) or {}
        config.fasta_url = reference.get("fasta_url")
        config.fasta_filename = reference.get("fasta_filename")

        validation_section = module_settings.get("validation", {}) or {}
        declared_profile = validation_section.get("profile")
        config.validation_profile = _resolve_profile(module_id, declared_profile)
        config.max_plausible_ppm = validation_section.get("max_plausible_ppm")
        config.max_plausible_dalton = validation_section.get("max_plausible_dalton")

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
