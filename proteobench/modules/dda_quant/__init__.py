from abc import ABC, abstractmethod


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
        """Method used to add the current data point to the collected benchmarks."""
        pass


class ParseInputsInterface(ABC):
    @abstractmethod
    def convert_to_standard_format(self):
        """Convert a search engine output into a generic format supported by the module."""
        pass
