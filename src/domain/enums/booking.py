from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    # тренировка была, клиент не пришёл — отмечает тренер
    NO_SHOW = "no_show"


# статусы, при которых запись занимает место в слоте
ACTIVE_BOOKING_STATUSES: tuple[BookingStatus, ...] = (
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
)


# статусы прошедших тренировок, которые «состоялись» по времени
PAST_BOOKING_STATUSES: tuple[BookingStatus, ...] = (
    BookingStatus.COMPLETED,
    BookingStatus.NO_SHOW,
)


class BookingActor(str, Enum):
    """Кто совершил действие с записью (например, отменил)."""

    TRAINER = "trainer"
    CLIENT = "client"
    SYSTEM = "system"


class HistoryFilter(str, Enum):
    ALL = "all"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
