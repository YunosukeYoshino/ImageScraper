"""Provenance and discovery entities.

Core domain models for image discovery and provenance tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ProvenanceEntry(BaseModel):
    """Record of image discovery provenance."""

    topic: str = Field(..., description="Original topic keyword")
    source_page_url: HttpUrl = Field(..., description="Page where image url was found")
    image_url: HttpUrl = Field(..., description="Discovered image URL")
    discovery_method: str = Field(..., description="SERP, sitemap, feed, etc.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Relevance scoring fields
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score 0.0-1.0")
    alt_text: Optional[str] = Field(default=None, description="Image alt attribute")
    filename: Optional[str] = Field(default=None, description="Image filename from URL")
    context_text: Optional[str] = Field(default=None, description="Surrounding text (max 200 chars)")

    def get_relevance_label(self) -> str:
        """Return human-readable relevance label."""
        if self.relevance_score >= 0.6:
            return "高"
        elif self.relevance_score >= 0.3:
            return "中"
        return "低"


class QueryLogEntry(BaseModel):
    """Log entry for a discovery query."""

    topic: str
    provider: str
    query: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    page_count: int = 0
    image_count: int = 0


class DownloadFilter(BaseModel):
    """Filter settings for selective download."""

    min_width: Optional[int] = Field(default=None, description="Minimum image width in pixels")
    min_height: Optional[int] = Field(default=None, description="Minimum image height in pixels")
    allow_domains: Optional[List[str]] = Field(
        default=None, description="Whitelist domains (if set, only these allowed)"
    )
    deny_domains: Optional[List[str]] = Field(default=None, description="Blacklist domains (excluded)")


class PreviewResult(BaseModel):
    """Result of a discovery preview operation."""

    topic: str
    entries: List[ProvenanceEntry]
    total_images: int
    provider: str
    query_log: QueryLogEntry

    def to_dict(self) -> dict:
        """Convert to dictionary using Pydantic's model_dump method."""
        return self.model_dump()
