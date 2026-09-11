from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository


@dataclass(frozen=True, eq=False)
class GetBookingByIdRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class GetBookingByIdUseCase(UseCase[GetBookingByIdRequest, Booking]):
    booking_repo: BookingRepository

    async def __call__(self, command: GetBookingByIdRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None:
            raise BookingNotFoundException(booking_id=command.booking_id)
        return booking