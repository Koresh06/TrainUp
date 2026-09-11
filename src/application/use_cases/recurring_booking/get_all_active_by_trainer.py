from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest

from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.repositories.recurring_booking import RecurringBookingRepository


@dataclass(frozen=True, eq=False)
class GetActiveRecurringBookingsByTrainerRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetActiveRecurringBookingsByTrainerUseCase(
    UseCase[GetActiveRecurringBookingsByTrainerRequest, list[RecurringBooking]]
):
    recurring_repo: RecurringBookingRepository

    async def __call__(
        self, command: GetActiveRecurringBookingsByTrainerRequest
    ) -> list[RecurringBooking]:
        return await self.recurring_repo.get_active_by_trainer_id(command.trainer_id)
