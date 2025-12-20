"""HTTP client for fetching web pages."""
from __future__ import annotations

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ImageScraper/1.0; +https://github.com/example)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def request_with_retry(
    url: str,
    retries: int = 3,
    backoff: float = 1.2,
    headers: Optional[dict] = None,
) -> requests.Response:
    """Fetch URL with retry logic.

    Args:
        url: URL to fetch
        retries: Number of retry attempts
        backoff: Backoff multiplier between retries
        headers: Optional custom headers

    Returns:
        Response object

    Raises:
        RuntimeError: If all retries fail
    """
    last_exc: Optional[Exception] = None
    request_headers = headers or DEFAULT_HEADERS

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=request_headers, timeout=15)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_exc}")


def fetch_page(url: str, headers: Optional[dict] = None) -> str:
    """Fetch HTML content from a URL.

    Args:
        url: URL to fetch
        headers: Optional custom headers

    Returns:
        HTML content as string
    """
    response = request_with_retry(url, headers=headers)
    return response.text
