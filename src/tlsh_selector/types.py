"""Type definitions for tlsh-selector."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SelectionResult:
    """
    Immutable result of file selection.

    This class can be used directly as a list-like object for indices,
    while also providing access to additional information.

    Attributes:
        indices: Tuple of selected file indices
        file_paths: Tuple of selected file paths
        hashes: Dictionary mapping file paths to TLSH hashes (None if no cache used)
        diversity_scores: Tuple of diversity scores for each selected file (None if not computed)
        elapsed_time: Time taken for the selection process in seconds (None if not tracked)

    Examples:
        >>> result = select_diverse_files(paths, n_select=10)
        >>> print(result[0])  # Access first index
        >>> for idx in result:  # Iterate over indices
        ...     print(paths[idx])
        >>> indices = list(result)  # Convert to list
        >>> if result.hashes:  # Check if hashes are available
        ...     print(result.hashes[paths[0]])
    """

    indices: tuple[int, ...]
    file_paths: tuple[str, ...]
    hashes: dict[str, str] | None = None
    diversity_scores: tuple[float, ...] | None = None
    elapsed_time: float | None = None

    def __iter__(self):
        """Support iteration over indices: for idx in result."""
        return iter(self.indices)

    def __getitem__(self, key: int | slice) -> int | tuple[int, ...]:
        """Support indexing: result[0] or result[1:3]."""
        return self.indices[key]

    def __len__(self) -> int:
        """Support len(result)."""
        return len(self.indices)

    def __repr__(self) -> str:
        """String representation."""
        return f"SelectionResult(n_selected={len(self.indices)})"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result to a dictionary.

        Returns:
            Dictionary containing all available fields
        """
        result = {
            "indices": list(self.indices),
            "file_paths": list(self.file_paths),
        }
        if self.hashes is not None:
            result["hashes"] = self.hashes
        if self.diversity_scores is not None:
            result["diversity_scores"] = list(self.diversity_scores)
        if self.elapsed_time is not None:
            result["elapsed_time"] = self.elapsed_time
        return result
