from __future__ import annotations
"""Relevance scoring for topic-based image discovery.

Calculates a 0.0-1.0 relevance score based on keyword matching in:
- alt text (weight: 0.4)
- filename (weight: 0.3)
- surrounding context text (weight: 0.2)
- domain trust (weight: 0.1)
"""

import re
from typing import Optional, List
from urllib.parse import urlparse

# Weights for each scoring component
WEIGHT_ALT = 0.4
WEIGHT_FILENAME = 0.3
WEIGHT_CONTEXT = 0.2
WEIGHT_DOMAIN = 0.1

# Trusted domains for image content
TRUSTED_DOMAINS = {
    "wikimedia.org",
    "wikipedia.org",
    "pixabay.com",
    "unsplash.com",
    "pexels.com",
    "flickr.com",
    "imgur.com",
}


def _tokenize(text: str) -> List[str]:
    """Split text into lowercase tokens (supports Japanese and alphanumeric)."""
    if not text:
        return []
    # Split on whitespace and punctuation, keep Japanese characters together
    tokens = re.findall(r"[\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", text.lower())
    return [t for t in tokens if len(t) > 1]  # Filter single chars


def _calculate_match_ratio(topic_tokens: List[str], text: str) -> float:
    """Calculate what fraction of topic tokens appear in text."""
    if not topic_tokens or not text:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for token in topic_tokens if token in text_lower)
    return matches / len(topic_tokens)


def _score_domain(domain: Optional[str]) -> float:
    """Return 1.0 for trusted domains, 0.0 otherwise."""
    if not domain:
        return 0.0
    domain_lower = domain.lower()
    for trusted in TRUSTED_DOMAINS:
        if domain_lower == trusted or domain_lower.endswith("." + trusted):
            return 1.0
    return 0.0


def calculate_relevance_score(
    topic: str,
    alt_text: Optional[str] = None,
    filename: Optional[str] = None,
    context_text: Optional[str] = None,
    domain: Optional[str] = None,
) -> float:
    """Calculate relevance score (0.0-1.0) for an image based on topic matching.

    Args:
        topic: Search topic/keyword
        alt_text: Image alt attribute
        filename: Image filename from URL
        context_text: Surrounding text from the page
        domain: Image URL domain

    Returns:
        Score between 0.0 (no relevance) and 1.0 (high relevance)
    """
    if not topic or not topic.strip():
        return 0.0

    topic_tokens = _tokenize(topic)
    if not topic_tokens:
        return 0.0

    # Calculate individual scores
    alt_score = _calculate_match_ratio(topic_tokens, alt_text or "")
    filename_score = _calculate_match_ratio(topic_tokens, filename or "")
    context_score = _calculate_match_ratio(topic_tokens, context_text or "")
    domain_score = _score_domain(domain)

    # Weighted sum
    total = (
        WEIGHT_ALT * alt_score
        + WEIGHT_FILENAME * filename_score
        + WEIGHT_CONTEXT * context_score
        + WEIGHT_DOMAIN * domain_score
    )

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, total))


def extract_filename_from_url(url: str) -> Optional[str]:
    """Extract filename from image URL."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        path = parsed.path
        if "/" in path:
            filename = path.rsplit("/", 1)[-1]
            # Remove query parameters
            if "?" in filename:
                filename = filename.split("?")[0]
            return filename if filename else None
        return None
    except Exception:
        return None


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return parsed.netloc or None
    except Exception:
        return None
