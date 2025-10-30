"""Basic usage examples for tlsh-selector."""

import tempfile
from pathlib import Path

from tlsh_selector import select_diverse_files


def create_sample_files(num_files: int = 20) -> list[str]:
    """
    Create sample files for demonstration.

    Args:
        num_files: Number of files to create

    Returns:
        List of file paths
    """
    temp_dir = Path(tempfile.mkdtemp())
    file_paths = []

    for i in range(num_files):
        file_path = temp_dir / f"file_{i}.bin"
        # Create files with different content patterns
        # Files with similar indices will have similar content
        content = bytes([i % 256] * 100 + [j for j in range(100)])
        file_path.write_bytes(content)
        file_paths.append(str(file_path))

    return file_paths


def example_basic():
    """Basic selection without caching."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Create sample files
    file_paths = create_sample_files(20)
    print(f"Created {len(file_paths)} sample files")

    # Select 5 most diverse files
    result = select_diverse_files(file_paths, n_select=5)

    print(f"\nSelected indices: {list(result)}")
    print(f"Selected files:")
    for idx in result:
        print(f"  - {file_paths[idx]}")


def example_with_cache():
    """Selection with caching enabled."""
    print("\n" + "=" * 60)
    print("Example 2: With Caching")
    print("=" * 60)

    # Create sample files
    file_paths = create_sample_files(20)

    # First run - computes hashes
    print("\nFirst run (computing hashes):")
    result1 = select_diverse_files(
        file_paths,
        n_select=5,
        cache_dir="/tmp/tlsh_selector_example",
        verbose=True,
    )
    print(f"Selected: {list(result1)}")
    print(f"Elapsed time: {result1.elapsed_time:.3f}s")

    # Second run - uses cached hashes
    print("\nSecond run (using cache):")
    result2 = select_diverse_files(
        file_paths,
        n_select=5,
        cache_dir="/tmp/tlsh_selector_example",
        verbose=True,
        random_state=42,  # Same seed should give same results
    )
    print(f"Selected: {list(result2)}")
    print(f"Elapsed time: {result2.elapsed_time:.3f}s")

    # Access cached hashes
    if result2.hashes:
        print(f"\nTotal files hashed: {len(result2.hashes)}")
        print(f"First file hash: {list(result2.hashes.values())[0]}")


def example_parallel():
    """Selection with parallel hash computation."""
    print("\n" + "=" * 60)
    print("Example 3: Parallel Computation")
    print("=" * 60)

    # Create more files to see parallel benefit
    file_paths = create_sample_files(100)
    print(f"Created {len(file_paths)} sample files")

    # Sequential computation
    print("\nSequential computation:")
    result1 = select_diverse_files(
        file_paths, n_select=10, n_jobs=1, verbose=True
    )
    print(f"Elapsed time: {result1.elapsed_time:.3f}s")

    # Parallel computation
    print("\nParallel computation (all cores):")
    result2 = select_diverse_files(
        file_paths, n_select=10, n_jobs=-1, verbose=True
    )
    print(f"Elapsed time: {result2.elapsed_time:.3f}s")


def example_result_object():
    """Demonstrate SelectionResult usage."""
    print("\n" + "=" * 60)
    print("Example 4: Working with SelectionResult")
    print("=" * 60)

    file_paths = create_sample_files(20)

    result = select_diverse_files(
        file_paths,
        n_select=5,
        cache_dir="/tmp/tlsh_selector_example",
    )

    # Use as a list
    print(f"Length: {len(result)}")
    print(f"First index: {result[0]}")
    print(f"Slice: {result[1:3]}")

    # Iterate
    print("\nIterating over indices:")
    for idx in result:
        print(f"  Index {idx}: {file_paths[idx]}")

    # Convert to list
    indices_list = list(result)
    print(f"\nAs list: {indices_list}")

    # Access additional information
    print(f"\nFile paths: {result.file_paths[:2]}...")
    if result.diversity_scores:
        print(f"Diversity scores: {result.diversity_scores}")
    print(f"Elapsed time: {result.elapsed_time:.3f}s")

    # Convert to dict
    result_dict = result.to_dict()
    print(f"\nAs dict keys: {result_dict.keys()}")


if __name__ == "__main__":
    example_basic()
    example_with_cache()
    example_parallel()
    example_result_object()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
