class ProteoBenchError(Exception):
    """Base class for errors raised by the ProteoBench benchmarking pipeline."""

    def __init__(self, message=""):
        self.message = message
        super().__init__(message)


class DatasetAlreadyExistsOnServerError(Exception):
    """Raised when attempting to submit a dataset that already exists on the public datasets server."""


class ParseError(ProteoBenchError):
    """Raised when an input file cannot be loaded or parsed."""


class ParseSettingsError(ProteoBenchError):
    """Raised when a tool's parse settings cannot be loaded."""


class ConvertStandardFormatError(ProteoBenchError):
    """Raised when converting the input to the standard format fails."""


class QuantificationError(ProteoBenchError):
    """Raised when the quantification scores cannot be set up."""


class IntermediateFormatGenerationError(ProteoBenchError):
    """Raised when generating the intermediate data structure fails."""


class DatapointGenerationError(ProteoBenchError):
    """Raised when generating a datapoint fails."""


class DatapointAppendError(ProteoBenchError):
    """Raised when adding a datapoint to the collection fails."""


class EntrapmentError(ProteoBenchError):
    """Raised when an entrapment-specific step fails."""


class PlotError(ProteoBenchError):
    """Raised when plotting fails."""
