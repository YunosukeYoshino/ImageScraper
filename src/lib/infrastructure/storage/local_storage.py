"""Local file storage implementation."""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from typing import Optional

from ..http.http_client import request_with_retry

logger = logging.getLogger(__name__)


def hash_filename(url: str) -> str:
    """Generate hash-based filename from URL.

    Args:
        url: Source URL

    Returns:
        Hash-based filename with extension
    """
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    ext = os.path.splitext(url.split("?")[0])[1] or ".img"
    return f"{h}{ext}"


def ensure_directory(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)


def download_image(url: str, dest_dir: str) -> Optional[str]:
    """Download image from URL to local directory.

    Args:
        url: Image URL
        dest_dir: Destination directory

    Returns:
        Path to saved file, or None if failed
    """
    try:
        r = request_with_retry(url, retries=2)
        content_type = r.headers.get("Content-Type", "")
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or os.path.splitext(url.split("?")[0])[1]
        if not ext:
            ext = ".bin"

        filename = hash_filename(url)
        if not os.path.splitext(filename)[1] and ext:
            filename += ext

        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "wb") as f:
            f.write(r.content)

        logger.info(f"Saved {url} -> {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return None


class LocalStorage:
    """Local file storage implementation."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        ensure_directory(base_dir)

    def save(self, data: bytes, filename: str, directory: str = "") -> str:
        """Save data to local file.

        Args:
            data: Binary content
            filename: Target filename
            directory: Subdirectory (relative to base_dir)

        Returns:
            Full path to saved file
        """
        target_dir = os.path.join(self.base_dir, directory) if directory else self.base_dir
        ensure_directory(target_dir)
        filepath = os.path.join(target_dir, filename)

        with open(filepath, "wb") as f:
            f.write(data)

        return filepath

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        full_path = os.path.join(self.base_dir, path)
        return os.path.exists(full_path)

    def delete(self, path: str) -> bool:
        """Delete file."""
        full_path = os.path.join(self.base_dir, path)
        try:
            os.remove(full_path)
            return True
        except OSError:
            return False
