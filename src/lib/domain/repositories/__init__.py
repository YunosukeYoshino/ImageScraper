"""Repository interfaces - Abstract data access contracts."""
from .search_repository import SearchRepository
from .storage_repository import StorageRepository

__all__ = [
    "SearchRepository",
    "StorageRepository",
]
