from aiogram.filters.callback_data import CallbackData


class RateTrainingCD(CallbackData, prefix="rate"):
    booking_id: int
    stars: int
