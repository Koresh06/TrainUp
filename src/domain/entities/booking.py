from dataclasses import dataclass

from src.domain.entities.base import Entity
from src.domain.enums.booking import BookingStatus


@dataclass(kw_only=True)
class Booking(Entity):
    client_id: int
    slot_id: int
    trainer_id: int
    status: BookingStatus

    def confirm(self) -> None:
        self.status = BookingStatus.CONFIRMED
        self.touch()

    def cancel(self) -> None:
        self.status = BookingStatus.CANCELLED
        self.touch()

    def complete(self) -> None:
        self.status = BookingStatus.COMPLETED
        self.touch()
