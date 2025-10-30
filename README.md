# tlsh-selector

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Select the most diverse files from a dataset using TLSH (Trend Micro Locality Sensitive Hash).

## Overview

`tlsh-selector` helps you select a diverse subset of files from a large dataset. It uses [TLSH](https://github.com/trendmicro/tlsh) to measure file similarity and employs a greedy algorithm to select files that are maximally different from each other.

**Key Features:**
- 🚀 Fast selection using greedy algorithm (O(m×n) complexity)
- 💾 Smart caching system with automatic invalidation
- ⚡ Parallel hash computation for large datasets
- 🎯 Reproducible results with random seed control
- 📦 Simple, intuitive API
- 🔧 Both functional and object-oriented interfaces

**Use Cases:**
- Selecting diverse malware samples for analysis
- Creating representative subsets of large datasets
- Reducing dataset redundancy while maintaining diversity
- Building balanced training/testing datasets

## Installation

### From Source

```bash
git clone https://github.com/bolin8017/tlsh-selector.git
cd tlsh-selector
pip install -e .
```

### Requirements

- Python >= 3.10
- numpy >= 1.20.0
- py-tlsh >= 4.0.0
- tqdm >= 4.60.0

## Quick Start

```python
from tlsh_selector import select_diverse_files

# Simple usage - select 10 most diverse files
file_paths = ['file1.bin', 'file2.bin', 'file3.bin', ...]
result = select_diverse_files(file_paths, n_select=10)

# Access selected indices
print(list(result))  # [3, 15, 42, ...]

# Access selected file paths
for idx in result:
    print(f"Selected: {file_paths[idx]}")
```

## Usage Examples

### Basic Selection

```python
from tlsh_selector import select_diverse_files

result = select_diverse_files(
    file_paths=['file1', 'file2', 'file3', ...],
    n_select=10,
    verbose=True  # Show progress bar
)

# Result is list-like
print(f"Selected {len(result)} files")
print(f"First index: {result[0]}")
print(f"All indices: {list(result)}")
```

### With Caching (Recommended for Multiple Runs)

```python
from tlsh_selector import select_diverse_files

# First run - computes and caches hashes
result = select_diverse_files(
    file_paths=file_paths,
    n_select=100,
    cache_dir='/tmp/tlsh_cache',  # Enable caching
    verbose=True
)

# Second run - reuses cached hashes (much faster!)
result = select_diverse_files(
    file_paths=file_paths,
    n_select=50,
    cache_dir='/tmp/tlsh_cache',
    verbose=True
)

# Access cached hashes
if result.hashes:
    print(f"Cached {len(result.hashes)} hashes")
```

### Parallel Processing

```python
from tlsh_selector import select_diverse_files

# Use all CPU cores for hash computation
result = select_diverse_files(
    file_paths=file_paths,
    n_select=100,
    n_jobs=-1,  # -1 = use all cores
    verbose=True
)

print(f"Completed in {result.elapsed_time:.2f} seconds")
```

### Reproducible Selection

```python
from tlsh_selector import select_diverse_files

# Same random_state gives same results
result1 = select_diverse_files(file_paths, n_select=10, random_state=42)
result2 = select_diverse_files(file_paths, n_select=10, random_state=42)

assert list(result1) == list(result2)  # Identical results
```

### Advanced Usage with FileSelector Class

```python
from tlsh_selector import FileSelector

# Create selector with persistent configuration
selector = FileSelector(
    cache_dir='/tmp/tlsh_cache',
    n_jobs=-1,
    verbose=True
)

# Pre-compute hashes for all files
hashes = selector.compute_hashes(file_paths)
print(f"Computed {len(hashes)} hashes")

# Perform multiple selections (reusing cached hashes)
result1 = selector.select(file_paths, n_select=10)
result2 = selector.select(file_paths, n_select=20)

# Access cached hashes
all_cached = selector.get_cached_hashes()

# Clear cache when done
selector.clear_cache()
```

### Working with SelectionResult

```python
result = select_diverse_files(file_paths, n_select=5, cache_dir='/tmp/cache')

# List-like interface
print(len(result))           # 5
print(result[0])             # First index
print(result[1:3])           # Slice
print(list(result))          # Convert to list

# Iterate over indices
for idx in result:
    print(f"File: {file_paths[idx]}")

# Access additional information
print(result.file_paths)      # Selected file paths
print(result.hashes)          # All TLSH hashes (if cached)
print(result.diversity_scores) # Diversity score for each selection
print(result.elapsed_time)    # Time taken

# Convert to dictionary
result_dict = result.to_dict()
```

## How It Works

The selection algorithm uses a greedy approach:

1. **Hash Computation**: Computes TLSH hash for each file (with optional caching and parallelization)
2. **Random First Selection**: Randomly selects the first file
3. **Greedy Selection**: Iteratively selects files with maximum minimum distance from already selected files
4. **Distance Tracking**: Uses efficient NumPy arrays to track minimum distances

**Time Complexity**: O(m×n) where n is the total number of files and m is the number to select.

**TLSH Distance**: Lower values indicate more similar files. The algorithm maximizes the minimum distance to ensure diversity.

## API Reference

### `select_diverse_files()`

```python
def select_diverse_files(
    file_paths: list[str],
    n_select: int,
    *,
    cache_dir: str | None = None,
    verbose: bool = False,
    n_jobs: int = 1,
    random_state: int | None = None,
) -> SelectionResult:
```

**Parameters:**
- `file_paths`: List of file paths to select from
- `n_select`: Number of files to select
- `cache_dir`: Directory for caching TLSH hashes (None = no caching)
- `verbose`: Show progress bars and detailed information
- `n_jobs`: Number of parallel workers (1 = sequential, -1 = all cores)
- `random_state`: Random seed for reproducibility

**Returns:** `SelectionResult` object (list-like)

### `FileSelector` Class

```python
class FileSelector:
    def __init__(
        self,
        *,
        cache_dir: str | None = None,
        n_jobs: int = 1,
        verbose: bool = False,
    )

    def select(
        self,
        file_paths: list[str],
        n_select: int,
        *,
        verbose: bool | None = None,
        random_state: int | None = None,
    ) -> SelectionResult

    def compute_hashes(
        self,
        file_paths: list[str],
        *,
        verbose: bool | None = None,
    ) -> dict[str, str]

    def get_cached_hashes(self) -> dict[str, str]

    def clear_cache(self) -> None
```

### `SelectionResult` Class

```python
@dataclass(frozen=True)
class SelectionResult:
    indices: tuple[int, ...]           # Selected file indices
    file_paths: tuple[str, ...]        # Selected file paths
    hashes: dict[str, str] | None      # All TLSH hashes (if cached)
    diversity_scores: tuple[float, ...] | None  # Diversity scores
    elapsed_time: float | None         # Execution time

    # List-like interface
    def __iter__(self) -> Iterator[int]
    def __getitem__(self, key) -> int | tuple[int, ...]
    def __len__(self) -> int
    def to_dict(self) -> dict[str, Any]
```

## Performance Tips

1. **Use Caching**: Enable `cache_dir` when running multiple selections on the same dataset
2. **Parallel Processing**: Use `n_jobs=-1` for large datasets (>1000 files)
3. **Pre-compute Hashes**: Use `FileSelector.compute_hashes()` to separate hash computation from selection
4. **Cache Format**: Default pickle format is fastest; JSON is human-readable but slower

## Limitations

- TLSH requires files to be at least 50 bytes
- Very small files will be automatically skipped
- Cache invalidation is based on file mtime and size
- Parallel processing has overhead; only beneficial for large datasets

## Error Handling

```python
from tlsh_selector import select_diverse_files, InsufficientFilesError

try:
    result = select_diverse_files(file_paths, n_select=100)
except InsufficientFilesError as e:
    print(f"Not enough valid files: {e}")
except ValueError as e:
    print(f"Invalid parameters: {e}")
```

## Development

### Setup

```bash
git clone https://github.com/yourusername/tlsh-selector.git
cd tlsh-selector
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=tlsh_selector  # With coverage
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [TLSH](https://github.com/trendmicro/tlsh) by Trend Micro for the locality sensitive hashing algorithm
- Inspired by the need for efficient dataset diversification in malware analysis

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{tlsh_selector,
  title = {tlsh-selector: Select diverse files using TLSH},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/tlsh-selector}
}
```
