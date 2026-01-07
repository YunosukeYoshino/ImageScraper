"""Type definitions for domain layer.

Clean Architecture principle: Types are part of domain layer and have no external dependencies.
"""

from __future__ import annotations

from src.lib.domain.types.config_types import UIConfig
from src.lib.domain.types.provenance_types import ProvenanceRecordDict, QueryLogDict
from src.lib.domain.types.search_types import (
    DDGImageResult,
    DDGTextResult,
    narrow_image_result_source,
    narrow_text_result_href,
)

__all__ = [
    "DDGTextResult",
    "DDGImageResult",
    "narrow_text_result_href",
    "narrow_image_result_source",
    "UIConfig",
    "QueryLogDict",
    "ProvenanceRecordDict",
]
