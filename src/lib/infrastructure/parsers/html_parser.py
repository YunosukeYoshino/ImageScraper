"""HTML parsing and image extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

IMG_EXT_PATTERN = re.compile(r"\.(?:png|jpe?g|gif|webp|svg)(?:\?.*)?$", re.IGNORECASE)


@dataclass
class ImageMetadata:
    """Metadata extracted from an image element."""

    url: str
    alt: Optional[str] = None
    context: Optional[str] = None


def parse_html(html: str) -> BeautifulSoup:
    """Parse HTML content into BeautifulSoup object."""
    return BeautifulSoup(html, "html.parser")


def _is_image_url(url: str) -> bool:
    """Check if URL points to an image file."""
    return bool(IMG_EXT_PATTERN.search(url)) or url.split("?")[0].lower().endswith(
        tuple([".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"])
    )


def _normalize_url(src: str, base: str) -> str:
    """Normalize relative URLs to absolute."""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    return urljoin(base, src)


def _extract_context_text(img_tag, max_length: int = 200) -> Optional[str]:
    """Extract surrounding text from image's parent elements."""
    try:
        parent = img_tag.parent
        for _ in range(3):
            if parent is None:
                break
            text = parent.get_text(separator=" ", strip=True)
            if text and len(text) > 10:
                return text[:max_length]
            parent = parent.parent
        return None
    except Exception:
        return None


def extract_images(
    html: str,
    base_url: str,
    limit: Optional[int] = None,
    with_metadata: bool = False,
) -> List[ImageMetadata] | List[str]:
    """Extract image URLs from HTML.

    Args:
        html: HTML content
        base_url: Base URL for resolving relative paths
        limit: Maximum number of images to return
        with_metadata: If True, return ImageMetadata objects; otherwise, URLs only

    Returns:
        List of image URLs or ImageMetadata objects
    """
    soup = parse_html(html)
    results: List[ImageMetadata] = []
    seen: set[str] = set()

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src:
            continue

        src_val = src if isinstance(src, str) else str(src)
        full_url = _normalize_url(src_val.strip(), base_url)
        if full_url in seen:
            continue
        seen.add(full_url)

        if not _is_image_url(full_url):
            continue

        if with_metadata:
            alt_attr = img.get("alt", "")
            alt = (alt_attr if isinstance(alt_attr, str) else str(alt_attr)).strip() or None
            context = _extract_context_text(img)
            results.append(ImageMetadata(url=full_url, alt=alt, context=context))
        else:
            results.append(ImageMetadata(url=full_url))

        if limit is not None and len(results) >= limit:
            break

    if with_metadata:
        return results
    return [m.url for m in results]
