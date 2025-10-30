"""Custom exceptions for tlsh-selector."""


class TLSHSelectorError(Exception):
    """Base exception for all tlsh-selector errors."""

    pass


class FileNotFoundError(TLSHSelectorError):
    """Raised when a file is not found."""

    pass


class InvalidHashError(TLSHSelectorError):
    """Raised when a TLSH hash is invalid or cannot be computed."""

    pass


class InsufficientFilesError(TLSHSelectorError):
    """Raised when there are not enough valid files to select from."""

    pass


class CacheError(TLSHSelectorError):
    """Raised when there is an error with cache operations."""

    pass
