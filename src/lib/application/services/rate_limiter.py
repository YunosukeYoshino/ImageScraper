from __future__ import annotations

import time
from threading import Lock


class TokenBucket:
    """Simple token bucket rate limiter.

    fill_rate: tokens per second
    capacity: maximum tokens stored
    acquire(n): blocks until n tokens available, then consumes.
    non_blocking_try_acquire(n): returns bool.
    """

    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self._tokens = capacity
        self.fill_rate = fill_rate
        self._last = time.monotonic()
        self._lock = Lock()

    def _refill_locked(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        self._last = now
        added = delta * self.fill_rate
        if added > 0:
            self._tokens = min(self.capacity, self._tokens + added)

    def non_blocking_try_acquire(self, n: int = 1) -> bool:
        with self._lock:
            self._refill_locked()
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def acquire(self, n: int = 1, timeout: float | None = None) -> None:
        """Block until n tokens are available or timeout.

        Args:
            n: tokens to consume
            timeout: optional maximum seconds to wait; raises TimeoutError if exceeded.
        """
        start = time.monotonic()
        while True:
            if self.non_blocking_try_acquire(n):
                return
            if timeout is not None and (time.monotonic() - start) > timeout:
                raise TimeoutError(f"TokenBucket acquire timeout after {timeout}s")
            # Sleep scaled to fill rate; minimum 10ms to avoid busy loop.
            time.sleep(max(0.01, n / max(self.fill_rate, 1e-9) * 0.25))
