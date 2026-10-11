from dataclasses import dataclass
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingStatus
from src.domain.exception.booking import BookingStatusTransitionException


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

    def is_active(self) -> bool:
        return self.status in ACTIVE_BOOKING_STATUSES

    def confirm(self) -> None:
        # подтвердить можно только ожидающую запись — иначе повторное нажатие
        # «Подтвердить» в группе «воскрешает» уже отменённую бронь
        if self.status != BookingStatus.PENDING:
            raise BookingStatusTransitionException(
                booking_id=self.id, status=self.status
            )
        self.status = BookingStatus.CONFIRMED
        self.touch()

    def cancel(self) -> None:
        if not self.is_active():
            raise BookingStatusTransitionException(
                booking_id=self.id, status=self.status
            )
        self.status = BookingStatus.CANCELLED
        self.touch()

    def complete(self) -> None:
        if self.status != BookingStatus.CONFIRMED:
            raise BookingStatusTransitionException(
                booking_id=self.id, status=self.status
            )
        self.status = BookingStatus.COMPLETED
        self.touch()

    def set_reminder_job(self, job_id: str) -> None:
        self.reminder_job_id = job_id

    def clear_reminder_job(self) -> None:
        self.reminder_job_id = None
