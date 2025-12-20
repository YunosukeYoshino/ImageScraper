from __future__ import annotations

"""Topic-based image discovery orchestrator.

Responsibilities:
- Query search provider(s) for candidate pages
- Parse result pages and extract image URLs
- Respect robots.txt for pages
- Write deterministic query logs
- Produce provenance entries
- Filter and download images (US2)
"""

from typing import List, Tuple, Optional, Callable
import logging
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .models_discovery import ProvenanceEntry, PreviewResult, QueryLogEntry, DownloadFilter
from .image_scraper import robots_allowed, list_images, list_images_with_metadata, download_images_parallel, _hash_name
from . import search_provider
from .rate_limit import TokenBucket
from .relevance_scorer import calculate_relevance_score, extract_filename_from_url, extract_domain_from_url

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "duckduckgo"

_DISCOVERY_LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "discovery_logs"))

# Rate limiter for search provider (max 2 requests per second)
_discovery_rate_limiter = TokenBucket(capacity=2, fill_rate=2.0)


def _apply_rate_limit() -> None:
    """Apply rate limiting before network requests."""
    _discovery_rate_limiter.acquire(1)


# Wire rate limiter to search provider
search_provider.set_rate_limiter(_apply_rate_limit)


def _slugify_topic(topic: str) -> str:
    s = topic.strip().lower()
    s = re.sub(r"[^a-z0-9\-\_\sぁ-んァ-ヶ一-龥]", " ", s)
    s = re.sub(r"\s+", "_", s)
    return s[:60] if s else "topic"


def discover_topic(topic: str, limit: int = 50) -> PreviewResult:
    """Discover images for a topic using a search provider and return a preview.

    - Queries provider for candidate pages
    - Respects robots.txt for pages and images (via list_images)
    - Builds ProvenanceEntry list up to `limit`
    - Writes deterministic query log to discovery_logs
    """
    logger.info("discover_topic.start topic=%s limit=%d provider=%s", topic, limit, DEFAULT_PROVIDER)
    # 1) Search pages via provider (mockable)
    try:
        page_urls = search_provider.search_pages(topic, provider=DEFAULT_PROVIDER, max_pages=20)
    except Exception as e:
        logger.warning("search_provider.error topic=%s err=%s", topic, e)
        page_urls = []

    images_collected: List[ProvenanceEntry] = []
    pages_considered = 0
    for page in page_urls:
        if limit and len(images_collected) >= limit:
            break
        pages_considered += 1
        if not robots_allowed(page):
            logger.warning("robots page disallow: %s", page)
            continue
        try:
            # Use metadata-aware extraction for relevance scoring
            image_metas = list_images_with_metadata(page, limit=None, respect_robots=True)
        except Exception as e:
            logger.warning("list_images.failed page=%s err=%s", page, e)
            continue
        for meta in image_metas:
            if limit and len(images_collected) >= limit:
                break
            # Calculate relevance score
            filename = extract_filename_from_url(meta.url)
            domain = extract_domain_from_url(meta.url)
            score = calculate_relevance_score(
                topic=topic,
                alt_text=meta.alt,
                filename=filename,
                context_text=meta.context,
                domain=domain,
            )
            images_collected.append(
                ProvenanceEntry(
                    topic=topic,
                    source_page_url=page,
                    image_url=meta.url,
                    discovery_method="SERP",
                    relevance_score=score,
                    alt_text=meta.alt,
                    filename=filename,
                    context_text=meta.context,
                )
            )

    # Sort by relevance score (highest first)
    images_collected.sort(key=lambda e: e.relevance_score, reverse=True)

    query_log = QueryLogEntry(
        topic=topic,
        provider=DEFAULT_PROVIDER,
        query=topic,
        page_count=pages_considered,
        image_count=len(images_collected),
    )

    # 2) Write deterministic query log
    try:
        os.makedirs(_DISCOVERY_LOG_DIR, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        fn = f"{ts}_{_slugify_topic(topic)}.json"
        path = os.path.join(_DISCOVERY_LOG_DIR, fn)
        payload = {
            "topic": topic,
            "provider": DEFAULT_PROVIDER,
            "query": topic,
            "timestamp": query_log.timestamp.isoformat(),
            "page_count": pages_considered,
            "image_count": len(images_collected),
            "pages": page_urls,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("query_log.written path=%s", path)
    except Exception as e:
        logger.warning("query_log.write_failed topic=%s err=%s", topic, e)

    result = PreviewResult(
        topic=topic,
        entries=images_collected,
        total_images=len(images_collected),
        provider=DEFAULT_PROVIDER,
        query_log=query_log,
    )
    logger.info("discover_topic.end topic=%s count=%d", topic, result.total_images)
    return result


# ---------------------------------------------------------------------------
# US2: Filtering & Selective Download
# ---------------------------------------------------------------------------

def filter_entries(
    entries: List[ProvenanceEntry],
    download_filter: Optional[DownloadFilter] = None,
) -> List[ProvenanceEntry]:
    """Apply filters to provenance entries.

    Args:
        entries: List of ProvenanceEntry to filter.
        download_filter: Optional DownloadFilter with domain/resolution constraints.

    Returns:
        Filtered list of ProvenanceEntry.
    """
    if not download_filter:
        return entries

    filtered: List[ProvenanceEntry] = []
    for entry in entries:
        image_url = str(entry.image_url)
        parsed = urlparse(image_url)
        domain = parsed.netloc.lower()

        # Domain allow list (whitelist)
        if download_filter.allow_domains:
            allowed = any(
                domain == d.lower() or domain.endswith("." + d.lower())
                for d in download_filter.allow_domains
            )
            if not allowed:
                logger.debug("filter.domain_not_allowed url=%s domain=%s", image_url, domain)
                continue

        # Domain deny list (blacklist)
        if download_filter.deny_domains:
            denied = any(
                domain == d.lower() or domain.endswith("." + d.lower())
                for d in download_filter.deny_domains
            )
            if denied:
                logger.debug("filter.domain_denied url=%s domain=%s", image_url, domain)
                continue

        # Note: Resolution filtering (min_width, min_height) requires fetching image headers
        # or downloading. For efficiency, we skip resolution check at filter stage and
        # apply it during download if needed.

        filtered.append(entry)

    logger.info("filter_entries input=%d output=%d", len(entries), len(filtered))
    return filtered


def _check_image_resolution(filepath: str, min_width: Optional[int], min_height: Optional[int]) -> bool:
    """Check if image meets minimum resolution requirements.

    Args:
        filepath: Path to the image file.
        min_width: Minimum width in pixels (None = no limit).
        min_height: Minimum height in pixels (None = no limit).

    Returns:
        True if image meets requirements, False otherwise.
    """
    if not HAS_PIL:
        logger.warning("PIL not available, skipping resolution check for %s", filepath)
        return True

    if min_width is None and min_height is None:
        return True

    try:
        with Image.open(filepath) as img:
            width, height = img.size
            if min_width is not None and width < min_width:
                logger.debug("resolution.reject width=%d < min_width=%d file=%s", width, min_width, filepath)
                return False
            if min_height is not None and height < min_height:
                logger.debug("resolution.reject height=%d < min_height=%d file=%s", height, min_height, filepath)
                return False
            return True
    except Exception as e:
        logger.warning("resolution.check_failed file=%s err=%s", filepath, e)
        return True  # Keep file on error (conservative approach)


def download_selected(
    entries: List[ProvenanceEntry],
    output_dir: str,
    download_filter: Optional[DownloadFilter] = None,
    max_workers: int = 8,
    respect_robots: bool = True,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Tuple[List[str], str]:
    """Download selected images and write provenance_index.json.

    Args:
        entries: List of ProvenanceEntry to download.
        output_dir: Destination directory.
        download_filter: Optional filter (domain filtering applied here).
        max_workers: Parallel download workers.
        respect_robots: Skip images disallowed by robots.txt.
        progress_cb: Optional progress callback(done, total).

    Returns:
        Tuple of (list of saved file paths, path to provenance_index.json).
    """
    # Apply domain filters
    filtered_entries = filter_entries(entries, download_filter)
    if not filtered_entries:
        logger.warning("download_selected: no entries after filtering")
        # Still write empty provenance index
        os.makedirs(output_dir, exist_ok=True)
        index_path = os.path.join(output_dir, "provenance_index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"entries": [], "total": 0}, f, ensure_ascii=False, indent=2)
        return [], index_path

    image_urls = [str(e.image_url) for e in filtered_entries]

    # Download images
    saved_files = download_images_parallel(
        image_urls,
        output_dir,
        max_workers=max_workers,
        respect_robots=respect_robots,
        progress_cb=progress_cb,
    )

    # Apply resolution filter after download (FR-005)
    min_width = download_filter.min_width if download_filter else None
    min_height = download_filter.min_height if download_filter else None
    if min_width is not None or min_height is not None:
        files_before = len(saved_files)
        filtered_files = []
        for filepath in saved_files:
            if _check_image_resolution(filepath, min_width, min_height):
                filtered_files.append(filepath)
            else:
                # Remove file that doesn't meet resolution requirements
                try:
                    os.remove(filepath)
                    logger.info("resolution.removed file=%s", filepath)
                except OSError as e:
                    logger.warning("resolution.remove_failed file=%s err=%s", filepath, e)
        saved_files = filtered_files
        logger.info("resolution_filter applied=%d removed=%d", files_before, files_before - len(saved_files))

    # Build provenance index mapping filename -> provenance
    # Clean Architecture: 実際に保存されたファイルから逆マッピングして正確なファイル名を取得
    url_to_entry = {str(e.image_url): e for e in filtered_entries}

    # URL hash -> URL のマッピングを作成（堅牢な逆参照のため）
    import hashlib
    url_hash_to_url = {
        hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]: url
        for url in image_urls
    }

    provenance_records = []
    for saved_path in saved_files:
        filename = os.path.basename(saved_path)
        # ファイル名から拡張子を除いたハッシュ部分を取得
        file_hash = os.path.splitext(filename)[0]

        # ハッシュから元のURLを取得
        original_url = url_hash_to_url.get(file_hash)
        if not original_url:
            logger.warning("provenance: hash not found for file=%s", filename)
            continue

        entry = url_to_entry.get(original_url)
        if entry:
            provenance_records.append({
                "filename": filename,
                "image_url": str(entry.image_url),
                "source_page_url": str(entry.source_page_url),
                "topic": entry.topic,
                "discovery_method": entry.discovery_method,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            })

    # Write provenance_index.json
    os.makedirs(output_dir, exist_ok=True)
    index_path = os.path.join(output_dir, "provenance_index.json")
    index_data = {
        "entries": provenance_records,
        "total": len(provenance_records),
        "filter_applied": {
            "allow_domains": download_filter.allow_domains if download_filter else None,
            "deny_domains": download_filter.deny_domains if download_filter else None,
            "min_width": download_filter.min_width if download_filter else None,
            "min_height": download_filter.min_height if download_filter else None,
        } if download_filter else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    logger.info("provenance_index.written path=%s entries=%d", index_path, len(provenance_records))

    return saved_files, index_path
