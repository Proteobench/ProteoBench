from dataclasses import dataclass
from typing import Optional


@dataclass
class ProteoBenchParameters:
    search_engine: Optional[str] = None
    software_version: Optional[str] = None
    fdr_psm: Optional[str] = None
    fdr_peptide: Optional[str] = None
    fdr_protein: Optional[str] = None
    MBR: Optional[str] = None
    precursor_tol: Optional[str] = None
    precursor_tol_unit: Optional[str] = None
    fragment_tol: Optional[str] = None
    fragment_tol_unit: Optional[str] = None
    enzyme_name: Optional[str] = None
    missed_cleavages: Optional[str] = None
    min_pep_length: Optional[str] = None
    max_pep_length: Optional[str] = None
    fixed_modifications: Optional[str] = None
    variable_modifications: Optional[str] = None
    max_num_modifications: Optional[str] = None
    precursor_charge: Optional[str] = None


# params = ProteoBenchParameters()
# params.search_engine = "MaxQuant"
# params
# %%
