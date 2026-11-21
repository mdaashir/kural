"""Kural — local-first voice typing and voice control for Windows."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cmd-kural")
except PackageNotFoundError:
    # Allow importing source files without an installed project environment.
    __version__ = "0+unknown"
