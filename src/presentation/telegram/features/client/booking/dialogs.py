from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Select, Button, Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.widgets.booking_calendar import BookingCalendar

from .slot_style import slot_style
from .states import BookingSG
from .handlers import (
    on_date_clicked,
    on_time_clicked,
    on_confirm_booking,
)
from .getters import (
    day_calendar_getter,
    times_getter,
    confirm_booking_getter,
)

booking_dialog = Dialog(
    Window(
        Const("Календарь доступных дат:"),
        BookingCalendar(id="booking_calendar", on_click=on_date_clicked),
        Cancel(Const("⬅️ Назад")),
        state=BookingSG.select_day,
        getter=day_calendar_getter,
    ),
    Window(
        Format("Свободное время на {selected_day_label}:"),
        Select(
            Format("{item[label]}"),
            id="time_select",
            items="times",
            item_id_getter=lambda item: item["value_id"],
            on_click=on_time_clicked,
            style=slot_style,
        ),
        Back(Const("⬅️ Назад")),
        state=BookingSG.select_time,
        getter=times_getter,
    ),
    Window(
        Format(
            "Проверь данные записи:\n\n"
            "📅 {date} в {time}\n\n"
        ),
        Button(
            Const("✅ Подтвердить"),
            id="confirm_booking",
            on_click=on_confirm_booking,
        ),
        Back(Const("⬅️ Назад")),
        state=BookingSG.confirm,
        getter=confirm_booking_getter,
    ),
)

