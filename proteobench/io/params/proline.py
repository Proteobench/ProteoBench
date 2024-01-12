"""Proline is a quantification tool. Search engine is often Mascot.

The parameters are provided per raw file in separate sheets of an excel file.

Relevant information in sheets:
- "Search settings and infos",
- "Import and filters"
- "Quant config"
"""
import re

import pandas as pd

from proteobench.io.params import ProteoBenchParameters

use_columns = {
    "Search settings and infos": [
        "software_name",
        "software_version",
        "enzymes",
        "max_missed_cleavages",
        "fixed_ptms",
        "variable_ptms",
        "peptide_charge_states",
        "peptide_mass_error_tolerance",
        "fragment_mass_error_tolerance",
    ],
    "Import and filters": [
        "psm_filter_expected_fdr",
        "psm_filter_2",
    ],
    "Quant config": [],
}

PATTERN_MIN_PEP_LENGTH = r"\[threshold_value=([0-9].*)\]"


def find_min_pep_length(string):
    min_length = re.findall(PATTERN_MIN_PEP_LENGTH, string)[0]
    return int(min_length)


def extract_params(fname) -> ProteoBenchParameters:
    params = ProteoBenchParameters()
    excel = pd.ExcelFile(fname)

    # ! First sheet contains search settings and infos
    sheet_name = "Search settings and infos"
    cols = use_columns[sheet_name]
    # parse and validate
    sheet = excel.parse(sheet_name, dtype="object", index_col=0).T
    idx = sheet["quant_channel_name"].to_list()
    stats = sheet.describe()
    assert all(stats.loc["unique", cols] == 1), "Not all columns are unique"
    sheet = sheet[cols].drop_duplicates().reset_index(drop=True)
    # Extract
    params.software_name = "Proline"
    params.search_engine = sheet.loc[0, "software_name"]
    params.search_engine_version = sheet.loc[0, "software_version"]
    params.enzyme = sheet.loc[0, "enzymes"]
    params.allowed_miscleavages = sheet.loc[0, "max_missed_cleavages"]
    params.fixed_mods = sheet.loc[0, "fixed_ptms"]
    params.variable_mods = sheet.loc[0, "variable_ptms"]
    params.precursor_mass_tolerance = sheet.loc[0, "peptide_mass_error_tolerance"]
    params.fragment_mass_tolerance = sheet.loc[0, "fragment_mass_error_tolerance"]

    # ! Second sheet contains information about the import and filters
    sheet_name = "Import and filters"
    cols = use_columns[sheet_name]
    # parse and validate
    sheet = excel.parse(sheet_name, dtype="object", index_col=0).T.loc[idx, cols]
    stats = sheet.describe()
    assert all(stats.loc["unique", cols] == 1), "Not all columns are unique"
    sheet = sheet[cols].drop_duplicates().reset_index(drop=True)
    # Extract
    params.ident_fdr_psm = int(sheet.loc[0, "psm_filter_expected_fdr"]) / 100
    params.min_peptide_length = find_min_pep_length(sheet.loc[0, "psm_filter_2"])

    # ! Third sheet only contains match between runs (MBR) information indirectly
    sheet_name = "Quant config"
    sheet = excel.parse(sheet_name, dtype="object", index_col=0)
    enable_match_between_runs = sheet.index.str.contains("cross assignment").any()
    params.enable_match_between_runs = enable_match_between_runs
    return params


if __name__ == "__main__":
    from pathlib import Path

    file = Path("../../../test/params/Proline_example_w_Mascot_wo_proteinSets.xlsx")
    params = extract_params(file)
    data_dict = params.__dict__
    series = pd.Series(data_dict)
    series.to_csv(file.with_suffix(".csv"))
    file = Path("../../../test/params/Proline_example_2.xlsx")
    params = extract_params(file)
    data_dict = params.__dict__
    series = pd.Series(data_dict)
    series.to_csv(file.with_suffix(".csv"))
