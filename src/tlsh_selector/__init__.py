"""
tlsh-selector: Select diverse files from a dataset using TLSH.

This package provides tools to select the most diverse subset of files
from a dataset using Trend Micro Locality Sensitive Hash (TLSH) for
similarity detection.
"""

from .exceptions import (
    CacheError,
    FileNotFoundError,
    InsufficientFilesError,
    InvalidHashError,
    TLSHSelectorError,
)
from .selector import FileSelector, select_diverse_files
from .types import SelectionResult

__version__ = "0.1.0"

__all__ = [
    # Main API
    "select_diverse_files",
    "FileSelector",
    "SelectionResult",
    # Exceptions
    "TLSHSelectorError",
    "FileNotFoundError",
    "InvalidHashError",
    "InsufficientFilesError",
    "CacheError",
]
