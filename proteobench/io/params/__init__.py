"""
This module provides the `ProteoBenchParameters` dataclass for handling parameters
related to ProteoBench. The parsing is done per data analysis software.

Normalized parameters (coerced by ``normalize()``):

- ``ident_fdr_psm``, ``ident_fdr_peptide``, ``ident_fdr_protein`` — float in [0, 1]
- ``allowed_miscleavages``, ``min/max_peptide_length``,
  ``min/max_precursor_charge``, ``max_mods`` — int
- ``enable_match_between_runs`` — bool
- ``enzyme`` — canonical capitalized name (e.g. "Trypsin", "Trypsin/P", "Lys-C")

NOT normalized (kept as-is from parsers):

- ``precursor_mass_tolerance``, ``fragment_mass_tolerance`` — string, format varies
- ``fixed_mods``, ``variable_mods`` — string, tool-specific format
- ``quantification_method`` — string
- ``software_name``, ``software_version``, ``search_engine``,
  ``search_engine_version`` — string

Classes
-------
ProteoBenchParameters
    A dataclass for handling ProteoBench parameters.
"""

# Reference for parameter names
# https://github.com/bigbio/proteomics-sample-metadata/blob/master/sdrf-proteomics/assets/param2sdrf.yml
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# Strings that should be treated as missing / unset values.
_MISSING_SENTINELS = frozenset({"none", "n/a", "not specified", "unknown", "placeholder", "na", "nan", "", "-"})

# Canonical enzyme name mapping (lowercase key → display name).
_ENZYME_MAP = {
    "trypsin": "Trypsin",
    "trypsin/p": "Trypsin/P",
    "stricttrypsin": "Trypsin",
    "lys-c": "Lys-C",
    "lysc": "Lys-C",
    "arg-c": "Arg-C",
    "argc": "Arg-C",
    "asp-n": "Asp-N",
    "aspn": "Asp-N",
    "chymotrypsin": "Chymotrypsin",
    "gluc": "Glu-C",
    "glu-c": "Glu-C",
}

# Fields that must be coerced to float (FDR values, decimal 0-1).
_FLOAT_FIELDS = ("ident_fdr_psm", "ident_fdr_peptide", "ident_fdr_protein")

# Fields that must be coerced to int.
_INT_FIELDS = (
    "allowed_miscleavages",
    "min_peptide_length",
    "max_peptide_length",
    "min_precursor_charge",
    "max_precursor_charge",
    "max_mods",
)


@dataclass
class ProteoBenchParameters:
    """
    ProteoBench parameter dataclass.

    Parameters
    ----------
    filename : os.path
        Path to parameter file.
    **kwargs : dict[str, Any]
        Other keyword arguments.
    """

    def __init__(self, filename=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DDA_ion.json"), **kwargs):
        """
        Read the JSON file and initializes only the attributes present in the file.

        Parameters
        ----------
        filename : os.path
            Path to parameter file.
        **kwargs : dict[str, Any]
            Other keyword arguments.
        """
        if not os.path.isfile(filename):
            print(f"Error: File '{filename}' not found.")
            return  # No initialization happens if the file is missing

        with open(filename, "r", encoding="utf-8") as file:
            json_dict = json.load(file)

        # Initialize only the fields present in the JSON
        for key, value in json_dict.items():
            if "value" in value:
                setattr(self, key, value["value"])
            elif "placeholder" in value:
                setattr(self, key, value["placeholder"])
            else:
                setattr(self, key, None)

        for key, value in kwargs.items():
            print(key, value)
            if hasattr(self, key) and value == "None":
                setattr(self, key, np.nan)
            elif hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Custom string representation to only show initialized attributes.

        Returns
        -------
        str
            String representation to only show initialized attributes.
        """
        return str({key: value for key, value in self.__dict__.items() if value is not None})

    def fill_none(self):
        """
        Fill all None values with np.nan and normalize parameter types.
        """
        for key, value in self.__dict__.items():
            if value == "None":
                setattr(self, key, np.nan)
        self.normalize()

    def _is_missing(self, val) -> bool:
        """Return True if *val* represents a missing / unset value."""
        if val is None:
            return True
        if isinstance(val, float) and np.isnan(val):
            return True
        if isinstance(val, str) and val.strip().lower() in _MISSING_SENTINELS:
            return True
        return False

    def normalize(self):
        """
        Coerce parsed parameter values to their canonical types.

        This method is called automatically at the end of ``fill_none()`` so
        that every parser benefits without per-parser changes.

        Normalization rules
        -------------------
        1. Any attribute whose value is a missing sentinel string (e.g.
           ``"not specified"``, ``"N/A"``, ``"None"``, ``""``) is set to
           ``np.nan``.
        2. FDR fields are coerced to ``float`` in the range [0, 1]. Values
           ``> 1`` are assumed to be percentages and divided by 100.
        3. Integer fields (miscleavages, peptide length, charge, max_mods)
           are coerced to ``int``.
        4. ``enable_match_between_runs`` is coerced to ``bool``.
        5. ``enzyme`` is mapped to a canonical name via ``_ENZYME_MAP``.
        """
        # A. Sanitize missing values across ALL attributes
        for key, val in list(self.__dict__.items()):
            if self._is_missing(val):
                setattr(self, key, np.nan)

        # B. Float coercion (FDR fields)
        for fld in _FLOAT_FIELDS:
            val = getattr(self, fld, None)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                continue
            try:
                val = float(val)
                if val >= 1:  # percentage → decimal (FDR is always < 1)
                    val /= 100
                setattr(self, fld, val)
            except (ValueError, TypeError):
                setattr(self, fld, np.nan)

        # C. Integer coercion
        for fld in _INT_FIELDS:
            val = getattr(self, fld, None)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                continue
            try:
                setattr(self, fld, int(float(val)))
            except (ValueError, TypeError):
                setattr(self, fld, np.nan)

        # D. Boolean coercion
        val = getattr(self, "enable_match_between_runs", None)
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            if isinstance(val, bool):
                pass  # already correct
            elif isinstance(val, str):
                setattr(
                    self,
                    "enable_match_between_runs",
                    val.strip().lower() in ("true", "1", "yes"),
                )
            else:
                try:
                    setattr(self, "enable_match_between_runs", bool(val))
                except (ValueError, TypeError):
                    setattr(self, "enable_match_between_runs", np.nan)

        # --- E. Enzyme name normalization -----------------------------------
        val = getattr(self, "enzyme", None)
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            if isinstance(val, str):
                canonical = _ENZYME_MAP.get(val.strip().lower())
                if canonical is not None:
                    setattr(self, "enzyme", canonical)
                # If not in map, keep original value as-is


# Automatically initialize from fields.json if run directly
if __name__ == "__main__":
    proteo_params = ProteoBenchParameters()
    print(proteo_params)
