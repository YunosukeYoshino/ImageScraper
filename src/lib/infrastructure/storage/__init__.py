"""Storage infrastructure - Local and remote file storage."""
from .local_storage import LocalStorage, hash_filename, download_image

__all__ = [
    "LocalStorage",
    "hash_filename",
    "download_image",
]
