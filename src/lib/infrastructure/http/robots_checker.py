"""Robots.txt checking functionality."""
from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib import robotparser

from .http_client import DEFAULT_HEADERS

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Checks robots.txt rules for URLs."""

    def __init__(self, user_agent: str = DEFAULT_HEADERS["User-Agent"]):
        self.user_agent = user_agent
        self._parsers: dict[str, robotparser.RobotFileParser] = {}

    def is_allowed(self, url: str) -> bool:
        """Check if fetching the URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False if disallowed
        """
        try:
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            if base not in self._parsers:
                rp = robotparser.RobotFileParser()
                rp.set_url(f"{base}/robots.txt")
                rp.read()
                self._parsers[base] = rp

            return self._parsers[base].can_fetch(self.user_agent, url)
        except Exception:
            # Fail open if robots.txt is unreachable
            return True


# Default instance for convenience
_default_checker = RobotsChecker()


def robots_allowed(
    target_url: str, user_agent: str = DEFAULT_HEADERS["User-Agent"]
) -> bool:
    """Check if robots.txt allows fetching target_url.

    Public function for checking robots.txt rules.
    Fails open if robots.txt is unreachable.

    Args:
        target_url: URL to check
        user_agent: User agent string

    Returns:
        True if allowed, False if disallowed
    """
    try:
        parsed = urlparse(target_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, target_url)
    except Exception:
        return True
