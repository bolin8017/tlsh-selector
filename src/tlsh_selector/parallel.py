"""Parallel computation utilities for TLSH operations."""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Callable

from tqdm import tqdm

from .hash_utils import compute_tlsh_hash


def _compute_hash_worker(file_path: str) -> tuple[str, str | None]:
    """
    Worker function to compute TLSH hash for a single file.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (file_path, hash_value or None if failed)
    """
    try:
        hash_value = compute_tlsh_hash(file_path)
        return (file_path, hash_value)
    except Exception:
        return (file_path, None)


def compute_hashes_parallel(
    file_paths: list[str],
    n_jobs: int = 1,
    verbose: bool = False,
) -> dict[str, str]:
    """
    Compute TLSH hashes for multiple files in parallel.

    Args:
        file_paths: List of file paths
        n_jobs: Number of parallel workers. 1 = sequential, -1 = use all CPU cores
        verbose: Whether to show progress bar

    Returns:
        Dictionary mapping file paths to TLSH hashes (excludes failed files)
    """
    if n_jobs == -1:
        n_jobs = mp.cpu_count()

    # Sequential processing
    if n_jobs == 1:
        results = {}
        iterator = tqdm(file_paths, desc="Computing TLSH hashes") if verbose else file_paths
        for file_path in iterator:
            try:
                hash_value = compute_tlsh_hash(file_path)
                results[file_path] = hash_value
            except Exception:
                pass  # Skip files that fail
        return results

    # Parallel processing
    results = {}
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        futures = {executor.submit(_compute_hash_worker, fp): fp for fp in file_paths}

        iterator = as_completed(futures)
        if verbose:
            iterator = tqdm(iterator, total=len(file_paths), desc="Computing TLSH hashes")

        for future in iterator:
            file_path, hash_value = future.result()
            if hash_value is not None:
                results[file_path] = hash_value

    return results


def _compute_distances_worker(
    args: tuple[str, list[str], dict[str, str]]
) -> tuple[int, list[float]]:
    """
    Worker function to compute TLSH distances from one file to multiple files.

    Args:
        args: Tuple of (current_hash, candidate_file_paths, hash_dict)

    Returns:
        Tuple of (original_index, list of distances)
    """
    import tlsh

    current_hash, candidate_paths, hash_dict = args
    distances = []
    for candidate_path in candidate_paths:
        candidate_hash = hash_dict[candidate_path]
        distance = tlsh.diff(current_hash, candidate_hash)
        distances.append(distance)
    return distances


def compute_distances_parallel(
    current_hash: str,
    candidate_paths: list[str],
    hash_dict: dict[str, str],
    n_jobs: int = 1,
) -> list[float]:
    """
    Compute TLSH distances from current hash to multiple candidate hashes in parallel.

    Note: For typical use cases, this is often not worth parallelizing due to overhead.
    Only beneficial when computing distances for thousands of candidates.

    Args:
        current_hash: TLSH hash of the current file
        candidate_paths: List of candidate file paths
        hash_dict: Dictionary mapping file paths to TLSH hashes
        n_jobs: Number of parallel workers

    Returns:
        List of distances in the same order as candidate_paths
    """
    import tlsh

    # For small numbers, sequential is faster
    if len(candidate_paths) < 1000 or n_jobs == 1:
        return [tlsh.diff(current_hash, hash_dict[path]) for path in candidate_paths]

    # For large numbers, consider parallelization
    if n_jobs == -1:
        n_jobs = mp.cpu_count()

    # Split work into chunks
    chunk_size = max(1, len(candidate_paths) // n_jobs)
    chunks = [
        candidate_paths[i : i + chunk_size]
        for i in range(0, len(candidate_paths), chunk_size)
    ]

    results = []
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        futures = [
            executor.submit(_compute_distances_worker, (current_hash, chunk, hash_dict))
            for chunk in chunks
        ]
        for future in as_completed(futures):
            results.extend(future.result())

    return results
