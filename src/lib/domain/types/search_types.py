"""Type definitions for search API responses.

Provides TypedDict definitions for DuckDuckGo API responses
and narrowing functions for type-safe access to result fields.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class DDGTextResult(TypedDict):
    """DuckDuckGo text search result structure.

    Note: The API returns either 'href' or 'link' depending on version.
    """

    title: str
    href: NotRequired[str]
    link: NotRequired[str]
    body: NotRequired[str]


class DDGImageResult(TypedDict):
    """DuckDuckGo image search result structure.

    Note: 'source' is the page URL, 'image' is the direct image URL.
    """

    title: str
    image: str
    source: NotRequired[str]
    url: NotRequired[str]
    thumbnail: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]


def narrow_text_result_href(result: dict[str, object] | object) -> str:
    """Extract href from DuckDuckGo text result with type narrowing.

    Handles both 'href' (new API) and 'link' (legacy API) keys.

    Args:
        result: Raw result from ddgs.text(), typed as object for safety

    Returns:
        URL string if found, empty string otherwise
    """
    if not isinstance(result, dict):
        return ""
    # ty cannot narrow dict[str, object] | object -> dict[str, object] correctly
    # ddgs library returns untyped dicts, so we suppress the type error
    href = result.get("href")  # ty: ignore[invalid-argument-type]
    if isinstance(href, str) and href:
        return href
    link = result.get("link")  # ty: ignore[invalid-argument-type]
    if isinstance(link, str) and link:
        return link
    return ""


def narrow_image_result_source(result: dict[str, object] | object) -> str:
    """Extract source page URL from DuckDuckGo image result with type narrowing.

    Handles both 'source' (preferred) and 'url' (fallback) keys.

    Args:
        result: Raw result from ddgs.images(), typed as object for safety

    Returns:
        URL string if found, empty string otherwise
    """
    if not isinstance(result, dict):
        return ""
    # ty cannot narrow dict[str, object] | object -> dict[str, object] correctly
    # ddgs library returns untyped dicts, so we suppress the type error
    source = result.get("source")  # ty: ignore[invalid-argument-type]
    if isinstance(source, str) and source:
        return source
    url = result.get("url")  # ty: ignore[invalid-argument-type]
    if isinstance(url, str) and url:
        return url
    return ""
