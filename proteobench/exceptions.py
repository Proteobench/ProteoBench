class ProteobenchError(Exception):
    """Base class for errors raised by the ProteoBench benchmarking pipeline."""

    def __init__(self, message=""):
        self.message = message
        super().__init__(message)


class DatasetAlreadyExistsOnServerError(Exception):
    """Raised when attempting to submit a dataset that already exists on the public datasets server."""


class ParseError(ProteobenchError):
    """Raised when an input file cannot be loaded or parsed."""


class ParseSettingsError(ProteobenchError):
    """Raised when a tool's parse settings cannot be loaded."""


class ConvertStandardFormatError(ProteobenchError):
    """Raised when converting the input to the standard format fails."""


class QuantificationError(ProteobenchError):
    """Raised when the quantification scores cannot be set up."""


class IntermediateFormatGenerationError(ProteobenchError):
    """Raised when generating the intermediate data structure fails."""


class DatapointGenerationError(ProteobenchError):
    """Raised when generating a datapoint fails."""


class DatapointAppendError(ProteobenchError):
    """Raised when adding a datapoint to the collection fails."""


class EntrapmentError(ProteobenchError):
    """Raised when an entrapment-specific step fails."""


class PlotError(ProteobenchError):
    """Raised when plotting fails."""
