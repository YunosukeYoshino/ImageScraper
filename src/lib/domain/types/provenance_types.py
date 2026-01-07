"""Type definitions for provenance and query logging.

Provides TypedDict definitions for JSON serialization of discovery metadata.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class QueryLogDict(TypedDict):
    """Query log entry for JSON serialization."""

    topic: str
    provider: str
    query: str
    timestamp: str  # ISO format
    page_count: int
    image_count: int
    pages: list[str]


class ProvenanceRecordDict(TypedDict):
    """Provenance record for JSON serialization."""

    filename: str
    image_url: str
    source_page_url: str
    topic: str
    discovery_method: str
    timestamp: NotRequired[str]  # Optional, None if not available
