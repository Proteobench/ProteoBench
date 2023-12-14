from dataclasses import dataclass
from typing import Optional


# Reference for parameter names
# https://github.com/bigbio/proteomics-sample-metadata/blob/master/sdrf-proteomics/assets/param2sdrf.yml
@dataclass
class ProteoBenchParameters:
    """
    Parameters for a proteomics search engine.

    Attributes
    ----------
    software_name : Optional[str]
        Name of the software tool / pipeline used for this benchmark run
        (examples: "MaxQuant", "AlphaPept", "Proline", ...).
    software_version : Optional[str]
        Version of the software tool / pipeline used for this benchmark run
    search_engine: Optional[str]
        Search engine used for this benchmark run
        (examples: "Andromeda", "Mascot", ...).
    search_engine_version : Optional[str]
        Version of the search engine used for this benchmark run.
    ident_fdr_psm : Optional[str]
        False discovery rate (FDR) threshold for peptide-spectrum match
        (PSM) validation ("0.01" = 1%).
    ident_fdr_peptide : Optional[str]
        False discovery rate (FDR) threshold for peptide validation ("0.01" = 1%).
    ident_fdr_protein : Optional[str]
        False discovery rate (FDR) threshold for protein validation ("0.01" = 1%).
    enable_match_between_runs : Optional[bool]
        Match between run (also named cross assignment) is enabled.
    precursor_mass_tolerance : Optional[str]
       Precursor mass tolerance used for the search,
       associated with the unit: "20 ppm" = +/- 20 ppm; if several, separate with "|".
    fragment_mass_tolerance : Optional[str]
        Precursor mass tolerance used for the search:
        "20 ppm" = +/- 20 ppm; if several, separate with "|"
    enzyme : Optional[str]
        Enzyme used as parameter for the search. If several, use "|".
    allowed_miscleavages : Optional[int]
        Maximal number of missed cleavages allowed.
    min_peptide_length : Optional[str]
        Minimum peptide length (number of residues) allowed for the search.
    max_peptide_length : Optional[str]
        Maximum peptide length (number of residues) allowed for the search.
    fixed_mods : Optional[str]
        Fixed modifications searched for in the search. If several, separate with "|".
    variable_mods : Optional[str]
        Variable modifications searched for in the search. If several, separate with "|".
    max_mods : Optional[int]
        Maximal number of modifications per peptide
        (including fixed and variable modifications).
    min_precursor_charge : Optional[int]
        Minimum precursor charge allowed.
    max_precursor_charge : Optional[int]
        Maximum precursor charge allowed.
    """

    software_name: Optional[str] = None
    software_version: Optional[str] = None
    search_engine: Optional[str] = None
    search_engine_version: Optional[str] = None
    ident_fdr_psm: Optional[str] = None  # fdr_psm
    ident_fdr_peptide: Optional[str] = None  # fdr_peptide
    ident_fdr_protein: Optional[str] = None  # fdr_protein
    enable_match_between_runs: Optional[bool] = None  # MBR
    # TODO: either add the units for the tolerance here or remove them from the webpage/plot/etc.
    precursor_mass_tolerance: Optional[str] = None  # precursor_tol, precursor_tol_unit
    fragment_mass_tolerance: Optional[str] = None  # fragment_tol, fragment_tol_unit
    enzyme: Optional[str] = None  # enzyme_name
    allowed_miscleavages: Optional[int] = None  # missed_cleavages
    min_peptide_length: Optional[str] = None  # min_pep_length
    max_peptide_length: Optional[str] = None  # max_pep_length
    fixed_mods: Optional[str] = None  # fixed_modifications
    variable_mods: Optional[str] = None  # variable_modifications
    max_mods: Optional[int] = None  # max_num_modifications
    min_precursor_charge: Optional[int] = None  # precursor_charge
    max_precursor_charge: Optional[int] = None
