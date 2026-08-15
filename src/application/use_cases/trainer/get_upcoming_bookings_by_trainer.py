from dataclasses import dataclass

from src.domain.entities.booking import Booking
from src.domain.repositories.booking import BookingRepository
from src.application.use_cases.base import UseCase, UseCaseRequest


@dataclass(frozen=True, eq=False)
class GetUpcomingBookingsByTrainerRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetUpcomingBookingsByTrainerUseCase(
    UseCase[GetUpcomingBookingsByTrainerRequest, list[Booking]]
):
    booking_repo: BookingRepository

    async def __call__(
        self, command: GetUpcomingBookingsByTrainerRequest
    ) -> list[Booking]:
        return await self.booking_repo.get_upcoming_by_trainer(command.trainer_id)
