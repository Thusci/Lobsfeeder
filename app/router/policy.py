from __future__ import annotations

from app.core.errors import HealthCircuitOpenError, NoCapacityError, RouterError, UpstreamClientError


def should_fallback(exc: Exception, stream_started: bool = False) -> bool:
    if stream_started:
        return False
    if isinstance(exc, UpstreamClientError) and 400 <= exc.status_code < 500:
        return False
    if isinstance(exc, RouterError):
        return exc.retryable
    return True


def should_count_as_health_failure(exc: Exception) -> bool:
    if isinstance(exc, (NoCapacityError, HealthCircuitOpenError)):
        return False
    if isinstance(exc, UpstreamClientError) and 400 <= exc.status_code < 500:
        return False
    return True
