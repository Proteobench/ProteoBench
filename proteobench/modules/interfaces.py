"""Types defined by ABCs"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ModuleInterface(ABC):
    @abstractmethod
    def benchmarking(self):
        """Method used to run the benchmarking."""
        pass

    @abstractmethod
    def load_input_file(self):
        """Method loads dataframe from the file depending on its format."""
        pass

    @abstractmethod
    def generate_intermediate(self):
        """Calculate intermediate values from the uploaded file."""
        pass

    @abstractmethod
    def generate_datapoint(self):
        """Method used to compute benchmarks for the provided intermediate structure."""
        pass

    @abstractmethod
    def add_current_data_point(self):
        pass


class ParseInputsInterface(ABC):
    @abstractmethod
    def convert_to_standard_format(self):
        """Convert a search engine output into a generic format supported by the module."""
        pass


class PlotDataPoint(ABC):
    @abstractmethod
    def plot_bench(self, result_df):
        """Plot benchmarking results."""

    @abstractmethod
    def plot_metric(self, benchmark_metrics_df):
        """Plot benchmarking metrics."""


@dataclass
class Settings:
    mapper: str
    condition_mapper: str
    decoy_flag: str
    species_dict: str
    contaminant_flag: str
    min_count_multispec: str
    species_expected_ratio: str
