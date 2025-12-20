"""Legacy module - Re-exports from domain.services for backward compatibility.

New code should import from src.lib.domain.services instead.
"""
from __future__ import annotations

# Re-export from new location for backward compatibility
from .domain.services.relevance_scorer import (
    calculate_relevance_score,
    extract_filename_from_url,
    extract_domain_from_url,
    _tokenize,
    _calculate_match_ratio,
    _score_domain,
    WEIGHT_ALT,
    WEIGHT_FILENAME,
    WEIGHT_CONTEXT,
    WEIGHT_DOMAIN,
    TRUSTED_DOMAINS,
)

__all__ = [
    "calculate_relevance_score",
    "extract_filename_from_url",
    "extract_domain_from_url",
    "_tokenize",
    "_calculate_match_ratio",
    "_score_domain",
]
