"""
I2MassChroQ parameter file parser.
"""

import os
import pathlib

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

MODIFICATION_MAPPING = {
    # X!Tandem format: mass@residue
    "57.02146@C": "C[Carbamidomethyl]",
    "15.99491@M": "M[Oxidation]",
    "+42.01056@[": "N-term[Acetyl]",
    "-18.0106@^E": "N-term E[Pyro-glu]",
    "-17.0265@^Q": "N-term Q[Pyro-glu]",
    # X!Tandem "quick" options
    "Acetyl(N-term)": "N-term[Acetyl]",
    "Pyrolidone(N-term)": "N-term[Pyrolidone]",
    # Sage format: residue:mass or ^residue:mass
    "C:57.021465": "C[Carbamidomethyl]",
    "M:15.994915": "M[Oxidation]",
    "^E:-18.010565": "N-term E[Pyro-glu]",
    "^Q:-17.026548": "N-term Q[Pyro-glu]",
}


def _homogenize_mods(raw_mods: str, sep: str = ";") -> str:
    """Map raw modification strings to ProForma-like format using MODIFICATION_MAPPING.

    Splits on *sep*, looks up each token, and falls back to the raw token if not found.
    """
    if not raw_mods or not raw_mods.strip():
        return ""
    mapped = []
    for mod in raw_mods.split(sep):
        mod = mod.strip()
        if not mod:
            continue
        mapped.append(MODIFICATION_MAPPING.get(mod, mod))
    return ", ".join(mapped)


def _extract_xtandem_params(
    params: pd.Series, json_file=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DDA_ion.json")
) -> ProteoBenchParameters:
    """
    Parse i2MassChroQ parameters when with X!Tandem is used.

    Parameters
    ----------
    params : pd.Series
        The parameters extracted from the i2MassChroQ parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    _tol_frag = "{} {}".format(
        params.loc["spectrum, fragment monoisotopic mass error"],
        params.loc["spectrum, fragment monoisotopic mass error units"].replace("Daltons", "Da"),
    )

    # Construct tolerance strings for parent mass error
    _tol_prec_lower = "{} {}".format(
        params.loc["spectrum, parent monoisotopic mass error minus"],
        params.loc["spectrum, parent monoisotopic mass error units"].replace("Daltons", "Da"),
    )

    _tol_prec_upper = "{} {}".format(
        params.loc["spectrum, parent monoisotopic mass error plus"],
        params.loc["spectrum, parent monoisotopic mass error units"].replace("Daltons", "Da"),
    )

    # Max missed cleavage sites, either from scoring or refinement
    max_cleavage = params.loc["scoring, maximum missed cleavage sites"]
    if params.loc["refine"] == "yes":
        max_cleavage = int(params.loc["refine, maximum missed cleavage sites"])

    _enzyme = str(params.loc["protein, cleavage site"])

    if params.loc["protein, cleavage semi"] == "yes":
        _semi_enzymatic = True
    elif params.loc["protein, cleavage semi"] == "no":
        _semi_enzymatic = False
    else:
        raise ValueError(f"Unknown value for protein, cleavage semi: {params.loc['protein, cleavage semi']}")

    fixed_mods_list = list(params.loc[params.index.str.contains("residue, modification mass")].dropna())
    var_mods_list = list(params.loc[params.index.str.contains("residue, potential modification mass")].dropna())

    # Add "hidden" modifications when using X!Tandem:
    if params.loc["protein, quick acetyl"] == "yes":
        var_mods_list.append("Acetyl(N-term)")
    if params.loc["protein, quick pyrolidone"] == "yes":
        var_mods_list.append("Pyrolidone(N-term)")

    # Create and return a ProteoBenchParameters object with the extracted values
    params = ProteoBenchParameters(
        filename=json_file,
        software_name="i2MassChroQ",
        software_version=params.loc["i2MassChroQ_VERSION"],
        search_engine=params.loc["AnalysisSoftware_name"].replace("X! ", "X!"),  # Normalize the search engine name
        search_engine_version=str(params.loc["AnalysisSoftware_version"] or ""),
        ident_fdr_psm=float(params.loc["psm_fdr"]),
        ident_fdr_peptide=float(params.loc["peptide_fdr"]),
        ident_fdr_protein=float(params.loc["protein_fdr"]),
        # set match between runs to True if it is enabled
        enable_match_between_runs=True if params.loc["mcq_mbr"] == "T" else False,
        precursor_mass_tolerance="[-" + _tol_prec_lower + ", " + _tol_prec_upper + "]",
        fragment_mass_tolerance="[-" + _tol_frag + ", " + _tol_frag + "]",
        enzyme=_enzyme,
        semi_enzymatic=_semi_enzymatic,
        allowed_miscleavages=max_cleavage,
        min_peptide_length=None,  # xtandem: "spectrum, minimum fragment mz"
        max_peptide_length=None,
        fixed_mods=_homogenize_mods(";".join(fixed_mods_list)),
        variable_mods=_homogenize_mods(";".join(var_mods_list)),
        max_mods=None,
        min_precursor_charge=None,
        max_precursor_charge=int(params.loc["spectrum, maximum parent charge"]),
    )
    params.fill_none()
    return params


def _extract_sage_params(
    params: pd.Series, json_file=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DDA_ion.json")
) -> ProteoBenchParameters:
    """
    Parse i2MassChroQ parameters when Sage is used.

    Parameters
    ----------
    params : pd.Series
        The parameters extracted from the i2MassChroQ parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    # Construct tolerance strings for fragment and parent mass errors
    fragment_mass_tolerance = params.loc["sage_fragment_tol"]  # e.g '-0.02 0.02 da'

    # Construct tolerance strings for parent mass error
    precursor_mass_tolerance = params.loc["sage_precursor_tol"]  # e.g. "-10 10 ppm"

    # Max missed cleavage sites, either from scoring or refinement
    max_cleavage = int(params.loc["sage_database_enzyme_missed_cleavages"])  # e.g. "2"

    _enzyme = "{}{},{}".format(
        params.loc["sage_database_enzyme_cleave_at"],
        (
            "|{}".format(params.loc["sage_database_enzyme_restrict"])
            if "sage_database_enzyme_restrict" in params.index
            else ""
        ),
        params.loc["sage_database_enzyme_c_terminal"],
    )  # e.g. "KR" and "sage_database_enzyme_restrict"	"P" and 'sage_database_enzyme_c_terminal'	"true"
    # Replace the enzyme pattern with the enzyme name used in ProteoBench
    # if _enzyme == "[RK]|{P}":
    #     _enzyme = "Trypsin"
    # elif _enzyme == "[RK]":
    #     _enzyme = "Trypsin/P"

    # Sage uses space-separated mods; convert to ", " for _homogenize_mods
    fixed_mods_list = params.loc["sage_database_static_mods"].replace(" ", ", ")  # C:57.021465
    var_mods_list = params.loc["sage_database_variable_mods"].replace(" ", ", ")  # "M:15.994915, ^E:-18.010565, ^Q:-17.026548"

    min_precursor_charge, max_precursor_charge = params.loc["sage_precursor_charge"].split()

    # Create and return a ProteoBenchParameters object with the extracted values
    params = ProteoBenchParameters(
        filename=json_file,
        software_name="i2MassChroQ",
        software_version=params.loc["i2MassChroQ_VERSION"],
        search_engine=params.loc["AnalysisSoftware_name"],
        search_engine_version=str(params.loc["AnalysisSoftware_version"] or ""),
        ident_fdr_psm=float(params.loc["psm_fdr"]),
        ident_fdr_peptide=float(params.loc["peptide_fdr"]),
        ident_fdr_protein=float(params.loc["protein_fdr"]),
        # set match between runs to True if it is enabled
        enable_match_between_runs=True if params.loc["mcq_mbr"] == "T" else False,
        precursor_mass_tolerance=precursor_mass_tolerance,
        fragment_mass_tolerance=fragment_mass_tolerance,
        enzyme=_enzyme,
        semi_enzymatic=False,  # i2masschroq does not propagate this parameter
        allowed_miscleavages=max_cleavage,
        min_peptide_length=int(params.loc["sage_database_enzyme_min_len"]),  # 5
        max_peptide_length=int(params.loc["sage_database_enzyme_max_len"]),  # 50
        fixed_mods=_homogenize_mods(fixed_mods_list, sep=", "),
        variable_mods=_homogenize_mods(var_mods_list, sep=", "),
        max_mods=int(params.loc["sage_database_max_variable_mods"]),  # 2
        min_precursor_charge=int(min_precursor_charge),
        max_precursor_charge=int(max_precursor_charge),
        json_file=json_file,
    )
    params.fill_none()
    return params


def extract_params(
    fname: pathlib.Path, json_file=os.path.join(os.path.dirname(__file__), "json/Quant/quant_lfq_DDA_ion.json")
) -> ProteoBenchParameters:
    """
    Extract parameters from an i2MassChroQ parameter file and return a `ProteoBenchParameters` object.

    Parameters
    ----------
    fname : pathlib.Path
        The file path to the i2MassChroQ parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters encapsulated in a `ProteoBenchParameters` object.
    """
    # Read parameters from the file
    params = pd.read_csv(fname, sep="\t", header=None, index_col=0).squeeze()

    if params.loc["AnalysisSoftware_name"] in ["X!Tandem", "X! Tandem"]:
        return _extract_xtandem_params(params, json_file=json_file)
    elif params.loc["AnalysisSoftware_name"] == "Sage":
        return _extract_sage_params(params, json_file=json_file)
    else:
        raise ValueError(f"Unsupported search engine: {params.loc['AnalysisSoftware_name']}")


if __name__ == "__main__":
    # Reads i2MassChroQ parameter files, extracts parameters, and writes them to CSV files.
    # List of parameter file paths
    base_dir = pathlib.Path("../../../test/params/")
    for fname in [
        "i2mproteobench_2pep_fdr01psm_fdr01prot_xtandem.tsv",
        "i2mq_result_parameters.tsv",
        "i2mproteobench_params_sage.tsv",
    ]:
        file = base_dir / fname

        # Read the parameter file to extract parameters
        params = pd.read_csv(file, sep="\t", header=None, index_col=0).squeeze()
        params = extract_params(file.with_suffix(".tsv"))

        # Convert the parameters to a dictionary and then to a pandas Series
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        print(series)

        # Write the Series to a CSV file
        series.to_csv(file.parent / (file.stem + "_sel.csv"))
