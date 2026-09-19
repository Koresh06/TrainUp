from dataclasses import dataclass
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.booking import BookingStatus


@dataclass(kw_only=True)
class Booking(Entity):
    client_id: int
    trainer_id: int
    slot_id: int
    status: BookingStatus
    price: Decimal | None = None
    reminder_job_id: str | None = None
    recurring_booking_id: int | None = None
    completion_job_id: str | None = None

    def confirm(self) -> None:
        self.status = BookingStatus.CONFIRMED
        self.touch()

    def cancel(self) -> None:
        self.status = BookingStatus.CANCELLED
        self.touch()

    def complete(self) -> None:
        self.status = BookingStatus.COMPLETED
        self.touch()

    def set_reminder_job(self, job_id: str) -> None:
        self.reminder_job_id = job_id

    def clear_reminder_job(self) -> None:
        self.reminder_job_id = None