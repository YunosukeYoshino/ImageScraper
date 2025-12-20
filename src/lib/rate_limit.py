"""Legacy module - Re-exports from application.services for backward compatibility.

New code should import from src.lib.application.services instead.
"""
from __future__ import annotations

# Re-export from new location for backward compatibility
from .application.services.rate_limiter import TokenBucket

__all__ = ["TokenBucket"]
