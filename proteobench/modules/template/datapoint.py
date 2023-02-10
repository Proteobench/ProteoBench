import json
from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class Datapoint:
    """Data used to stored the experimental metadata and data analysis settings"""

    # Fixed metadata
    id: str = None
    is_temporary: bool = True
    # add/remove for each module
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

    def calculate_benchmarking_metric_1(self, intermediate_data):
        # TODO: calculate metric 1
        metric_1 = 0

        return metric_1

    def calculate_benchmarking_metric_2(self, intermediate_data):
        # TODO: calculate metric 1
        metric_2 = 0

        return metric_2

    # TODO: add more functions to calculate the benchmarking metrics

    # Leave this functions as it is
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
