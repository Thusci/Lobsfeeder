from __future__ import annotations

import asyncio
from collections import deque
from time import monotonic


class RPMLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: deque[float] = deque()
        self._lock = asyncio.Lock()

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0] < cutoff:
            self._events.popleft()

    async def can_accept(self) -> bool:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            return len(self._events) < self.limit

    async def try_acquire(self) -> bool:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            if len(self._events) >= self.limit:
                return False
            self._events.append(now)
            return True

    async def current(self) -> int:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            return len(self._events)
