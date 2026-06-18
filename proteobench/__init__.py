"""ProteoBench."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("proteobench")
except PackageNotFoundError:
    # Package metadata is unavailable (e.g. running from a source tree without
    # an install). Fall back so importing proteobench never fails.
    __version__ = "0.0.0+unknown"
