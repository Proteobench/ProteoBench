class ProteobenchError(Exception):
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
