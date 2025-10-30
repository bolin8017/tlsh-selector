"""Advanced usage examples for tlsh-selector."""

import tempfile
from pathlib import Path

from tlsh_selector import FileSelector


def create_sample_files(num_files: int = 20) -> list[str]:
    """Create sample binary files."""
    temp_dir = Path(tempfile.mkdtemp())
    file_paths = []

    for i in range(num_files):
        file_path = temp_dir / f"file_{i}.bin"
        content = bytes([i % 256] * 100 + [j for j in range(100)])
        file_path.write_bytes(content)
        file_paths.append(str(file_path))

    return file_paths


def example_file_selector_class():
    """Using FileSelector class for multiple operations."""
    print("=" * 60)
    print("Example 1: FileSelector Class")
    print("=" * 60)

    # Create selector with configuration
    selector = FileSelector(
        cache_dir="/tmp/tlsh_selector_advanced",
        n_jobs=-1,
        verbose=True,
    )

    file_paths = create_sample_files(30)

    # First selection
    print("\nFirst selection (10 files):")
    result1 = selector.select(file_paths, n_select=10)
    print(f"Selected: {list(result1)}")

    # Second selection with different n_select (reuses cache)
    print("\nSecond selection (5 files):")
    result2 = selector.select(file_paths, n_select=5)
    print(f"Selected: {list(result2)}")

    # Get cached hashes
    cached = selector.get_cached_hashes()
    print(f"\nCached hashes: {len(cached)} files")


def example_precompute_hashes():
    """Pre-computing hashes for later use."""
    print("\n" + "=" * 60)
    print("Example 2: Pre-computing Hashes")
    print("=" * 60)

    selector = FileSelector(
        cache_dir="/tmp/tlsh_selector_precompute",
        n_jobs=-1,
        verbose=True,
    )

    file_paths = create_sample_files(50)

    # Pre-compute hashes
    print("Pre-computing hashes for all files:")
    hashes = selector.compute_hashes(file_paths)
    print(f"Computed {len(hashes)} hashes")

    # Now selection is fast (no hash computation needed)
    print("\nPerforming selection (using cached hashes):")
    result = selector.select(file_paths, n_select=10, verbose=False)
    print(f"Selected: {list(result)}")
    print(f"Elapsed time: {result.elapsed_time:.3f}s")


def example_reproducible_selection():
    """Reproducible selection with random_state."""
    print("\n" + "=" * 60)
    print("Example 3: Reproducible Selection")
    print("=" * 60)

    file_paths = create_sample_files(20)

    # Same random_state gives same results
    selector = FileSelector(verbose=False)

    result1 = selector.select(file_paths, n_select=5, random_state=42)
    result2 = selector.select(file_paths, n_select=5, random_state=42)
    result3 = selector.select(file_paths, n_select=5, random_state=123)

    print(f"Run 1 (seed=42): {list(result1)}")
    print(f"Run 2 (seed=42): {list(result2)}")
    print(f"Run 3 (seed=123): {list(result3)}")
    print(f"\nResults 1 and 2 are identical: {list(result1) == list(result2)}")
    print(f"Results 1 and 3 are different: {list(result1) != list(result3)}")


def example_diversity_scores():
    """Analyzing diversity scores."""
    print("\n" + "=" * 60)
    print("Example 4: Diversity Scores")
    print("=" * 60)

    file_paths = create_sample_files(20)

    selector = FileSelector(verbose=False)
    result = selector.select(file_paths, n_select=5)

    print("Selected files with diversity scores:")
    for idx, score in zip(result.indices, result.diversity_scores):
        print(f"  File {idx}: diversity score = {score}")

    print(f"\nFirst file has infinite diversity (randomly chosen)")
    print(f"Subsequent files selected to maximize minimum distance")


def example_cache_management():
    """Managing cache."""
    print("\n" + "=" * 60)
    print("Example 5: Cache Management")
    print("=" * 60)

    cache_dir = "/tmp/tlsh_selector_cache_mgmt"
    file_paths = create_sample_files(20)

    # Create selector and compute hashes
    selector = FileSelector(cache_dir=cache_dir, verbose=False)
    selector.compute_hashes(file_paths)

    # Check cached hashes
    cached = selector.get_cached_hashes()
    print(f"Cached hashes: {len(cached)}")

    # Clear cache
    print("\nClearing cache...")
    selector.clear_cache()

    cached_after = selector.get_cached_hashes()
    print(f"Cached hashes after clear: {len(cached_after)}")


def example_error_handling():
    """Handling errors gracefully."""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    from tlsh_selector import InsufficientFilesError

    file_paths = create_sample_files(5)
    selector = FileSelector(verbose=False)

    # Try to select more files than available
    try:
        result = selector.select(file_paths, n_select=10)
    except InsufficientFilesError as e:
        print(f"Caught expected error: {e}")

    # Create files that are too small for TLSH
    temp_dir = Path(tempfile.mkdtemp())
    small_files = []
    for i in range(3):
        file_path = temp_dir / f"small_{i}.bin"
        file_path.write_bytes(b"x" * 10)  # Too small for TLSH
        small_files.append(str(file_path))

    print("\nTrying to select from files too small for TLSH:")
    try:
        result = selector.select(small_files, n_select=2)
    except InsufficientFilesError as e:
        print(f"Caught expected error: {e}")


if __name__ == "__main__":
    example_file_selector_class()
    example_precompute_hashes()
    example_reproducible_selection()
    example_diversity_scores()
    example_cache_management()
    example_error_handling()

    print("\n" + "=" * 60)
    print("All advanced examples completed!")
    print("=" * 60)
