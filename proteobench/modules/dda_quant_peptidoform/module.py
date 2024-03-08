from __future__ import annotations

import pandas as pd

from proteobench.modules.dda_quant_base.module import Module
from proteobench.modules.dda_quant_peptidoform.parse import (
    ParseInputs,
    aggregate_modification_column,
)
from proteobench.modules.dda_quant_peptidoform.parse_settings import (
    DDA_QUANT_RESULTS_PATH,
    DDA_QUANT_RESULTS_REPO,
    PRECURSOR_NAME,
    ParseSettings,
)


class PeptidoformModule(Module):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(self):
        self.dda_quant_results_repo = DDA_QUANT_RESULTS_REPO
        self.precursor_name = PRECURSOR_NAME

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True

    def load_input_file(self, input_csv: str, input_format: str) -> pd.DataFrame:
        """Method loads dataframe from a csv depending on its format."""
        input_data_frame: pd.DataFrame

        if input_format == "MaxQuant":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "AlphaPept":
            input_data_frame = pd.read_csv(input_csv, low_memory=False)
        elif input_format == "Sage":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "FragPipe":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
        elif input_format == "WOMBAT":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
            input_data_frame["proforma"] = input_data_frame["modified_peptide"]
        elif input_format == "Proline":
            input_data_frame = pd.read_excel(
                input_csv,
                sheet_name="Quantified peptide ions",
                header=0,
                index_col=None,
            )
            # TODO this should be generalized further, maybe even moved to parsing param in toml
            input_data_frame["modifications"].fillna("", inplace=True)
            input_data_frame["proforma"] = input_data_frame.apply(
                lambda x: aggregate_modification_column(x.sequence, x.modifications),
                axis=1,
            )
        elif input_format == "i2MassChroQ":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["ProForma"]
        elif input_format == "Custom":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["Modified sequence"]

        return input_data_frame

    def benchmarking(
        self, input_file: str, input_format: str, user_input: dict, all_datapoints, default_cutoff_min_prec: int = 3
    ) -> pd.DataFrame:
        """Main workflow of the module. Used to benchmark workflow results."""

        # Parse user config
        input_df = self.load_input_file(input_file, input_format)
        parse_settings = ParseSettings(input_format)

        standard_format, replicate_to_raw = ParseInputs().convert_to_standard_format(input_df, parse_settings)

        # Get quantification data
        intermediate_data_structure = self.generate_intermediate(standard_format, replicate_to_raw, parse_settings)

        current_datapoint = self.generate_datapoint(
            intermediate_data_structure, input_format, user_input, default_cutoff_min_prec=default_cutoff_min_prec
        )

        all_datapoints = self.add_current_data_point(all_datapoints, current_datapoint)

        # TODO check why there are NA and inf/-inf values
        return (
            intermediate_data_structure,
            all_datapoints,
            input_df,
        )
