import json
from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class Datapoint:
    """Data used to store the experimental metadata and data analysis settings.

    Example for attributes:
        id: A unique identifier for the datapoint.
        is_temporary: A boolean flag indicating whether the datapoint is temporary or not.
        search_engine: The name of the search engine used for the experiment.
        software_version: The version number of the software used for the experiment.
        fdr_psm: The false discovery rate at the peptide-spectrum match level.
        fdr_peptide: The false discovery rate at the peptide level.
        fdr_protein: The false discovery rate at the protein level.
        MBR: A boolean flag indicating whether match-between-runs was enabled or not.
        precursor_tol: The precursor mass tolerance in units specified by precursor_tol_unit.
        precursor_tol_unit: The unit of the precursor mass tolerance. Either "Da" or "ppm".
        fragment_tol: The fragment mass tolerance in units specified by fragment_tol_unit.
        fragment_tol_unit: The unit of the fragment mass tolerance. Either "Da" or "ppm".
        enzyme_name: The name of the enzyme used for digestion.
        missed_cleavages: The number of allowed missed cleavages during digestion.
        min_pep_length: The minimum peptide length for identification.
        max_pep_length: The maximum peptide length for identification.
        weighted_sum: The weighted sum score used for protein inference.
        nr_prec: The number of precursors used for protein inference.
    """

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
    fragment_tol: int = 0
    fragment_tol_unit: str = "Da"
    enzyme_name: str = None
    missed_cleavages: int = 0
    min_pep_length: int = 0
    max_pep_length: int = 0

    def calculate_benchmarking_metric_1(self, intermediate_data):
        """Calculates the first benchmarking metric based on the intermediate data.

        Args:
            intermediate_data (dict): A dictionary containing the intermediate data.

        Returns:
            metric_1 (float): The value of the first benchmarking metric.
        """
        # TODO: calculate metric 1
        metric_1 = 0

        return metric_1

    def calculate_benchmarking_metric_2(self, intermediate_data):
        """Calculates the second benchmarking metric based on the intermediate data.

        Args:
            intermediate_data (dict): A dictionary containing the intermediate data.

        Returns:
            metric_2 (float): The value of the second benchmarking metric.
        """
        # TODO: calculate metric 2
        metric_2 = 0

        return metric_2

    # TODO: add more functions to calculate the benchmarking metrics

    # Leave this functions as it is
    def generate_id(self):
        """Generates a unique id for the datapoint based on the search engine and software version.

        Sets the id attribute to a string composed of the search engine name, software version number,
        and current timestamp separated by underscores. Prints the id to stdout.
        """
        self.id = self.search_engine + "_" + str(self.software_version) + "_" + str(datetime.timestamp(datetime.now()))

    def dump_json_object(self, file_name):
        """Dumps the datapoint as a JSON object to a file.

        Args:
            file_name (str): The name of the file to write to.

        Writes a JSON representation of the datapoint to a file with the given name. Appends the JSON object
        to the end of the file if it already exists.
        """
        f = open(file_name, "a")
        f.write(json.dumps(asdict(self)))
        f.close()
