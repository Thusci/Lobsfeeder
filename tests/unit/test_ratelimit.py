import pytest

from app.core.errors import NoCapacityError
from app.core.settings import AppConfig
from app.ratelimit.concurrency import ConcurrencyLimiter
from app.ratelimit.manager import RateLimitManager
from app.ratelimit.rpm import RPMLimiter
from app.ratelimit.tpm import TPMLimiter


@pytest.mark.asyncio
async def test_rpm_limiter_blocks_after_limit() -> None:
    limiter = RPMLimiter(limit=2, window_seconds=60)
    first = await limiter.reserve()
    second = await limiter.reserve()
    third = await limiter.reserve()
    assert first is not None
    assert second is not None
    assert third is None

    await limiter.finalize(first.reservation_id)
    await limiter.finalize(second.reservation_id)


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


@pytest.mark.asyncio
async def test_rate_limit_manager_releases_partial_reservations(config_data: dict) -> None:
    config_data["models"]["model_b"]["limits"]["concurrency"] = 1
    config = AppConfig.model_validate(config_data)
    manager = RateLimitManager(config)

    first_lease = await manager.acquire("model_b", estimated_tokens=10)
    snapshot = await manager.snapshot()
    assert snapshot["model_b"]["rpm_in_window"] == 1
    assert snapshot["model_b"]["tpm_in_window"] == 10

    with pytest.raises(NoCapacityError):
        await manager.acquire("model_b", estimated_tokens=10)

    snapshot = await manager.snapshot()
    assert snapshot["model_b"]["rpm_in_window"] == 1
    assert snapshot["model_b"]["tpm_in_window"] == 10

    await first_lease.finalize(actual_tokens=10)


@pytest.mark.asyncio
async def test_rate_limit_manager_respects_global_limits(config_data: dict) -> None:
    config_data["server"]["global_limits"] = {"total_rpm": 1, "total_concurrency": 1}
    config = AppConfig.model_validate(config_data)
    manager = RateLimitManager(config)

    lease = await manager.acquire("model_b", estimated_tokens=10)

    with pytest.raises(NoCapacityError):
        await manager.acquire("model_c", estimated_tokens=10)

    snapshot = await manager.global_snapshot()
    assert snapshot["rpm_in_window"] == 1
    assert snapshot["concurrency"] == 1

    await lease.finalize(actual_tokens=10)
