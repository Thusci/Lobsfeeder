from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import NoCapacityError
from app.core.settings import AppConfig
from app.ratelimit.concurrency import ConcurrencyLease, ConcurrencyLimiter
from app.ratelimit.rpm import RPMLimiter
from app.ratelimit.tpm import TPMReservation, TPMLimiter


@dataclass
class ModelLease:
    model_key: str
    concurrency: ConcurrencyLease
    tpm: TPMLimiter
    tpm_reservation: TPMReservation
    finalized: bool = False

    async def finalize(self, actual_tokens: int | None = None) -> None:
        if self.finalized:
            return
        self.finalized = True
        try:
            await self.tpm.finalize(self.tpm_reservation.reservation_id, actual_tokens)
        finally:
            await self.concurrency.release()


class RateLimitManager:
    def __init__(self, config: AppConfig) -> None:
        self._rpm: dict[str, RPMLimiter] = {}
        self._tpm: dict[str, TPMLimiter] = {}
        self._concurrency: dict[str, ConcurrencyLimiter] = {}

        for model_key, model in config.models.items():
            self._rpm[model_key] = RPMLimiter(model.limits.rpm)
            self._tpm[model_key] = TPMLimiter(model.limits.tpm)
            self._concurrency[model_key] = ConcurrencyLimiter(model.limits.concurrency)

    async def can_accept(self, model_key: str, estimated_tokens: int) -> bool:
        rpm_ok = await self._rpm[model_key].can_accept()
        if not rpm_ok:
            return False
        tpm_ok = await self._tpm[model_key].can_accept(estimated_tokens)
        if not tpm_ok:
            return False
        return await self._concurrency[model_key].can_accept()

    async def acquire(self, model_key: str, estimated_tokens: int) -> ModelLease:
        rpm_ok = await self._rpm[model_key].try_acquire()
        if not rpm_ok:
            raise NoCapacityError(f"Model {model_key} exceeded RPM")

        tpm_reservation = await self._tpm[model_key].reserve(estimated_tokens)
        if tpm_reservation is None:
            raise NoCapacityError(f"Model {model_key} exceeded TPM")

        concurrency_lease = await self._concurrency[model_key].try_acquire()
        if concurrency_lease is None:
            raise NoCapacityError(f"Model {model_key} exceeded concurrency")

        return ModelLease(
            model_key=model_key,
            concurrency=concurrency_lease,
            tpm=self._tpm[model_key],
            tpm_reservation=tpm_reservation,
        )

    async def snapshot(self) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        for model_key in self._rpm:
            result[model_key] = {
                "rpm_in_window": await self._rpm[model_key].current(),
                "tpm_in_window": await self._tpm[model_key].current(),
                "concurrency": await self._concurrency[model_key].current(),
            }
        return result
