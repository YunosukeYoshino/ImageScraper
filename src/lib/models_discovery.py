"""Legacy module - Re-exports from domain.entities for backward compatibility.

New code should import from src.lib.domain.entities instead.
"""

from __future__ import annotations

# Re-export from new location for backward compatibility
from .domain.entities.provenance import (
    DownloadFilter,
    PreviewResult,
    ProvenanceEntry,
    QueryLogEntry,
)

__all__ = [
    "ProvenanceEntry",
    "QueryLogEntry",
    "DownloadFilter",
    "PreviewResult",
]
