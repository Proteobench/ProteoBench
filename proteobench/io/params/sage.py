"""Proline is a quantification tool. Search engine is often Mascot.

The parameters are provided per raw file in separate sheets of an excel file.

Relevant information in sheets:
- "Search settings and infos",
- "Import and filters"
- "Quant config"
"""

import json

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname) -> ProteoBenchParameters:
    params = ProteoBenchParameters()

    try:
        file_contents = fname.getvalue().decode("utf-8")
        data = json.loads(file_contents)
    except AttributeError:
        file_contents = open(fname)
        data = json.load(file_contents)

    params.software_name = "Sage"
    params.software_version = data["version"]
    params.search_engine = "Sage"
    params.search_engine_version = data["version"]
    params.enzyme = data["database"]["enzyme"]["cleave_at"]
    params.allowed_miscleavages = data["database"]["enzyme"]["missed_cleavages"]
    params.fixed_mods = data["database"]["static_mods"]
    params.variable_mods = data["database"]["variable_mods"]
    try:
        params.precursor_mass_tolerance = data["precursor_tol"]["ppm"]
    except KeyError:
        params.precursor_mass_tolerance = data["precursor_tol"]["Da"]
    params.fragment_mass_tolerance = data["fragment_tol"]["ppm"]
    params.min_peptide_length = data["database"]["enzyme"]["min_len"]
    params.max_peptide_length = data["database"]["enzyme"]["max_len"]
    params.max_mods = data["database"]["max_variable_mods"]
    params.min_precursor_charge = data["precursor_charge"][0]
    params.max_precursor_charge = data["precursor_charge"][1]
    params.enable_match_between_runs = True
    return params


if __name__ == "__main__":
    from pathlib import Path

    file = Path("../../../test/params/sage_results.json")
    params = extract_params(file)
    data_dict = params.__dict__
    series = pd.Series(data_dict)
    series.to_csv(file.with_suffix(".csv"))
