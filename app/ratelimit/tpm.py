from __future__ import annotations

import asyncio
import uuid
from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass
class TPMReservation:
    reservation_id: str
    reserved_tokens: int


class TPMLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: deque[tuple[float, int]] = deque()
        self._pending: dict[str, tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

        stale_pending = [key for key, (ts, _) in self._pending.items() if ts < cutoff]
        for key in stale_pending:
            self._pending.pop(key, None)

    def _in_window_total(self) -> int:
        used = sum(tokens for _, tokens in self._events)
        reserved = sum(tokens for _, tokens in self._pending.values())
        return used + reserved

    async def can_accept(self, estimated_tokens: int) -> bool:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            return self._in_window_total() + max(estimated_tokens, 1) <= self.limit

    async def reserve(self, estimated_tokens: int) -> TPMReservation | None:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            reserve_tokens = max(estimated_tokens, 1)
            if self._in_window_total() + reserve_tokens > self.limit:
                return None
            reservation_id = uuid.uuid4().hex
            self._pending[reservation_id] = (now, reserve_tokens)
            return TPMReservation(reservation_id=reservation_id, reserved_tokens=reserve_tokens)

    async def finalize(self, reservation_id: str, actual_tokens: int | None) -> None:
        async with self._lock:
            now = monotonic()
            self._cleanup(now)
            pending = self._pending.pop(reservation_id, None)
            if pending is None:
                return
            _, reserved_tokens = pending
            settled_tokens = max(actual_tokens or reserved_tokens, 1)
            self._events.append((now, settled_tokens))

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
