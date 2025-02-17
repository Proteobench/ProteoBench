import datetime

import pytest

from proteobench.datapoint.quant_datapoint import QuantDatapoint

DATAPOINT_USER_INPUT_TYPE = {
    "DDA_MaxQuant": {
        "software_name": "MaxQuant",
        "software_version": "1.0",
        "search_engine_version": "1.0",
        "search_engine": "MaxQuant",
        "ident_fdr_psm": 0.01,
        "ident_fdr_peptide": 0.05,
        "ident_fdr_protein": 0.1,
        "enable_match_between_runs": 1,
        "precursor_mass_tolerance": "0.02 Da",
        "fragment_mass_tolerance": "0.02 Da",
        "enzyme": "Trypsin",
        "allowed_miscleavages": 1,
        "min_peptide_length": 6,
        "max_peptide_length": 30,
    },
    "DIA_DIA-NN": {
        "software_name": "DIA-NN",
        "software_version": "1.9",
        "search_engine_version": "1.9",
        "search_engine": "DIA-NN",
        "ident_fdr_peptide": 0.01,
        "ident_fdr_psm": 0.01,
        "ident_fdr_protein": 0.01,
        "enable_match_between_runs": 1,
        "enzyme": "Trypsin",
        "allowed_miscleavages": 1,
        "min_peptide_length": 6,
        "max_peptide_length": 40,
        "precursor_mass_tolerance": None,
        "fragment_mass_tolerance": None,
    },
}


class TestQuantDatapoint:
    @pytest.mark.parametrize("input_type", DATAPOINT_USER_INPUT_TYPE.keys())
    def test_Datapoint_constructor(self, input_type):
        input_format = DATAPOINT_USER_INPUT_TYPE[input_type]["software_name"]
        user_input = DATAPOINT_USER_INPUT_TYPE[input_type]
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

        QuantDatapoint(
            id=input_format + "_" + user_input["software_version"] + "_" + formatted_datetime,
            software_name=input_format,
            software_version=user_input["software_version"],
            search_engine=user_input["search_engine"],
            search_engine_version=user_input["search_engine_version"],
            ident_fdr_psm=user_input["ident_fdr_psm"],
            ident_fdr_peptide=user_input["ident_fdr_peptide"],
            ident_fdr_protein=user_input["ident_fdr_protein"],
            enable_match_between_runs=user_input["enable_match_between_runs"],
            precursor_mass_tolerance=user_input["precursor_mass_tolerance"],
            fragment_mass_tolerance=user_input["fragment_mass_tolerance"],
            enzyme=user_input["enzyme"],
            allowed_miscleavages=user_input["allowed_miscleavages"],
            min_peptide_length=user_input["min_peptide_length"],
            max_peptide_length=user_input["max_peptide_length"],
        )
