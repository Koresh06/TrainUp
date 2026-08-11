from typing import Protocol

from src.domain.entities.booking import Booking


class BookingRepository(Protocol):
    async def get_all(self) -> list[Booking]:
        ...

    async def get_by_id(self, booking_id: int) -> Booking | None:
        ...

    async def get_upcoming_by_client(self, client_id: int) -> list[Booking]:
        ...

    async def save(self, booking: Booking) -> Booking:
        ...

    async def delete(self, booking_id: int) -> None:
        ...