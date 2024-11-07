import pandas as pd
import pathlib

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname: str) -> ProteoBenchParameters:
    """Parse MSAID params file and extract relevant parameters."""
    # Some default and flag settings
    parameters = {
        "software_name": "MSAID",
        "search_engine": "Chimerys",
        "search_engine_version": "4.1.1",
        "quantification_method": "MS2 Area",
        "ident_fdr_psm": "0.01",
        "ident_fdr_peptide": "0.01",
        "ident_fdr_protein": "0.01",
        "enable_match_between_runs": False,
    }

    # Read the params file
    file = pd.read_csv(fname)
    # Convert the file to a dictionary
    params_dict = dict(file.itertuples(False, None))

    parameters["search_engine"] = params_dict["Algorithm"].split(" ")[0]
    parameters["search_engine_version"] = params_dict["Algorithm"].split(" ")[1]
    parameters["fragment_mass_tolerance"] = params_dict["Fragment Mass Tolerance"]
    parameters["enzyme"] = params_dict["Enzyme"]
    parameters["allowed_miscleavages"] = params_dict["Max. Missed Cleavage Sites"]
    parameters["min_peptide_length"] = params_dict["Min. Peptide Length"]
    parameters["max_peptide_length"] = params_dict["Max. Peptide Length"]
    parameters["fixed_mods"] = params_dict["Static Modifications"]
    parameters["variable_mods"] = params_dict["Variable Modifications"]
    parameters["max_mods"] = params_dict["Maximum Number of Modifications"]
    parameters["min_precursor_charge"] = params_dict["Min. Peptide Charge"]
    parameters["max_precursor_charge"] = params_dict["Max. Peptide Charge"]
    parameters["quantification_method"] = params_dict["Quantification Type"]
    if "Quan in all file" in parameters["quantification_method"]:
        parameters["enable_match_between_runs"] = True
    else:
        parameters["enable_match_between_runs"] = False

    return ProteoBenchParameters(**parameters)


if __name__ == "__main__":
    for fname in [
        "../../../test/params/MSAID_default_params.csv",
    ]:
        file = pathlib.Path(fname)
        params = extract_params(file)
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.with_suffix(".tsv"), sep="\t")
