"""Core file selection logic using TLSH."""

import random
import time
from typing import Any

import numpy as np
import tlsh
from tqdm import tqdm

from .exceptions import InsufficientFilesError
from .hash_utils import CacheManager, compute_tlsh_hash
from .parallel import compute_hashes_parallel
from .types import SelectionResult


def select_diverse_files(
    file_paths: list[str],
    n_select: int,
    *,
    cache_dir: str | None = None,
    verbose: bool = False,
    n_jobs: int = 1,
    random_state: int | None = None,
) -> SelectionResult:
    """
    Select the most diverse files from a dataset using TLSH.

    Uses a greedy algorithm that iteratively selects files with maximum
    minimum distance from already selected files. Time complexity: O(m*n)
    where n is the number of files and m is the number to select.

    Args:
        file_paths: List of file paths to select from
        n_select: Number of files to select
        cache_dir: Directory for caching TLSH hashes. None = no caching
        verbose: Whether to show progress bars and detailed information
        n_jobs: Number of parallel workers for hash computation. 1 = sequential, -1 = all cores
        random_state: Random seed for reproducibility (affects first file selection)

    Returns:
        SelectionResult: Selection result with indices, file paths, and optional hash information

    Raises:
        InsufficientFilesError: If there are fewer valid files than n_select
        ValueError: If n_select is invalid

    Examples:
        >>> # Simple usage
        >>> result = select_diverse_files(['file1', 'file2', 'file3'], n_select=2)
        >>> print(list(result))  # [0, 2]
        >>>
        >>> # With caching and parallelization
        >>> result = select_diverse_files(
        ...     file_paths=paths,
        ...     n_select=100,
        ...     cache_dir='/tmp/tlsh_cache',
        ...     verbose=True,
        ...     n_jobs=-1
        ... )
    """
    if n_select <= 0:
        raise ValueError(f"n_select must be positive, got {n_select}")

    if n_select > len(file_paths):
        raise ValueError(
            f"n_select ({n_select}) cannot be greater than number of files ({len(file_paths)})"
        )

    # Set random seed
    if random_state is not None:
        random.seed(random_state)
        np.random.seed(random_state)

    start_time = time.time()

    # Create selector instance
    selector = FileSelector(
        cache_dir=cache_dir,
        n_jobs=n_jobs,
        verbose=verbose,
    )

    # Perform selection
    result = selector.select(
        file_paths=file_paths,
        n_select=n_select,
        verbose=verbose,
        random_state=random_state,
    )

    return result


class FileSelector:
    """
    File selector with state management for TLSH-based selection.

    This class maintains cache state and configuration across multiple
    selection operations.
    """

    def __init__(
        self,
        *,
        cache_dir: str | None = None,
        n_jobs: int = 1,
        verbose: bool = False,
    ):
        """
        Initialize file selector.

        Args:
            cache_dir: Directory for caching TLSH hashes. None = no caching
            n_jobs: Number of parallel workers. 1 = sequential, -1 = all cores
            verbose: Default verbosity for operations
        """
        self._cache_dir = cache_dir
        self._cache_manager = CacheManager(cache_dir) if cache_dir else None
        self._n_jobs = n_jobs
        self._verbose = verbose
        self._hash_dict: dict[str, str] = {}

    def select(
        self,
        file_paths: list[str],
        n_select: int,
        *,
        verbose: bool | None = None,
        random_state: int | None = None,
    ) -> SelectionResult:
        """
        Select the most diverse files.

        Args:
            file_paths: List of file paths to select from
            n_select: Number of files to select
            verbose: Whether to show progress. None = use instance default
            random_state: Random seed for reproducibility

        Returns:
            SelectionResult: Selection result

        Raises:
            InsufficientFilesError: If there are fewer valid files than n_select
        """
        if verbose is None:
            verbose = self._verbose

        if random_state is not None:
            random.seed(random_state)
            np.random.seed(random_state)

        start_time = time.time()

        # Compute or load hashes
        self._hash_dict = self._compute_or_load_hashes(file_paths, verbose)

        # Get valid file names (files with valid hashes)
        valid_paths = list(self._hash_dict.keys())

        if len(valid_paths) < n_select:
            raise InsufficientFilesError(
                f"Only {len(valid_paths)} valid files found, but {n_select} requested. "
                f"Check if files exist and are valid for TLSH hashing (>= 50 bytes)."
            )

        # Perform greedy selection
        selected_indices, diversity_scores = self._greedy_selection(
            valid_paths, n_select, verbose
        )

        # Map back to original indices
        original_indices = [file_paths.index(valid_paths[idx]) for idx in selected_indices]
        selected_paths = [file_paths[i] for i in original_indices]

        elapsed_time = time.time() - start_time

        # Save cache if enabled
        if self._cache_manager:
            self._cache_manager.save()

        return SelectionResult(
            indices=tuple(original_indices),
            file_paths=tuple(selected_paths),
            hashes=self._hash_dict.copy() if self._cache_dir else None,
            diversity_scores=tuple(diversity_scores) if diversity_scores else None,
            elapsed_time=elapsed_time,
        )

    def _compute_or_load_hashes(
        self, file_paths: list[str], verbose: bool
    ) -> dict[str, str]:
        """
        Compute or load TLSH hashes from cache.

        Args:
            file_paths: List of file paths
            verbose: Whether to show progress

        Returns:
            Dictionary mapping file paths to TLSH hashes
        """
        hash_dict = {}
        files_to_compute = []

        # Check cache first
        if self._cache_manager:
            for file_path in file_paths:
                cached_hash = self._cache_manager.get(file_path)
                if cached_hash:
                    hash_dict[file_path] = cached_hash
                else:
                    files_to_compute.append(file_path)

            if verbose and hash_dict:
                print(f"Loaded {len(hash_dict)} hashes from cache")
        else:
            files_to_compute = file_paths

        # Compute missing hashes
        if files_to_compute:
            computed_hashes = compute_hashes_parallel(
                files_to_compute, n_jobs=self._n_jobs, verbose=verbose
            )
            hash_dict.update(computed_hashes)

            # Update cache
            if self._cache_manager:
                for file_path, hash_value in computed_hashes.items():
                    self._cache_manager.set(file_path, hash_value)

        return hash_dict

    def _greedy_selection(
        self, file_paths: list[str], n_select: int, verbose: bool
    ) -> tuple[list[int], list[float]]:
        """
        Perform greedy selection to find most diverse files.

        Algorithm:
        1. Randomly select first file
        2. Iteratively select the file with maximum minimum distance from selected files
        3. Track minimum distances using numpy array for efficiency

        Args:
            file_paths: List of valid file paths (with computed hashes)
            n_select: Number of files to select
            verbose: Whether to show progress

        Returns:
            Tuple of (selected_indices, diversity_scores)
        """
        n = len(file_paths)
        selected_indices = []
        diversity_scores = []

        # Initialize minimum distances array (inf means not yet compared)
        # -1 means already selected
        min_distances = np.full(n, np.inf, dtype=np.float32)

        # Randomly select first file
        first_idx = random.randint(0, n - 1)
        selected_indices.append(first_idx)
        min_distances[first_idx] = -1
        diversity_scores.append(np.inf)  # First file has infinite diversity by definition

        # Progress bar for selection process
        iterator = range(n_select - 1)
        if verbose:
            iterator = tqdm(iterator, desc="Selecting diverse files", initial=1, total=n_select)

        for _ in iterator:
            current_path = file_paths[selected_indices[-1]]
            current_hash = self._hash_dict[current_path]

            max_min_distance = -np.inf
            next_idx = -1

            # Update minimum distances and find next file to select
            for idx in range(n):
                if min_distances[idx] == -1:  # Already selected
                    continue

                # Compute distance to current file
                candidate_hash = self._hash_dict[file_paths[idx]]
                distance = tlsh.diff(current_hash, candidate_hash)

                # Update minimum distance for this candidate
                if min_distances[idx] == np.inf:
                    min_distances[idx] = distance
                else:
                    min_distances[idx] = min(min_distances[idx], distance)

                # Track file with maximum minimum distance
                if min_distances[idx] > max_min_distance:
                    max_min_distance = min_distances[idx]
                    next_idx = idx

            # Select the file with maximum minimum distance
            if next_idx != -1:
                selected_indices.append(next_idx)
                diversity_scores.append(float(max_min_distance))
                min_distances[next_idx] = -1

        return selected_indices, diversity_scores

    def compute_hashes(
        self,
        file_paths: list[str],
        *,
        verbose: bool | None = None,
    ) -> dict[str, str]:
        """
        Compute TLSH hashes without performing selection.

        Useful for pre-computing hashes for later use.

        Args:
            file_paths: List of file paths
            verbose: Whether to show progress. None = use instance default

        Returns:
            Dictionary mapping file paths to TLSH hashes
        """
        if verbose is None:
            verbose = self._verbose

        hash_dict = self._compute_or_load_hashes(file_paths, verbose)

        if self._cache_manager:
            self._cache_manager.save()

        return hash_dict

    def get_cached_hashes(self) -> dict[str, str]:
        """
        Get all cached hashes.

        Returns:
            Dictionary mapping file paths to TLSH hashes

        Raises:
            ValueError: If no cache directory is configured
        """
        if not self._cache_manager:
            raise ValueError("No cache directory configured")
        return self._cache_manager.get_all_hashes()

    def clear_cache(self) -> None:
        """
        Clear all cached hashes.

        Raises:
            ValueError: If no cache directory is configured
        """
        if not self._cache_manager:
            raise ValueError("No cache directory configured")
        self._cache_manager.clear()
