"""HTTP infrastructure - Network communication."""
from .http_client import fetch_page, request_with_retry, DEFAULT_HEADERS
from .robots_checker import robots_allowed, RobotsChecker

__all__ = [
    "fetch_page",
    "request_with_retry",
    "DEFAULT_HEADERS",
    "robots_allowed",
    "RobotsChecker",
]
