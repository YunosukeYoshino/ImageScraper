"""Search infrastructure - Search provider implementations."""
from .duckduckgo_search import DuckDuckGoSearch, search_pages

__all__ = [
    "DuckDuckGoSearch",
    "search_pages",
]
