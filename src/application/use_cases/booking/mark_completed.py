import logging
from datetime import date
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class MarkBookingCompletedRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class MarkBookingCompletedUseCase(UseCase[MarkBookingCompletedRequest, None]):
    booking_repo: BookingRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: MarkBookingCompletedRequest) -> None:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.status != BookingStatus.CONFIRMED:
            return

        booking.complete()
        booking.completion_job_id = None
        await self.booking_repo.save(booking)
        await self.transaction_manager.commit()
