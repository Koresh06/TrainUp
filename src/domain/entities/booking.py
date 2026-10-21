from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingActor, BookingStatus
from src.domain.exception.booking import BookingStatusTransitionException
from src.utils.get_datetime_utc_now import get_datetime_utc_now


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
    cancelled_by: BookingActor | None = None
    cancelled_at: datetime | None = None

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

    def cancel(self, by: BookingActor = BookingActor.TRAINER) -> None:
        if not self.is_active():
            raise BookingStatusTransitionException(
                booking_id=self.id, status=self.status
            )
        self.status = BookingStatus.CANCELLED
        self.cancelled_by = by
        self.cancelled_at = get_datetime_utc_now()
        self.touch()

    def mark_no_show(self) -> None:
        # из COMPLETED тоже можно: автозавершение срабатывает само после
        # тренировки, а тренер отмечает неявку позже
        if self.status not in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED):
            raise BookingStatusTransitionException(
                booking_id=self.id, status=self.status
            )
        self.status = BookingStatus.NO_SHOW
        self.touch()

    def mark_attended(self) -> None:
        """Тренер ошибся с неявкой — возвращаем «проведена»."""
        if self.status != BookingStatus.NO_SHOW:
            raise BookingStatusTransitionException(
                booking_id=self.id, status=self.status
            )
        self.status = BookingStatus.COMPLETED
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
