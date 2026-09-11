from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest

from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.exception.recurring_booking import RecurringBookingNotFoundException
from src.domain.repositories.recurring_booking import RecurringBookingRepository


@dataclass(frozen=True, eq=False)
class GetRecurringBookingByIdRequest(UseCaseRequest):
    recurring_booking_id: int


@dataclass(kw_only=True)
class GetRecurringBookingByIdUseCase(
    UseCase[GetRecurringBookingByIdRequest, RecurringBooking]
):
    recurring_repo: RecurringBookingRepository

    async def __call__(
        self, command: GetRecurringBookingByIdRequest
    ) -> RecurringBooking:
        recurring = await self.recurring_repo.get_by_id(command.recurring_booking_id)
        if recurring is None:
            raise RecurringBookingNotFoundException(command.recurring_booking_id)
        return recurring
