"""Image scraping and optional Google Drive upload utilities.

This module provides functions to:
- Fetch an HTML page via requests with robust headers and retry logic.
- Parse image URLs using BeautifulSoup and optional filtering.
- Download images to a local directory with collision avoidance.
- (Optional) Upload downloaded images to Google Drive using the Drive API.

Google Drive Upload Requires Authentication:
- There is NO truly unauthenticated library for uploading to private Google Drive.
- For automation, use one of:
  * Service Account (preferred for backend jobs) + google-api-python-client
  * OAuth user consent flow (pydrive2) if acting on a user's personal Drive
  * rclone (manual one-time auth) then invoke shell commands to copy files

If you only need to make images available publicly, consider using an object storage
service (e.g., Cloud Storage, S3) or a shared Drive folder after authentication.

Minimal usage example (local save only):

from src.lib.image_scraper import scrape_images
scrape_images("https://example.com", "downloaded_images")

To enable Drive upload you must first create credentials JSON and share a folder if using service account.
"""
from __future__ import annotations
import os
import re
import time
import mimetypes
from dataclasses import dataclass
from typing import Iterable, List, Optional
import logging
import hashlib
from urllib.parse import urlparse, urljoin
from urllib import robotparser

import requests
from bs4 import BeautifulSoup

# Optional import: wrap in try/except so local-only usage works.
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    _DRIVE_AVAILABLE = True
except Exception:  # pragma: no cover - absence is acceptable
    _DRIVE_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

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
            logging.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_exc}")


def _is_image_url(url: str) -> bool:
    return bool(IMG_EXT_PATTERN.search(url)) or url.split("?")[0].lower().endswith(tuple([".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]))


def _normalize_url(src: str, base: str) -> str:
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    # relative path
    return requests.compat.urljoin(base, src)


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
        logging.info(f"Saved {url} -> {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None


def _init_drive(service_account_file: str, scopes: Optional[List[str]] = None):
    if not _DRIVE_AVAILABLE:
        raise RuntimeError("google-api-python-client not available. Install google-api-python-client and google-auth.")
    scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    return build("drive", "v3", credentials=creds)


def _drive_upload(drive_service, local_path: str, parent_folder_id: Optional[str] = None) -> str:
    from googleapiclient.http import MediaFileUpload
    file_metadata = {"name": os.path.basename(local_path)}
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]
    media = MediaFileUpload(local_path, resumable=True)
    created = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = created.get("id")
    logging.info(f"Uploaded to Drive: {local_path} -> {file_id}")
    return file_id


def scrape_images(url: str, output_dir: str, limit: Optional[int] = None, drive_service=None, drive_folder_id: Optional[str] = None, respect_robots: bool = True) -> ScrapeResult:
    """Scrape image sources from a page and optionally upload them to Google Drive.

    Args:
        url: Page URL to scrape.
        output_dir: Local directory to store images.
        limit: Optional maximum number of images to process.
        drive_service: Optional Google Drive service instance (authenticated) for upload.
    drive_folder_id: Optional folder ID in Google Drive where images will be placed.
    respect_robots: When True, abort if robots.txt disallows fetching the page.

    Returns:
        ScrapeResult with details of the operation.
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
        raw_sources.append(src.strip())

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
            logging.warning(f"robots.txt disallows fetching image: {img_url}")
            continue
        local = _download_image(img_url, output_dir)
        if local:
            saved_files.append(local)
            if drive_service:
                try:
                    file_id = _drive_upload(drive_service, local, parent_folder_id=drive_folder_id)
                    drive_ids.append(file_id)
                except Exception as e:
                    logging.error(f"Drive upload failed for {local}: {e}")

    return ScrapeResult(page_url=url, image_urls=normalized, saved_files=saved_files, drive_file_ids=drive_ids)


__all__ = [
    "scrape_images",
    "ScrapeResult",
    "_init_drive",
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
        raw_sources.append(src.strip())

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


def download_images(image_urls: List[str], output_dir: str, drive_service=None, drive_folder_id: Optional[str] = None, respect_robots: bool = True) -> List[str]:
    """Download provided image URLs to output_dir, optionally uploading to Drive. Returns list of saved file paths."""
    _ensure_dir(output_dir)
    saved_files: List[str] = []
    for img_url in image_urls:
        if respect_robots and not _robots_allowed(img_url):
            logging.warning(f"robots.txt disallows fetching image: {img_url}")
            continue
        local = _download_image(img_url, output_dir)
        if local:
            saved_files.append(local)
            if drive_service:
                try:
                    _ = _drive_upload(drive_service, local, parent_folder_id=drive_folder_id)
                except Exception as e:
                    logging.error(f"Drive upload failed for {local}: {e}")
    return saved_files

