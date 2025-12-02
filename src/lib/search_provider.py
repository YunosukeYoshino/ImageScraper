from __future__ import annotations
"""Search provider adapter for topic-based image discovery.

Provides search_pages() to query a search engine and return candidate page URLs.
Supports DuckDuckGo via duckduckgo_search library with rate limiting.
"""

import logging
import time
from typing import List, Optional, Callable
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Optional import for duckduckgo_search
try:
    from duckduckgo_search import DDGS
    _HAS_DDGS = True
except ImportError:
    _HAS_DDGS = False
    DDGS = None


# Rate limiter singleton (can be injected for testing)
_rate_limiter: Optional[Callable[[], None]] = None


def set_rate_limiter(limiter: Optional[Callable[[], None]]) -> None:
    """Set global rate limiter. Call limiter() before each network request."""
    global _rate_limiter
    _rate_limiter = limiter


def _wait_rate_limit() -> None:
    """Apply rate limiting if configured."""
    if _rate_limiter is not None:
        _rate_limiter()


def _is_valid_url(url: str) -> bool:
    """Check if a URL is valid and has http/https scheme."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _search_duckduckgo(topic: str, max_pages: int) -> List[str]:
    """Search DuckDuckGo using duckduckgo_search library."""
    if not _HAS_DDGS:
        logger.warning("duckduckgo_search not installed; returning empty results")
        return []

    urls: List[str] = []
    try:
        _wait_rate_limit()
        with DDGS() as ddgs:
            # Search for text results (pages containing images)
            # Append "images" to topic to find image-rich pages
            query = f"{topic} images"
            results = list(ddgs.text(query, max_results=max_pages * 2))

            for r in results:
                if len(urls) >= max_pages:
                    break
                href = r.get("href") or r.get("link") or ""
                if _is_valid_url(href):
                    urls.append(href)

        logger.info("duckduckgo.search topic=%s found=%d", topic, len(urls))
    except Exception as e:
        logger.warning("duckduckgo.search failed topic=%s err=%s", topic, e)

    return urls


def _search_duckduckgo_images(topic: str, max_pages: int) -> List[str]:
    """Search DuckDuckGo Images directly for image source pages."""
    if not _HAS_DDGS:
        logger.warning("duckduckgo_search not installed; returning empty results")
        return []

    source_pages: List[str] = set()
    try:
        _wait_rate_limit()
        with DDGS() as ddgs:
            results = list(ddgs.images(topic, max_results=max_pages * 5))

            for r in results:
                if len(source_pages) >= max_pages:
                    break
                # images() returns 'url' for image and 'source' for page
                page_url = r.get("source") or r.get("url") or ""
                if _is_valid_url(page_url) and page_url not in source_pages:
                    source_pages.add(page_url)

        logger.info("duckduckgo.images topic=%s source_pages=%d", topic, len(source_pages))
    except Exception as e:
        logger.warning("duckduckgo.images failed topic=%s err=%s", topic, e)

    return list(source_pages)[:max_pages]


def search_pages(topic: str, provider: str = "duckduckgo", max_pages: int = 20) -> List[str]:
    """Search for candidate pages containing images related to topic.

    Args:
        topic: Search keyword/phrase
        provider: Search provider (currently only "duckduckgo" supported)
        max_pages: Maximum number of page URLs to return

    Returns:
        List of page URLs that may contain relevant images
    """
    if not topic or not topic.strip():
        logger.warning("search_pages called with empty topic")
        return []

    topic = topic.strip()
    logger.info("search_pages.start topic=%s provider=%s max_pages=%d", topic, provider, max_pages)

    if provider == "duckduckgo":
        # Try images search first (gets source pages directly)
        urls = _search_duckduckgo_images(topic, max_pages)

        # If images search returned few results, supplement with text search
        if len(urls) < max_pages // 2:
            text_urls = _search_duckduckgo(topic, max_pages - len(urls))
            seen = set(urls)
            for u in text_urls:
                if u not in seen:
                    urls.append(u)
                    seen.add(u)
                    if len(urls) >= max_pages:
                        break
    else:
        logger.warning("unsupported provider %s; returning empty", provider)
        urls = []

    logger.info("search_pages.end topic=%s count=%d", topic, len(urls))
    return urls[:max_pages]
