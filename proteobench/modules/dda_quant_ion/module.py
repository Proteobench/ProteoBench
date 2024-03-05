from __future__ import annotations

import pandas as pd

from proteobench.io.params import ProteoBenchParameters
from proteobench.modules.dda_quant_base.module import Module
from proteobench.modules.dda_quant_base.parse import aggregate_modification_column
from proteobench.modules.dda_quant_ion.parse import ParseInputs
from proteobench.modules.dda_quant_ion.parse_settings import ParseSettings


class IonModule(Module):
    """Object is used as a main interface with the Proteobench library within the module."""

    def __init__(self, module_settings):
        super().__init__(module_settings)

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
            input_data_frame = IonModule.load_input_file_Proline(input_csv)

        elif input_format == "i2MassChroQ":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["ProForma"]
        elif input_format == "Custom":
            input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
            input_data_frame["proforma"] = input_data_frame["Modified sequence"]

        return input_data_frame


    @staticmethod
    def load_input_file_Proline(input_csv):
        input_data_frame = pd.read_excel(
            input_csv,
            sheet_name="Quantified peptide ions",
            header=0,
            index_col=None,
        )
        input_data_frame["modifications"].fillna("", inplace=True)
        input_data_frame["subsets_accessions"].fillna("", inplace=True)
        input_data_frame["proforma"] = input_data_frame.apply(
            lambda x: aggregate_modification_column(x.sequence, x.modifications),
            axis=1,
        )
        input_data_frame["proteins"] = input_data_frame["samesets_accessions"] + input_data_frame[
            "subsets_accessions"
        ].apply(lambda x: "; " + x if len(x) > 0 else "")
        input_data_frame["proteins"] = input_data_frame["proteins"].apply(
            lambda x: "; ".join(sorted(x.split("; ")))
        )
        input_data_frame.drop_duplicates(
            subset=["proforma", "master_quant_peptide_ion_charge", "proteins"], inplace=True
        )
        group_cols = ["proforma", "master_quant_peptide_ion_charge"]
        agg_funcs = {col: "first" for col in input_data_frame.columns if col not in group_cols + ["proteins"]}
        input_data_frame = (
            input_data_frame.groupby(group_cols)
            .agg({"proteins": lambda x: "; ".join(x), **agg_funcs})
            .reset_index()
        )
        return input_data_frame
