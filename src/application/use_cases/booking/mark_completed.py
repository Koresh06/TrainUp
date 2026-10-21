import logging
from dataclasses import dataclass
from datetime import timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.services.package_charge import PackageChargeService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import PLAN_NEXT_TRAINING_REMINDER_DAYS
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class MarkBookingCompletedRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class MarkBookingCompletedUseCase(UseCase[MarkBookingCompletedRequest, None]):
    booking_repo: BookingRepository
    booking_scheduler: BookingScheduler
    package_charge: PackageChargeService
    transaction_manager: TransactionManager

    async def __call__(self, command: MarkBookingCompletedRequest) -> None:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.status != BookingStatus.CONFIRMED:
            return

        booking.complete()
        booking.completion_job_id = None
        await self.package_charge.sync(booking)
        await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        await self.booking_scheduler.schedule_plan_next_training_reminder(
            client_id=booking.client_id,
            remind_at_utc=get_datetime_utc_now()
            + timedelta(days=PLAN_NEXT_TRAINING_REMINDER_DAYS),
        )
        logger.info("[MarkBookingCompleted:done] booking_id=%s", booking.id)
