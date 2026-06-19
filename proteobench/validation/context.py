"""
Validation context passed to every check.

A :class:`ValidationContext` bundles all inputs a check might need behind a
single, uniform object so that every check has the signature
``check(ctx) -> list[ValidationIssue]``. This decouples individual checks from
the orchestrator and from each other: a new check can read whatever it needs
from the context without changing any call site.

The context carries the concrete inputs available today (standardized
DataFrame, parsed parameters, reference FASTA, module config, selected tool)
plus a generic ``reference`` slot and an ``extras`` dict so future module types
can supply their own reference data (for example a de novo ground-truth table)
without changing the context shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd

from proteobench.validation.config import ModuleValidationConfig
from proteobench.validation.fasta import FastaReference


@dataclass
class ValidationContext:
    """
    Inputs available to a validation check.

    Attributes
    ----------
    standard_df : pandas.DataFrame
        The standardized result DataFrame produced by the module parser.
    parameters : Any, optional
        Parsed parameters (a :class:`ProteoBenchParameters` or any object with
        the same attributes). ``None`` when no parameter file was provided.
    config : ModuleValidationConfig
        Module validation configuration (column names, flags, FASTA location,
        resolved profile).
    fasta : FastaReference, optional
        Reference protein identifiers, for profiles that validate against a
        sequence database. ``None`` when unavailable or not applicable.
    input_format : str, optional
        The selected software tool used to produce the results.
    reference : Any, optional
        Generic reference object for profiles whose reference is not a FASTA
        (for example a de novo ground-truth table). ``None`` when unused.
    extras : dict, optional
        Escape hatch for additional, profile-specific inputs.
    """

    standard_df: pd.DataFrame
    parameters: Any = None
    config: ModuleValidationConfig = field(default_factory=ModuleValidationConfig)
    fasta: Optional[FastaReference] = None
    input_format: Optional[str] = None
    reference: Any = None
    extras: Dict[str, Any] = field(default_factory=dict)
