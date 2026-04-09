from __future__ import annotations

import asyncio
import uuid
from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass
class RPMReservation:
    reservation_id: str


class RPMLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: deque[float] = deque()
        self._pending: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0] < cutoff:
            self._events.popleft()
        stale_pending = [key for key, ts in self._pending.items() if ts < cutoff]
        for key in stale_pending:
            self._pending.pop(key, None)

    def _in_window_total(self) -> int:
        return len(self._events) + len(self._pending)

    async def can_accept(self) -> bool:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            return self._in_window_total() < self.limit

    async def reserve(self) -> RPMReservation | None:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            if self._in_window_total() >= self.limit:
                return None
            reservation_id = uuid.uuid4().hex
            self._pending[reservation_id] = now
            return RPMReservation(reservation_id=reservation_id)

    async def finalize(self, reservation_id: str) -> None:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            reserved_at = self._pending.pop(reservation_id, None)
            if reserved_at is None:
                return
            self._events.append(now)

    async def release(self, reservation_id: str) -> None:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            self._pending.pop(reservation_id, None)

    async def current(self) -> int:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            return self._in_window_total()
