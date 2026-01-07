"""DuckDuckGo search provider implementation."""

from __future__ import annotations

import logging
import time
import warnings
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from src.lib.domain.repositories.search_repository import SearchRepository
from src.lib.domain.types import narrow_image_result_source, narrow_text_result_href

logger = logging.getLogger(__name__)

# Optional import for ddgs
# DDGS is an optional dependency - type is Any when unavailable
_HAS_DDGS = False
DDGS: type[Any] | None = None

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed.*ddgs.*")
    try:
        from ddgs import DDGS as _DDGS

        DDGS = _DDGS
        _HAS_DDGS = True
    except ImportError:
        try:
            from duckduckgo_search import DDGS as _DDGS  # ty: ignore[unresolved-import]

            DDGS = _DDGS
            _HAS_DDGS = True
        except ImportError:
            pass


# Rate limiter singleton
_rate_limiter: Optional[Callable[[], None]] = None


def set_rate_limiter(limiter: Optional[Callable[[], None]]) -> None:
    """Set global rate limiter."""
    global _rate_limiter
    _rate_limiter = limiter


def _wait_rate_limit() -> None:
    """Apply rate limiting if configured."""
    if _rate_limiter is not None:
        _rate_limiter()


def _is_valid_url(url: str) -> bool:
    """Check if a URL is valid."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _search_with_retry(func, topic: str, max_retries: int = 3, base_delay: float = 2.0):
    """Execute search with exponential backoff on rate limit errors."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "ratelimit" in err_str or "202" in err_str or "rate" in err_str:
                delay = base_delay * (2**attempt)
                logger.info("Rate limited, retrying in %.1fs (attempt %d/%d)", delay, attempt + 1, max_retries)
                time.sleep(delay)
            else:
                raise
    if last_error:
        raise last_error
    return None


class DuckDuckGoSearch(SearchRepository):
    """DuckDuckGo search implementation."""

    def search_pages(self, topic: str, max_pages: int = 20) -> list[str]:
        """Search for pages related to the topic."""
        if not _HAS_DDGS:
            logger.warning("ddgs not installed; returning empty results")
            return []

        urls: list[str] = []

        def _do_search():
            nonlocal urls
            _wait_rate_limit()
            assert DDGS is not None  # Guaranteed by _HAS_DDGS check
            with DDGS() as ddgs:
                query = f"{topic} images"
                results = list(ddgs.text(query, max_results=max_pages * 2))
                for r in results:
                    if len(urls) >= max_pages:
                        break
                    href = narrow_text_result_href(r)
                    if _is_valid_url(href):
                        urls.append(href)
            return urls

        try:
            _search_with_retry(_do_search, topic)
            logger.info("duckduckgo.search topic=%s found=%d", topic, len(urls))
        except Exception as e:
            logger.warning("duckduckgo.search failed topic=%s err=%s", topic, e)

        return urls

    def search_images(self, topic: str, max_results: int = 50) -> list[str]:
        """Search for image source pages."""
        if not _HAS_DDGS:
            logger.warning("ddgs not installed; returning empty results")
            return []

        source_pages: set[str] = set()

        def _do_search():
            nonlocal source_pages
            _wait_rate_limit()
            assert DDGS is not None  # Guaranteed by _HAS_DDGS check
            with DDGS() as ddgs:
                results = list(ddgs.images(topic, max_results=max_results * 5))
                for r in results:
                    if len(source_pages) >= max_results:
                        break
                    page_url = narrow_image_result_source(r)
                    if _is_valid_url(page_url) and page_url not in source_pages:
                        source_pages.add(page_url)
            return source_pages

        try:
            _search_with_retry(_do_search, topic)
            logger.info("duckduckgo.images topic=%s source_pages=%d", topic, len(source_pages))
        except Exception as e:
            logger.warning("duckduckgo.images failed topic=%s err=%s", topic, e)

        return list(source_pages)[:max_results]


# Convenience function for backward compatibility
def search_pages(topic: str, provider: str = "duckduckgo", max_pages: int = 20) -> list[str]:
    """Search for candidate pages containing images."""
    if not topic or not topic.strip():
        logger.warning("search_pages called with empty topic")
        return []

    topic = topic.strip()
    logger.info("search_pages.start topic=%s provider=%s max_pages=%d", topic, provider, max_pages)

    if provider == "duckduckgo":
        search = DuckDuckGoSearch()
        urls = search.search_images(topic, max_pages)
        if len(urls) < max_pages // 2:
            text_urls = search.search_pages(topic, max_pages - len(urls))
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
