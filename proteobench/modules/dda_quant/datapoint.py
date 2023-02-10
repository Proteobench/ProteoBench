import json
from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class Datapoint:
    """Data used to stored the"""

    id: str = None
    search_engine: str = None
    software_version: int = 0
    fdr_psm: int = 0
    fdr_peptide: int = 0
    fdr_protein: int = 0
    MBR: bool = False
    precursor_tol: int = 0
    precursor_tol_unit: str = "Da"
    fragmnent_tol: int = 0
    fragment_tol_unit: str = "Da"
    enzyme_name: str = None
    missed_cleavages: int = 0
    min_pep_length: int = 0
    max_pep_length: int = 0
    weighted_sum: int = 0
    nr_prec: int = 0
    is_temporary: bool = True
    # fixed_mods: [],
    # variable_mods: [],
    # max_number_mods_pep: int = 0,
    # precursor_charge: int = 0,
    # reproducibility: int = 0,
    # mean_reproducibility: int = 0,

    def calculate_missing_quan_prec(self, df, nr_missing_0):
        nr_quan_prec_missing = []

        return nr_quan_prec_missing

    def calculate_plot_data(self, df):
        species = ["YEAST", "HUMAN", "ECOLI"]
        prop_ratios = []
        sum_ratios = 0
        nr_missing_0 = 0
        for spec in species:
            f = len(df[df[spec] == True])
            sum_s = (df[df[spec] == True]["1|2_expected_ratio_diff"]).sum()
            ratio = sum_s / f
            prop_ratio = (f / len(df)) * ratio
            prop_ratios.append(prop_ratio)
            sum_ratios += prop_ratio
            nr_missing_0 += f

        self.weighted_sum = round(sum_ratios, ndigits=3)
        self.nr_prec = len(df)

    def generate_id(self):
        self.id = (
            self.search_engine
            + "_"
            + str(self.software_version)
            + "_"
            + str(datetime.timestamp(datetime.now()))
        )
        print(self.id)

    def dump_json_object(self, file_name):
        f = open(file_name, "a")
        f.write(json.dumps(asdict(self)))
        f.close()
