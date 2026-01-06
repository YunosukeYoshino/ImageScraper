"""HTTP infrastructure - Network communication."""

from .http_client import DEFAULT_HEADERS, fetch_page, request_with_retry
from .robots_checker import RobotsChecker, robots_allowed

__all__ = [
    "fetch_page",
    "request_with_retry",
    "DEFAULT_HEADERS",
    "robots_allowed",
    "RobotsChecker",
]
