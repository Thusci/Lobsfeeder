from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import NoCapacityError
from app.core.settings import AppConfig
from app.ratelimit.concurrency import ConcurrencyLease, ConcurrencyLimiter
from app.ratelimit.rpm import RPMLimiter, RPMReservation
from app.ratelimit.tpm import TPMReservation, TPMLimiter


@dataclass
class ModelLease:
    model_key: str
    rpm: RPMLimiter
    rpm_reservation: RPMReservation
    concurrency: ConcurrencyLease
    tpm: TPMLimiter
    tpm_reservation: TPMReservation
    global_rpm: RPMLimiter | None = None
    global_rpm_reservation: RPMReservation | None = None
    global_concurrency: ConcurrencyLease | None = None
    finalized: bool = False

    async def finalize(self, actual_tokens: int | None = None) -> None:
        if self.finalized:
            return
        self.finalized = True
        try:
            if self.global_rpm is not None and self.global_rpm_reservation is not None:
                await self.global_rpm.finalize(self.global_rpm_reservation.reservation_id)
            await self.rpm.finalize(self.rpm_reservation.reservation_id)
        finally:
            try:
                await self.tpm.finalize(self.tpm_reservation.reservation_id, actual_tokens)
            finally:
                try:
                    await self.concurrency.release()
                finally:
                    if self.global_concurrency is not None:
                        await self.global_concurrency.release()


class RateLimitManager:
    def __init__(self, config: AppConfig) -> None:
        self._rpm: dict[str, RPMLimiter] = {}
        self._tpm: dict[str, TPMLimiter] = {}
        self._concurrency: dict[str, ConcurrencyLimiter] = {}
        self._global_rpm = (
            RPMLimiter(config.server.global_limits.total_rpm)
            if config.server.global_limits.total_rpm is not None
            else None
        )
        self._global_concurrency = (
            ConcurrencyLimiter(config.server.global_limits.total_concurrency)
            if config.server.global_limits.total_concurrency is not None
            else None
        )

        for model_key, model in config.models.items():
            self._rpm[model_key] = RPMLimiter(model.limits.rpm)
            self._tpm[model_key] = TPMLimiter(model.limits.tpm)
            self._concurrency[model_key] = ConcurrencyLimiter(model.limits.concurrency)

    async def can_accept(self, model_key: str, estimated_tokens: int) -> bool:
        if self._global_rpm is not None and not await self._global_rpm.can_accept():
            return False
        rpm_ok = await self._rpm[model_key].can_accept()
        if not rpm_ok:
            return False
        tpm_ok = await self._tpm[model_key].can_accept(estimated_tokens)
        if not tpm_ok:
            return False
        if self._global_concurrency is not None and not await self._global_concurrency.can_accept():
            return False
        return await self._concurrency[model_key].can_accept()

    async def acquire(self, model_key: str, estimated_tokens: int) -> ModelLease:
        global_rpm_reservation: RPMReservation | None = None
        global_concurrency_lease: ConcurrencyLease | None = None

        if self._global_rpm is not None:
            global_rpm_reservation = await self._global_rpm.reserve()
            if global_rpm_reservation is None:
                raise NoCapacityError("Global RPM exceeded")

        rpm_reservation = await self._rpm[model_key].reserve()
        if rpm_reservation is None:
            if self._global_rpm is not None and global_rpm_reservation is not None:
                await self._global_rpm.release(global_rpm_reservation.reservation_id)
            raise NoCapacityError(f"Model {model_key} exceeded RPM")

        try:
            tpm_reservation = await self._tpm[model_key].reserve(estimated_tokens)
            if tpm_reservation is None:
                raise NoCapacityError(f"Model {model_key} exceeded TPM")

            try:
                if self._global_concurrency is not None:
                    global_concurrency_lease = await self._global_concurrency.try_acquire()
                    if global_concurrency_lease is None:
                        raise NoCapacityError("Global concurrency exceeded")

                concurrency_lease = await self._concurrency[model_key].try_acquire()
                if concurrency_lease is None:
                    raise NoCapacityError(f"Model {model_key} exceeded concurrency")
            except Exception:
                if global_concurrency_lease is not None:
                    await global_concurrency_lease.release()
                await self._tpm[model_key].release(tpm_reservation.reservation_id)
                raise
        except Exception:
            await self._rpm[model_key].release(rpm_reservation.reservation_id)
            if self._global_rpm is not None and global_rpm_reservation is not None:
                await self._global_rpm.release(global_rpm_reservation.reservation_id)
            raise

        return ModelLease(
            model_key=model_key,
            rpm=self._rpm[model_key],
            rpm_reservation=rpm_reservation,
            concurrency=concurrency_lease,
            tpm=self._tpm[model_key],
            tpm_reservation=tpm_reservation,
            global_rpm=self._global_rpm,
            global_rpm_reservation=global_rpm_reservation,
            global_concurrency=global_concurrency_lease,
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

    async def global_snapshot(self) -> dict[str, int | None]:
        return {
            "rpm_in_window": await self._global_rpm.current() if self._global_rpm is not None else None,
            "concurrency": await self._global_concurrency.current() if self._global_concurrency is not None else None,
        }
