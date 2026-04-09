from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RouterError(Exception):
    message: str
    status_code: int = 500
    error_type: str = "server_error"
    code: str = "internal_error"
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


class ValidationError(RouterError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_type="invalid_request_error",
            code="validation_error",
            retryable=False,
        )


class EvaluatorError(RouterError):
    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_type="upstream_error",
            code="evaluator_error",
            retryable=retryable,
        )


class RoutingError(RouterError):
    def __init__(self, message: str, status_code: int = 503, code: str = "routing_error") -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_type="server_error",
            code=code,
            retryable=False,
        )


class NoCapacityError(RouterError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=429,
            error_type="rate_limit_error",
            code="no_capacity",
            retryable=True,
        )


class UpstreamTimeoutError(RouterError):
    def __init__(self, message: str = "Upstream timeout") -> None:
        super().__init__(
            message=message,
            status_code=504,
            error_type="upstream_error",
            code="upstream_timeout",
            retryable=True,
        )


class UpstreamRateLimitError(RouterError):
    def __init__(self, message: str = "Upstream rate limited") -> None:
        super().__init__(
            message=message,
            status_code=429,
            error_type="rate_limit_error",
            code="upstream_rate_limited",
            retryable=True,
        )


class UpstreamServerError(RouterError):
    def __init__(self, message: str = "Upstream server error") -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_type="upstream_error",
            code="upstream_server_error",
            retryable=True,
        )


class UpstreamClientError(RouterError):
    def __init__(self, message: str, status_code: int = 400, retryable: bool = False) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_type="invalid_request_error",
            code="upstream_client_error",
            retryable=retryable,
        )


class UpstreamAuthError(RouterError):
    def __init__(self, message: str = "Upstream authentication error") -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_type="upstream_error",
            code="upstream_auth_error",
            retryable=True,
        )


class ParseError(RouterError):
    def __init__(self, message: str = "Failed to parse upstream response") -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_type="upstream_error",
            code="parse_error",
            retryable=True,
        )


class HealthCircuitOpenError(RouterError):
    def __init__(self, message: str = "Model is unhealthy") -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_type="server_error",
            code="health_circuit_open",
            retryable=True,
        )
