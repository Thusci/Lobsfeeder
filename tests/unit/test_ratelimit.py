import pytest

from app.ratelimit.concurrency import ConcurrencyLimiter
from app.ratelimit.rpm import RPMLimiter
from app.ratelimit.tpm import TPMLimiter


@pytest.mark.asyncio
async def test_rpm_limiter_blocks_after_limit() -> None:
    limiter = RPMLimiter(limit=2, window_seconds=60)
    assert await limiter.try_acquire() is True
    assert await limiter.try_acquire() is True
    assert await limiter.try_acquire() is False


@pytest.mark.asyncio
async def test_tpm_reserve_and_finalize() -> None:
    limiter = TPMLimiter(limit=10, window_seconds=60)
    reservation = await limiter.reserve(6)
    assert reservation is not None
    assert await limiter.can_accept(5) is False
    await limiter.finalize(reservation.reservation_id, actual_tokens=4)
    assert await limiter.can_accept(5) is True


@pytest.mark.asyncio
async def test_concurrency_release_no_leak() -> None:
    limiter = ConcurrencyLimiter(limit=1)
    lease = await limiter.try_acquire()
    assert lease is not None
    assert await limiter.try_acquire() is None
    await lease.release()
    assert await limiter.try_acquire() is not None
