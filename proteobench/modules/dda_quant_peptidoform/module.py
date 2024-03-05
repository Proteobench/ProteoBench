from __future__ import annotations

import pandas as pd

from proteobench.modules.dda_quant_base.module import Module
from proteobench.modules.dda_quant_peptidoform.parse import (
    ParseInputs,
    aggregate_modification_column,
)
from proteobench.modules.dda_quant_peptidoform.parse_settings import ParseSettings


class PeptidoformModule(Module):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(self, parse_settings):
        super().__init__(parse_settings)

    def is_implemented(self) -> bool:
        """Returns whether the module is fully implemented."""
        return True


    def load_input_file(self, input_csv: str, input_format: str) -> pd.DataFrame:
        """Method loads dataframe from a csv depending on its format."""
        input_data_frame: pd.DataFrame

        if input_format == "MaxQuant":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
            input_data_frame["proforma"] = input_data_frame["Sequence"]
        elif input_format == "AlphaPept":
            input_data_frame = pd.read_csv(input_csv, low_memory=False)
        elif input_format == "Sage":
            input_data_frame = pd.read_csv(input_csv, sep="\t", low_memory=False)
        elif input_format == "FragPipe":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["Peptide Sequence"]
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
