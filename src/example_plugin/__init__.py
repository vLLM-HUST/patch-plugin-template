"""Template for a default-off, single-mechanism runtime-patch plugin for vLLM-HUST."""

from ._version import __version__
from .plugin import register

__all__ = ["__version__", "register"]
