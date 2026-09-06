from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class BookingAction(StrEnum):
    CONFIRM = "confirm"
    CANCEL = "cancel"


class BookingActionCD(CallbackData, prefix="booking"):
    action: BookingAction
    booking_id: int