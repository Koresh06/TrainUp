from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class ReminderAction(StrEnum):
    CONFIRM = "confirm"
    CANCEL = "cancel"


class ReminderActionCD(CallbackData, prefix="reminder"):
    action: ReminderAction
    booking_id: int
