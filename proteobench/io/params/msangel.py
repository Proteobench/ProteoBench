"""
MSAngel creates modular pipelines that allows several search engines to identify
peptides, which are then quantified with Proline.
The parameters are provided in a .json file.
MSAngel allows for multiple search engines to be used in the same pipeline. So it
requires a list of search engines and their respective parameters, which are then
concatenated.

Relevant information in file:
-
"""

import json
import pathlib
from typing import Union

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def extract_search_engine(search_params: list) -> dict:
    """
    Extract search engine name from the JSON data.
    It only works for workflows using a single search engine.

    Parameters
    ----------
    search_params : list
        The list of search parameters extracted from the JSON file.

    Returns
    -------
    dict
        The search engine name.
    """

    for each_search_params in search_params["operations"]:
        if "searchEnginesWithForms" in each_search_params:
            return each_search_params["searchEnginesWithForms"][0][0]


def extract_params_mascot_specific(search_params: list, input_params: ProteoBenchParameters) -> ProteoBenchParameters:
    """
    Extract search parameters from the JSON data of a workflow running Mascot.
    Adds them to the partially completed input_params ProteoBenchParameters object.

    Parameters
    ----------
    search_params : list
        The list of search parameters extracted from the JSON file.
    input_params : ProteoBenchParameters
        The partially completed input_params object.

    Returns
    -------
    ProteoBenchParameters
        The input_params object with the extracted parameters added.
    """

    for each_search_params in search_params["operations"]:
        if "searchEnginesWithForms" in each_search_params:
            # params.search_engine_version =
            input_params.enzyme = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["CLE"]
            # params.allowed_miscleavages =
            input_params.fixed_mods = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["MODS"]
            input_params.variable_mods = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["IT_MODS"]
            input_params.allowed_miscleavages = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["PFA"]
            second_pass = input_params.allowed_miscleavages = each_search_params["searchEnginesWithForms"][0][1][
                "paramMap"
            ]["ERRORTOLERANT"]
            if second_pass == "1":
                input_params.second_pass = True
            else:
                input_params.second_pass = False
            # get tolerance:
            tol = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["TOL"]
            unit = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["TOLU"]
            tol = float(tol)
            print(tol)
            input_params.precursor_mass_tolerance = "[-" + str(tol) + " " + unit + ", +" + str(tol) + " " + unit + "]"

        if "validationConfig" in each_search_params:
            input_params.ident_fdr_psm = each_search_params["validationConfig"]["psmExpectedFdr"] / 100
            # input_params.min_peptide_length = each_search_params["validationConfig"]["psmFilters"] #TODO: I am not sure if this is the max or min length

    return input_params


def extract_params_xtandem_specific(search_params: list, input_params: ProteoBenchParameters) -> ProteoBenchParameters:
    """
    Extract search parameters from the JSON data of a workflow running X!Tandem.
    Adds them to the partially completed input_params ProteoBenchParameters object.

    Parameters
    ----------
    search_params : list
        The list of search parameters extracted from the JSON file.
    input_params : ProteoBenchParameters
        The partially completed input_params object.

    Returns
    -------
    ProteoBenchParameters
        The input_params object with the extracted parameters added.
    """

    for each_search_params in search_params["operations"]:
        if "searchEnginesWithForms" in each_search_params:
            # params.search_engine_version =
            input_params.enzyme = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["digestionParameters"][
                "enzymes"
            ][0]["name"]
            # params.allowed_miscleavages =
            input_params.fixed_mods = ", ".join(
                each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["modificationParameters"][
                    "fixedModifications"
                ]
            )
            input_params.variable_mods = ", ".join(
                each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["modificationParameters"][
                    "variableModifications"
                ]
            )
            ## get value of each_search_params['searchEnginesWithForms'][0][1]["paramMap"]["digestionParameters"]["nMissedCleavages"] where key == input_params.enzyme
            n_missed_cleavages_dict = each_search_params["searchEnginesWithForms"][0][1]["paramMap"][
                "digestionParameters"
            ]["nMissedCleavages"]
            input_params.allowed_miscleavages = n_missed_cleavages_dict.get(input_params.enzyme, None)
            # get tolerance for precursors:
            tol = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["precursorTolerance"]
            unit = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["precursorAccuracyType"]
            tol = float(tol)
            input_params.precursor_mass_tolerance = "[-" + str(tol) + " " + unit + ", +" + str(tol) + " " + unit + "]"
            # get tolerance for fragments:
            tol2 = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["fragmentIonMZTolerance"]
            unit2 = each_search_params["searchEnginesWithForms"][0][1]["paramMap"]["fragmentAccuracyType"]
            tol2 = float(tol2)
            input_params.fragment_mass_tolerance = (
                "[-" + str(tol2) + " " + unit2 + ", +" + str(tol2) + " " + unit2 + "]"
            )

            # Add "hidden" modifications when using X!Tandem:
            for key, value in each_search_params["searchEnginesWithForms"][0][1]["paramMap"][
                "algorithmParameters"
            ].items():
                if value["type"] == "com.compomics.util.parameters.identification.tool_specific.XtandemParameters":
                    if value["data"]["proteinQuickAcetyl"] == True:
                        input_params.variable_mods = input_params.variable_mods + ";Acetyl(N-term)"
                    if value["data"]["quickPyrolidone"] == True:
                        input_params.variable_mods = input_params.variable_mods + ";Pyrolidone(N-term)"

        if "validationConfig" in each_search_params:
            input_params.ident_fdr_psm = each_search_params["validationConfig"]["psmExpectedFdr"] / 100
            # input_params.min_peptide_length = each_search_params["validationConfig"]["psmFilters"] #TODO: I am not sure if this is the max or min length

    return input_params


def extract_params(fname: Union[str, pathlib.Path]) -> ProteoBenchParameters:
    """
    Parse MSAangel quantification tool JSON parameter file and extract relevant parameters.

    Parameters
    ----------
    fname : str or pathlib.Path
        The path to the MSAngel JSON parameter file.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a `ProteoBenchParameters` object.
    """
    params = ProteoBenchParameters()

    try:
        # If the input is a file-like object (e.g., StringIO), decode it
        file_contents = fname.getvalue().decode("utf-8")
        data = json.loads(file_contents)
    except AttributeError:
        # Otherwise, treat it as a file path
        with open(fname, "r") as file_contents:
            data = json.load(file_contents)

    # Extract parameters from the JSON data
    params.software_name = "MSAngel"
    params.software_version = data["msAngelVersion"]
    params.search_engine = extract_search_engine(data)

    # Params fixed in MSAngel
    params.enable_match_between_runs = True

    # parameter parsing depends on the search engine used
    if params.search_engine == "Mascot":
        extract_params_mascot_specific(data, params)
    elif params.search_engine == "X!Tandem":
        extract_params_xtandem_specific(data, params)

    params.fill_none()

    return params


if __name__ == "__main__":
    """
    Extract parameters from MSAngel JSON files and save them as CSV.
    """
    from pathlib import Path

    file = Path("../../../test/params/MSAngel_Xtandem-export-param.json")

    # Extract parameters from the file
    params = extract_params(file)

    # Convert the extracted parameters to a dictionary and then to a pandas Series
    data_dict = params.__dict__
    series = pd.Series(data_dict)

    # Write the Series to a CSV file
    series.to_csv(file.with_suffix(".csv"))
