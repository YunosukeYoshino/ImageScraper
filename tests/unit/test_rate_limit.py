import time
import unittest

from src.lib.rate_limit import TokenBucket


class TestTokenBucket(unittest.TestCase):
    def test_non_blocking_try_acquire(self):
        tb = TokenBucket(capacity=2, fill_rate=10)
        self.assertTrue(tb.non_blocking_try_acquire())
        self.assertTrue(tb.non_blocking_try_acquire())
        self.assertFalse(tb.non_blocking_try_acquire())  # empty now

    def test_acquire_blocks_until_refilled(self):
        tb = TokenBucket(capacity=1, fill_rate=2)  # ~0.5s per token
        # consume initial token
        self.assertTrue(tb.non_blocking_try_acquire())
        self.assertFalse(tb.non_blocking_try_acquire())
        t0 = time.monotonic()
        tb.acquire()  # should block until refilled
        dt = time.monotonic() - t0
        # Expect >=0.45s (slightly less than 0.5 due to scheduling) and <1.0s sanity bound
        self.assertGreaterEqual(dt, 0.45, f"Acquire did not block long enough: {dt}")
        self.assertLess(dt, 1.2, f"Acquire blocked too long: {dt}")
        # After acquire, token consumed; next non-blocking should likely fail again until refill
        # Sleep long enough (>0.5s) to allow one token to refill, then consume
        time.sleep(0.55)
        self.assertTrue(tb.non_blocking_try_acquire())


if __name__ == "__main__":
    unittest.main()
