from aiogram.filters.callback_data import CallbackData


class TrainerDigestCD(CallbackData, prefix="digest"):
    # дата дня из сводки (ISO) — открываем расписание сразу на нём
    day: str
