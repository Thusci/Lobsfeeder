from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class ConcurrencyLease:
    limiter: "ConcurrencyLimiter"
    acquired: bool = True

    async def release(self) -> None:
        if not self.acquired:
            return
        await self.limiter.release()
        self.acquired = False


class ConcurrencyLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._in_flight = 0
        self._lock = asyncio.Lock()

    async def can_accept(self) -> bool:
        async with self._lock:
            return self._in_flight < self.limit

    async def try_acquire(self) -> ConcurrencyLease | None:
        async with self._lock:
            if self._in_flight >= self.limit:
                return None
            self._in_flight += 1
            return ConcurrencyLease(limiter=self)

    async def release(self) -> None:
        async with self._lock:
            if self._in_flight > 0:
                self._in_flight -= 1

    async def current(self) -> int:
        async with self._lock:
            return self._in_flight
