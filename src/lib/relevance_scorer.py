"""Legacy module - Re-exports from domain.services for backward compatibility.

New code should import from src.lib.domain.services instead.
"""

from __future__ import annotations

# Re-export from new location for backward compatibility
from .domain.services.relevance_scorer import (
    _calculate_match_ratio,
    _score_domain,
    _tokenize,
    calculate_relevance_score,
    extract_domain_from_url,
    extract_filename_from_url,
)

__all__ = [
    "calculate_relevance_score",
    "extract_filename_from_url",
    "extract_domain_from_url",
    "_tokenize",
    "_calculate_match_ratio",
    "_score_domain",
]
