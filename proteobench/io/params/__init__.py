from dataclasses import dataclass
from typing import Optional


# Reference for parameter names
# https://github.com/bigbio/proteomics-sample-metadata/blob/master/sdrf-proteomics/assets/param2sdrf.yml
# new name as comment
@dataclass
class ProteoBenchParameters:
    search_engine: Optional[str] = None
    software_version: Optional[str] = None
    fdr_psm: Optional[str] = None  # ident_fdr_psm
    fdr_peptide: Optional[str] = None  # ident_fdr_peptide
    fdr_protein: Optional[str] = None  # ident_fdr_protein
    MBR: Optional[str] = None  # enable_match_between_runs
    precursor_tol: Optional[
        str
    ] = None  # precursor_mass_tolerance, value and unit not separated
    precursor_tol_unit: Optional[str] = None
    fragment_tol: Optional[
        str
    ] = None  # fragment_mass_tolerance, value and unit not separated
    fragment_tol_unit: Optional[str] = None
    enzyme_name: Optional[str] = None  # enzyme
    missed_cleavages: Optional[str] = None  # allowed_miscleavages
    min_pep_length: Optional[str] = None  # min_peptide_length
    max_pep_length: Optional[str] = None  # max_peptide_length
    fixed_modifications: Optional[str] = None  # fixex_mods
    variable_modifications: Optional[str] = None  # variable_mods
    max_num_modifications: Optional[str] = None  # max_mods
    precursor_charge: Optional[str] = None  # min_precursor_charge
