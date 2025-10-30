"""TLSH hash computation and caching utilities."""

import json
import os
import pickle
from pathlib import Path
from typing import Literal

import tlsh

from .exceptions import CacheError, InvalidHashError


def compute_tlsh_hash(file_path: str) -> str:
    """
    Compute TLSH hash for a single file.

    Args:
        file_path: Path to the file

    Returns:
        TLSH hash string

    Raises:
        InvalidHashError: If the file cannot be hashed (e.g., too small, not readable)
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        hash_value = tlsh.hash(data)
        if not hash_value:
            raise InvalidHashError(f"Failed to compute TLSH hash for {file_path} (file may be too small)")
        return hash_value
    except FileNotFoundError:
        raise InvalidHashError(f"File not found: {file_path}")
    except Exception as e:
        raise InvalidHashError(f"Error computing TLSH hash for {file_path}: {e}")


class CacheManager:
    """
    Manage TLSH hash caching with automatic invalidation on file changes.

    Supports multiple cache formats: pickle (fast), json (readable), sqlite (scalable).
    Automatically detects file changes via mtime and size.
    """

    def __init__(
        self,
        cache_dir: str,
        format: Literal["pickle", "json"] = "pickle",
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
            format: Cache format ('pickle' or 'json')
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.format = format
        self.cache_file = self.cache_dir / f"tlsh_cache.{format}"
        self._cache: dict[str, dict] = {}
        self._dirty = False
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            self._cache = {}
            return

        try:
            if self.format == "pickle":
                with open(self.cache_file, "rb") as f:
                    self._cache = pickle.load(f)
            else:  # json
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
        except Exception as e:
            raise CacheError(f"Failed to load cache from {self.cache_file}: {e}")

    def _save_cache(self) -> None:
        """Save cache to disk."""
        if not self._dirty:
            return

        try:
            if self.format == "pickle":
                with open(self.cache_file, "wb") as f:
                    pickle.dump(self._cache, f)
            else:  # json
                with open(self.cache_file, "w") as f:
                    json.dump(self._cache, f, indent=2)
            self._dirty = False
        except Exception as e:
            raise CacheError(f"Failed to save cache to {self.cache_file}: {e}")

    def _get_file_metadata(self, file_path: str) -> tuple[float, int]:
        """
        Get file metadata for cache invalidation.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (modification time, file size)
        """
        stat = os.stat(file_path)
        return (stat.st_mtime, stat.st_size)

    def _is_cache_valid(self, file_path: str) -> bool:
        """
        Check if cached hash is still valid.

        Args:
            file_path: Path to the file

        Returns:
            True if cache is valid, False otherwise
        """
        if file_path not in self._cache:
            return False

        try:
            current_mtime, current_size = self._get_file_metadata(file_path)
            cached_mtime = self._cache[file_path]["mtime"]
            cached_size = self._cache[file_path]["size"]
            return current_mtime == cached_mtime and current_size == cached_size
        except (FileNotFoundError, KeyError):
            return False

    def get(self, file_path: str) -> str | None:
        """
        Get cached hash for a file.

        Args:
            file_path: Path to the file

        Returns:
            TLSH hash string if cached and valid, None otherwise
        """
        if self._is_cache_valid(file_path):
            return self._cache[file_path]["hash"]
        return None

    def set(self, file_path: str, hash_value: str) -> None:
        """
        Cache a hash for a file.

        Args:
            file_path: Path to the file
            hash_value: TLSH hash string
        """
        try:
            mtime, size = self._get_file_metadata(file_path)
            self._cache[file_path] = {
                "hash": hash_value,
                "mtime": mtime,
                "size": size,
            }
            self._dirty = True
        except FileNotFoundError:
            pass  # Ignore if file no longer exists

    def get_all_hashes(self) -> dict[str, str]:
        """
        Get all valid cached hashes.

        Returns:
            Dictionary mapping file paths to TLSH hashes
        """
        result = {}
        for file_path, data in self._cache.items():
            if self._is_cache_valid(file_path):
                result[file_path] = data["hash"]
        return result

    def clear(self) -> None:
        """Clear all cached hashes."""
        self._cache = {}
        self._dirty = True
        self._save_cache()

    def save(self) -> None:
        """Explicitly save cache to disk."""
        self._save_cache()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save cache."""
        self._save_cache()
