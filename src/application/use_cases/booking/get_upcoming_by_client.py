from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.repositories.booking import BookingRepository


@dataclass(frozen=True, eq=False)
class GetUpcomingBookingsByClientRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class GetUpcomingBookingsByClientUseCase(
    UseCase[GetUpcomingBookingsByClientRequest, list[Booking]]
):
    booking_repo: BookingRepository

    async def __call__(self, command: GetUpcomingBookingsByClientRequest) -> list[Booking]:
        return await self.booking_repo.get_upcoming_by_client(command.client_id)
