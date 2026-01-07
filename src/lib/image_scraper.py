"""Image scraping and optional Google Drive upload utilities.

This module provides functions to:
- Fetch an HTML page via requests with robust headers and retry logic.
- Parse image URLs using BeautifulSoup and optional filtering.
- Download images to a local directory with collision avoidance.
- (Optional) Upload downloaded images to Google Drive using pluggable strategies.

Google Drive Upload Options:
1. Service Account (google-api-python-client)
   - Best for backend automation
   - Requires service account JSON key
   - Target folder must be shared with service account email

2. rclone (command-line tool)
   - Best for personal Drive accounts
   - One-time OAuth authentication via browser
   - No code-level credentials needed after setup

Minimal usage example (local save only):

    from src.lib.image_scraper import scrape_images
    scrape_images("https://example.com", "downloaded_images")

With Google Drive upload (rclone) - note: drive_uploader is keyword-only:

    from src.lib.drive_uploader import create_uploader
    uploader = create_uploader(method="rclone")
    scrape_images(
        "https://example.com",
        "images",
        drive_uploader=uploader,  # keyword-only parameter
        drive_folder="backups"
    )

With Google Drive upload (service account) - note: drive_uploader is keyword-only:

    from src.lib.drive_uploader import create_uploader
    uploader = create_uploader(method="service_account", service_account_file="key.json")
    scrape_images(
        "https://example.com",
        "images",
        drive_uploader=uploader,  # keyword-only parameter
        drive_folder="folder_id"
    )
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, List, Optional
from urllib import robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from src.lib.drive_uploader import DriveUploader

# Import the new DriveUploader abstraction
try:
    from src.lib.drive_uploader import DriveUploader as _DriveUploader

    _UPLOADER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _UPLOADER_AVAILABLE = False
    _DriveUploader: Any = None

# Legacy imports for backward compatibility (optional dependency)
try:
    from google.oauth2 import service_account  # ty: ignore[unresolved-import]
    from googleapiclient.discovery import build  # ty: ignore[unresolved-import]

    _LEGACY_DRIVE_AVAILABLE = True
except Exception:  # pragma: no cover - absence is acceptable
    _LEGACY_DRIVE_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ImageScraper/1.0; +https://github.com/example)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

IMG_EXT_PATTERN = re.compile(r"\.(?:png|jpe?g|gif|webp|svg)(?:\?.*)?$", re.IGNORECASE)


@dataclass
class ScrapeResult:
    page_url: str
    image_urls: List[str]
    saved_files: List[str]
    drive_file_ids: List[str]


def _request_with_retry(url: str, retries: int = 3, backoff: float = 1.2) -> requests.Response:
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except Exception as e:  # broad for retry
            last_exc = e
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_exc}")


def _is_image_url(url: str) -> bool:
    if IMG_EXT_PATTERN.search(url):
        return True
    extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")
    return url.split("?")[0].lower().endswith(extensions)


def _normalize_url(src: str, base: str) -> str:
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    # relative path - use stdlib urljoin instead of requests.compat
    from urllib.parse import urljoin

    return urljoin(base, src)


def _robots_allowed(target_url: str, user_agent: str = DEFAULT_HEADERS["User-Agent"]) -> bool:
    """Return True if robots.txt allows fetching target_url. If robots.txt is
    unreachable, default to True (fail-open) to avoid false negatives.
    """
    try:
        parsed = urlparse(target_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        # If no rules present, can_fetch returns True by default
        return rp.can_fetch(user_agent, target_url)
    except Exception:
        return True


def robots_allowed(target_url: str, user_agent: str = DEFAULT_HEADERS["User-Agent"]) -> bool:
    """Public wrapper to check robots.txt allowance for a given URL.

    Exposed for reuse by other modules (e.g., topic discovery). Fails open
    if robots.txt is unreachable.
    """
    return _robots_allowed(target_url, user_agent=user_agent)


def _hash_name(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    ext = os.path.splitext(url.split("?")[0])[1] or ".img"
    return f"{h}{ext}"


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _download_image(url: str, dest_dir: str) -> Optional[str]:
    try:
        r = _request_with_retry(url, retries=2)
        content_type = r.headers.get("Content-Type", "")
        # Determine extension
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or os.path.splitext(url.split("?")[0])[1]
        if not ext:
            ext = ".bin"
        filename = _hash_name(url)
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


def _upload_to_drive(uploader: "DriveUploader", local_path: str, remote_folder: Optional[str] = None) -> str:
    """Upload a file to Google Drive using the provided uploader strategy.

    Args:
        uploader: DriveUploader instance (ServiceAccountUploader or RcloneUploader)
        local_path: Path to local file
        remote_folder: Target folder (folder ID for service account, path for rclone)

    Returns:
        Identifier of uploaded file (file ID or remote path)
    """
    return uploader.upload_file(local_path, remote_folder)


# Legacy functions - kept for backward compatibility but deprecated
def _init_drive(service_account_file: str, scopes: Optional[List[str]] = None):
    """DEPRECATED: Use create_uploader() from drive_uploader module instead.

    This function is kept for backward compatibility with existing code.
    """
    if not _LEGACY_DRIVE_AVAILABLE:
        raise RuntimeError("google-api-python-client not available. Install google-api-python-client and google-auth.")
    scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    return build("drive", "v3", credentials=creds)


def _drive_upload(drive_service, local_path: str, parent_folder_id: Optional[str] = None) -> str:
    """DEPRECATED: Use DriveUploader.upload_file() instead.

    This function is kept for backward compatibility with existing code.
    """
    from googleapiclient.http import MediaFileUpload  # ty: ignore[unresolved-import]

    file_metadata = {"name": os.path.basename(local_path)}
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]
    media = MediaFileUpload(local_path, resumable=True)
    created = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = created.get("id")
    logger.info(f"Uploaded to Drive (legacy): {local_path} -> {file_id}")
    return file_id


def scrape_images(
    url: str,
    output_dir: str,
    limit: Optional[int] = None,
    drive_service=None,
    drive_folder_id: Optional[str] = None,
    respect_robots: bool = True,
    *,  # All parameters after this are keyword-only
    drive_uploader: Optional["DriveUploader"] = None,
    drive_folder: Optional[str] = None,
) -> ScrapeResult:
    """Scrape image sources from a page and optionally upload them to Google Drive.

    Args:
        url: Page URL to scrape
        output_dir: Local directory to store images
        limit: Optional maximum number of images to process
        drive_service: (DEPRECATED) Legacy Google Drive service instance
        drive_folder_id: (DEPRECATED) Legacy folder ID parameter
        respect_robots: When True, abort if robots.txt disallows fetching the page
        drive_uploader: (Keyword-only) DriveUploader instance for uploads (new interface)
        drive_folder: (Keyword-only) Folder identifier (folder ID or path depending on uploader)

    Returns:
        ScrapeResult with details of the operation

    Example:
        # Modern usage with rclone (keyword-only parameters)
        from src.lib.drive_uploader import create_uploader
        uploader = create_uploader(method="rclone")
        result = scrape_images(
            "https://example.com",
            "./images",
            drive_uploader=uploader,
            drive_folder="backups"
        )

        # Legacy positional usage still works
        result = scrape_images("https://example.com", "./images", None, service, folder_id, True)
    """
    _ensure_dir(output_dir)
    if respect_robots and not _robots_allowed(url):
        raise PermissionError(f"Blocked by robots.txt: {url}")
    response = _request_with_retry(url)
    soup = BeautifulSoup(response.text, "html.parser")

    raw_sources: List[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src:
            continue
        src_val = src if isinstance(src, str) else str(src)
        raw_sources.append(src_val.strip())

    # Deduplicate and normalize
    normalized: List[str] = []
    seen = set()
    for src in raw_sources:
        full = _normalize_url(src, url)
        if full in seen:
            continue
        seen.add(full)
        if _is_image_url(full):
            normalized.append(full)

    if limit is not None:
        normalized = normalized[:limit]

    saved_files: List[str] = []
    drive_ids: List[str] = []

    for img_url in normalized:
        if respect_robots and not _robots_allowed(img_url):
            logger.warning(f"robots.txt disallows fetching image: {img_url}")
            continue
        local = _download_image(img_url, output_dir)
        if local:
            saved_files.append(local)

            # Handle Drive upload with new interface (preferred) or legacy interface
            if drive_uploader:
                try:
                    file_id = _upload_to_drive(drive_uploader, local, drive_folder)
                    drive_ids.append(file_id)
                except Exception as e:
                    logger.error(f"Drive upload failed for {local}: {e}")
            elif drive_service:
                # Legacy path for backward compatibility
                try:
                    file_id = _drive_upload(drive_service, local, parent_folder_id=drive_folder_id)
                    drive_ids.append(file_id)
                except Exception as e:
                    logger.error(f"Drive upload failed for {local}: {e}")

    return ScrapeResult(page_url=url, image_urls=normalized, saved_files=saved_files, drive_file_ids=drive_ids)


__all__ = [
    "scrape_images",
    "ScrapeResult",
    "_init_drive",
    "robots_allowed",
    "list_images",
    "list_images_with_metadata",
    "ImageMetadata",
    "download_images",
    "download_images_parallel",
]


# -- New helpers for UI preview/selective download --
def list_images(url: str, limit: Optional[int] = None, respect_robots: bool = True) -> List[str]:
    """Return normalized image URLs from a page without downloading."""
    if respect_robots and not _robots_allowed(url):
        raise PermissionError(f"Blocked by robots.txt: {url}")
    response = _request_with_retry(url)
    soup = BeautifulSoup(response.text, "html.parser")
    raw_sources: List[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src:
            continue
        src_val = src if isinstance(src, str) else str(src)
        raw_sources.append(src_val.strip())

    normalized: List[str] = []
    seen = set()
    for src in raw_sources:
        full = _normalize_url(src, url)
        if full in seen:
            continue
        seen.add(full)
        if _is_image_url(full):
            normalized.append(full)
    if limit is not None:
        normalized = normalized[:limit]
    return normalized


def download_images(
    image_urls: List[str],
    output_dir: str,
    drive_service=None,
    drive_folder_id: Optional[str] = None,
    respect_robots: bool = True,
    *,  # All parameters after this are keyword-only
    drive_uploader: Optional["DriveUploader"] = None,
    drive_folder: Optional[str] = None,
) -> List[str]:
    """Download provided image URLs to output_dir, optionally uploading to Drive.

    Args:
        image_urls: List of image URLs to download
        output_dir: Local directory to save images
        drive_service: (DEPRECATED) Legacy Google Drive service instance
        drive_folder_id: (DEPRECATED) Legacy folder ID parameter
        respect_robots: When True, skip images blocked by robots.txt
        drive_uploader: (Keyword-only) DriveUploader instance for uploads (new interface)
        drive_folder: (Keyword-only) Folder identifier (folder ID or path)

    Returns:
        List of saved file paths

    Example:
        # Modern usage with keyword-only parameters
        from src.lib.drive_uploader import create_uploader
        uploader = create_uploader(method="rclone")
        files = download_images(
            urls,
            "./images",
            drive_uploader=uploader,
            drive_folder="backups"
        )

        # Legacy positional usage still works
        files = download_images(urls, "./images", service, folder_id, True)
    """
    _ensure_dir(output_dir)
    saved_files: List[str] = []
    for img_url in image_urls:
        if respect_robots and not _robots_allowed(img_url):
            logger.warning(f"robots.txt disallows fetching image: {img_url}")
            continue
        local = _download_image(img_url, output_dir)
        if local:
            saved_files.append(local)

            # Handle Drive upload with new interface (preferred) or legacy interface
            if drive_uploader:
                try:
                    _ = _upload_to_drive(drive_uploader, local, drive_folder)
                except Exception as e:
                    logger.error(f"Drive upload failed for {local}: {e}")
            elif drive_service:
                # Legacy path for backward compatibility
                try:
                    _ = _drive_upload(drive_service, local, parent_folder_id=drive_folder_id)
                except Exception as e:
                    logger.error(f"Drive upload failed for {local}: {e}")
    return saved_files


@dataclass
class ImageMetadata:
    """Metadata extracted from an image element."""

    url: str
    alt: Optional[str] = None
    context: Optional[str] = None


def _extract_context_text(img_tag, max_length: int = 200) -> Optional[str]:
    """Extract surrounding text from image's parent elements."""
    try:
        # Try to get text from parent elements
        parent = img_tag.parent
        for _ in range(3):  # Go up to 3 levels
            if parent is None:
                break
            text = parent.get_text(separator=" ", strip=True)
            if text and len(text) > 10:
                return text[:max_length]
            parent = parent.parent
        return None
    except Exception:
        return None


def list_images_with_metadata(
    url: str, limit: Optional[int] = None, respect_robots: bool = True
) -> List[ImageMetadata]:
    """Return image URLs with metadata (alt, context) from a page.

    Args:
        url: Page URL to scrape
        limit: Maximum number of images to return
        respect_robots: Check robots.txt before fetching

    Returns:
        List of ImageMetadata objects containing url, alt text, and context
    """
    if respect_robots and not _robots_allowed(url):
        raise PermissionError(f"Blocked by robots.txt: {url}")

    response = _request_with_retry(url)
    soup = BeautifulSoup(response.text, "html.parser")

    results: List[ImageMetadata] = []
    seen: set[str] = set()

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src:
            continue

        src_val = src if isinstance(src, str) else str(src)
        full_url = _normalize_url(src_val.strip(), url)
        if full_url in seen:
            continue
        seen.add(full_url)

        if not _is_image_url(full_url):
            continue

        # Extract metadata
        alt_attr = img.get("alt", "")
        alt = (alt_attr if isinstance(alt_attr, str) else str(alt_attr)).strip() or None
        context = _extract_context_text(img)

        results.append(ImageMetadata(url=full_url, alt=alt, context=context))

        if limit is not None and len(results) >= limit:
            break

    return results


def download_images_parallel(
    image_urls: List[str],
    output_dir: str,
    max_workers: int = 8,
    respect_robots: bool = True,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> List[str]:
    """Parallel version of download_images with progress callback.

    Args:
        image_urls: list of image URLs to download.
        output_dir: destination directory.
        max_workers: concurrency level.
        respect_robots: skip disallowed images.
        progress_cb: optional callback invoked as progress_cb(done_count, total).
    Returns:
        List of saved file paths (order not guaranteed).
    """
    _ensure_dir(output_dir)
    total = len(image_urls)
    done = 0
    results: List[str] = []

    def _task(u: str) -> Optional[str]:
        if respect_robots and not _robots_allowed(u):
            logger.warning(f"robots.txt disallows fetching image: {u}")
            return None
        return _download_image(u, output_dir)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_map = {ex.submit(_task, u): u for u in image_urls}
        for fut in as_completed(future_map):
            res = None
            try:
                res = fut.result()
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Parallel download failed: {e}")
            if res:
                results.append(res)
            done += 1
            if progress_cb:
                try:
                    progress_cb(done, total)
                except Exception:  # pragma: no cover
                    pass
    return results
