from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.repositories.booking import BookingRepository


@dataclass(frozen=True, eq=False)
class GetBookingsHistoryByTrainerRequest(UseCaseRequest):
    trainer_id: int
    limit: int = 50


@dataclass(kw_only=True)
class GetBookingsHistoryByTrainerUseCase(
    UseCase[GetBookingsHistoryByTrainerRequest, list[Booking]]
):
    booking_repo: BookingRepository

    async def __call__(self, command: GetBookingsHistoryByTrainerRequest) -> list[Booking]:
        return await self.booking_repo.get_history_by_trainer(
            command.trainer_id, command.limit
        )