from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# статусы, при которых запись занимает место в слоте
ACTIVE_BOOKING_STATUSES: tuple[BookingStatus, ...] = (
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
)


class BookingsListMode(str, Enum):
    UPCOMING = "upcoming"
    HISTORY = "history"
