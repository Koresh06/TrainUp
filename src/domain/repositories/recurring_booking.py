from typing import Protocol

from src.domain.entities.recurring_booking import RecurringBooking


class RecurringBookingRepository(Protocol):
    async def get_by_id(self, recurring_booking_id: int) -> RecurringBooking | None: ...

    async def get_active_by_trainer_id(
        self, trainer_id: int
    ) -> list[RecurringBooking]: ...

    async def get_all_active(self) -> list[RecurringBooking]: ...

    async def save(self, recurring: RecurringBooking) -> RecurringBooking: ...
