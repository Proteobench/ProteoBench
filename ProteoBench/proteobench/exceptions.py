class ProteobenchError(Exception):
    pass


class DatasetAlreadyExistsOnServerError(Exception):
    """Raised when attempting to submit a dataset that already exists on the public datasets server."""

    pass


class ProteoBenchError(Exception):
    """Base exception class for ProteoBench."""

    pass


class ParseError(ProteoBenchError):
    """Raised when there's an error parsing input files."""

    pass


class ValidationError(ProteoBenchError):
    """Raised when data validation fails."""

    pass


class ParseError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ParseSettingsError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DatapointAppendError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DatapointGenerationError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class IntermediateFormatGenerationError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class QuantificationError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class PlotError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ConvertStandardFormatError(ProteobenchError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
