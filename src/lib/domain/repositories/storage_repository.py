"""Storage repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageRepository(ABC):
    """Abstract interface for file storage.

    Implementations handle saving files to local filesystem
    or remote storage (e.g., Google Drive).
    """

    @abstractmethod
    def save(self, data: bytes, filename: str, directory: str) -> str:
        """Save data to storage.

        Args:
            data: Binary content to save
            filename: Name for the file
            directory: Target directory/folder

        Returns:
            Path or identifier of the saved file
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a file exists at the given path."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete a file at the given path.

        Returns:
            True if deleted successfully, False otherwise
        """
        pass
