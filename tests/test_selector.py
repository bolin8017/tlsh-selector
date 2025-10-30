"""Tests for selector module."""

import tempfile
from pathlib import Path

import pytest

from tlsh_selector import (
    FileSelector,
    InsufficientFilesError,
    SelectionResult,
    select_diverse_files,
)


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    files = []
    for i in range(10):
        file_path = tmp_path / f"file_{i}.bin"
        # Create files with different content
        content = bytes([i % 256] * 100 + [j for j in range(100)])
        file_path.write_bytes(content)
        files.append(str(file_path))
    return files


def test_basic_selection(sample_files):
    """Test basic file selection."""
    result = select_diverse_files(sample_files, n_select=3)

    assert isinstance(result, SelectionResult)
    assert len(result) == 3
    assert len(result.indices) == 3
    assert len(result.file_paths) == 3
    assert all(0 <= idx < len(sample_files) for idx in result.indices)


def test_selection_with_cache(sample_files, tmp_path):
    """Test selection with caching."""
    cache_dir = str(tmp_path / "cache")

    result1 = select_diverse_files(
        sample_files, n_select=3, cache_dir=cache_dir, random_state=42
    )
    result2 = select_diverse_files(
        sample_files, n_select=3, cache_dir=cache_dir, random_state=42
    )

    # Same random state should give same results
    assert list(result1.indices) == list(result2.indices)
    assert result1.hashes is not None
    assert result2.hashes is not None


def test_result_as_list(sample_files):
    """Test SelectionResult list-like behavior."""
    result = select_diverse_files(sample_files, n_select=5)

    # Test iteration
    indices_list = [idx for idx in result]
    assert len(indices_list) == 5

    # Test indexing
    assert result[0] == result.indices[0]
    assert result[-1] == result.indices[-1]

    # Test slicing
    assert result[1:3] == result.indices[1:3]

    # Test len
    assert len(result) == 5

    # Test conversion
    assert list(result) == list(result.indices)


def test_insufficient_files(sample_files):
    """Test error when requesting more files than available."""
    with pytest.raises(InsufficientFilesError):
        select_diverse_files(sample_files, n_select=20)


def test_invalid_n_select(sample_files):
    """Test error with invalid n_select."""
    with pytest.raises(ValueError):
        select_diverse_files(sample_files, n_select=0)

    with pytest.raises(ValueError):
        select_diverse_files(sample_files, n_select=-1)


def test_reproducibility(sample_files):
    """Test reproducibility with random_state."""
    result1 = select_diverse_files(sample_files, n_select=3, random_state=42)
    result2 = select_diverse_files(sample_files, n_select=3, random_state=42)
    result3 = select_diverse_files(sample_files, n_select=3, random_state=123)

    assert list(result1.indices) == list(result2.indices)
    assert list(result1.indices) != list(result3.indices)


def test_file_selector_class(sample_files, tmp_path):
    """Test FileSelector class."""
    cache_dir = str(tmp_path / "cache")
    selector = FileSelector(cache_dir=cache_dir, verbose=False)

    # First selection
    result1 = selector.select(sample_files, n_select=3)
    assert len(result1) == 3

    # Second selection with different n_select
    result2 = selector.select(sample_files, n_select=5)
    assert len(result2) == 5

    # Check cache
    cached = selector.get_cached_hashes()
    assert len(cached) == len(sample_files)


def test_compute_hashes(sample_files, tmp_path):
    """Test hash computation."""
    cache_dir = str(tmp_path / "cache")
    selector = FileSelector(cache_dir=cache_dir, verbose=False)

    hashes = selector.compute_hashes(sample_files)
    assert len(hashes) == len(sample_files)
    assert all(isinstance(h, str) for h in hashes.values())


def test_clear_cache(sample_files, tmp_path):
    """Test cache clearing."""
    cache_dir = str(tmp_path / "cache")
    selector = FileSelector(cache_dir=cache_dir, verbose=False)

    selector.compute_hashes(sample_files)
    assert len(selector.get_cached_hashes()) > 0

    selector.clear_cache()
    assert len(selector.get_cached_hashes()) == 0


def test_small_files_handling(tmp_path):
    """Test handling of files too small for TLSH."""
    # Create files too small for TLSH (< 50 bytes)
    small_files = []
    for i in range(5):
        file_path = tmp_path / f"small_{i}.bin"
        file_path.write_bytes(b"x" * 10)
        small_files.append(str(file_path))

    with pytest.raises(InsufficientFilesError):
        select_diverse_files(small_files, n_select=2)


def test_diversity_scores(sample_files):
    """Test diversity scores are computed."""
    result = select_diverse_files(sample_files, n_select=5)

    assert result.diversity_scores is not None
    assert len(result.diversity_scores) == 5
    # First file should have infinite diversity
    assert result.diversity_scores[0] == float("inf")


def test_elapsed_time(sample_files):
    """Test elapsed time is tracked."""
    result = select_diverse_files(sample_files, n_select=3)

    assert result.elapsed_time is not None
    assert result.elapsed_time > 0


def test_to_dict(sample_files):
    """Test conversion to dictionary."""
    result = select_diverse_files(sample_files, n_select=3, random_state=42)

    result_dict = result.to_dict()
    assert "indices" in result_dict
    assert "file_paths" in result_dict
    assert len(result_dict["indices"]) == 3
