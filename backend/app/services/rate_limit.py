"""Simple in-memory per-key rate limiting service."""

import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window rate limiter."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, per_seconds: int) -> bool:
        now = time.time()
        window_start = now - per_seconds
        events = self._events[key]
        while events and events[0] < window_start:
            events.popleft()
        if len(events) >= limit:
            return False
        events.append(now)
        return True


rate_limiter = RateLimiter()
