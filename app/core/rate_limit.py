"""Simple in-memory rate limiting utilities."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, DefaultDict


class RateLimiter:
    def __init__(self, per_minute: int = 5) -> None:
        self.per_minute = per_minute
        self._hits: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        window_start = time.time() - 60
        bucket = self._hits[key]

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self.per_minute:
            return False

        bucket.append(time.time())
        return True


def get_rate_limiter(app) -> RateLimiter:
    limiter: RateLimiter = getattr(app.state, "rate_limiter", None)
    if limiter is None:
        limiter = RateLimiter()
        app.state.rate_limiter = limiter
    return limiter
