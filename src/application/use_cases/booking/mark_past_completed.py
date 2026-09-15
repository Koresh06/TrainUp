import logging
from datetime import date
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.booking import BookingRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class MarkPastBookingsCompletedRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class MarkPastBookingsCompletedUseCase(UseCase[MarkPastBookingsCompletedRequest, None]):
    booking_repo: BookingRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: MarkPastBookingsCompletedRequest) -> None:
        today = date.today()
        past_bookings = await self.booking_repo.get_past_confirmed(today)

        for booking in past_bookings:
            booking.complete()
            await self.booking_repo.save(booking)

        if past_bookings:
            await self.transaction_manager.commit()

        logger.info("[MarkPastBookingsCompleted:done] marked=%s", len(past_bookings))
