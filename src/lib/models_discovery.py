from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import List, Optional

try:
    from pydantic import BaseModel, Field, HttpUrl
except Exception:  # pydantic might be optional in runtime; fallback lightweight typing
    class BaseModel:  # type: ignore
        pass
    def Field(default=None, **kwargs):  # type: ignore
        return default
    HttpUrl = str  # type: ignore


class ProvenanceEntry(BaseModel):
    topic: str = Field(..., description="Original topic keyword")
    source_page_url: HttpUrl = Field(..., description="Page where image url was found")
    image_url: HttpUrl = Field(..., description="Discovered image URL")
    discovery_method: str = Field(..., description="SERP, sitemap, feed, etc.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryLogEntry(BaseModel):
    topic: str
    provider: str
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    page_count: int = 0
    image_count: int = 0


class PreviewResult(BaseModel):
    topic: str
    entries: List[ProvenanceEntry]
    total_images: int
    provider: str
    query_log: QueryLogEntry

    def to_dict(self) -> dict:
        # Pydantic BaseModel has .model_dump(); fallback to manual
        try:
            return self.model_dump()
        except Exception:
            return {
                "topic": self.topic,
                "entries": [e.__dict__ for e in self.entries],
                "total_images": self.total_images,
                "provider": self.provider,
                "query_log": self.query_log.__dict__,
            }
