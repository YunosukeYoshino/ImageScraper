"""Search repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class SearchRepository(ABC):
    """Abstract interface for search providers.

    Implementations must provide search functionality for discovering
    pages related to a given topic.
    """

    @abstractmethod
    def search_pages(self, topic: str, max_pages: int = 20) -> List[str]:
        """Search for pages related to the topic.

        Args:
            topic: Search keyword/phrase
            max_pages: Maximum number of page URLs to return

        Returns:
            List of page URLs that may contain relevant images
        """
        pass

    @abstractmethod
    def search_images(self, topic: str, max_results: int = 50) -> List[str]:
        """Search for images directly related to the topic.

        Args:
            topic: Search keyword/phrase
            max_results: Maximum number of image URLs to return

        Returns:
            List of image source page URLs
        """
        pass
