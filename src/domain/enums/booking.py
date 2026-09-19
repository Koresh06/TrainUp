from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingsListMode(str, Enum):
    UPCOMING = "upcoming"
    HISTORY = "history"