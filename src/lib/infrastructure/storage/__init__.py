"""Storage infrastructure - Local and remote file storage."""

from .local_storage import LocalStorage, download_image, hash_filename

__all__ = [
    "LocalStorage",
    "hash_filename",
    "download_image",
]
