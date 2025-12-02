from __future__ import annotations
"""Search provider adapter (minimal SERP simulation for MVP).

In real implementation this would perform network calls to a search engine
or use an API. For testability we keep logic injectable/mocked.
"""

from typing import List

# For MVP we return fixed mock pages (these would be replaced by real results)
MOCK_PAGES = [
    "https://example.com/",
]


def search_pages(topic: str, provider: str = "duckduckgo", max_pages: int = 20) -> List[str]:
    # Placeholder: return the first page only (limit by max_pages)
    return MOCK_PAGES[: max_pages]
