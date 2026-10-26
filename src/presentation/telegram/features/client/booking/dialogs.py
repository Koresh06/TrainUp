from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Select, Button, Cancel, Group
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.widgets.booking_calendar import BookingCalendar
from src.presentation.telegram.features.slot_style import slot_style

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
        Const("📅 <b>Выберите дату тренировки</b>\n\n<i>Синим выделены доступные дни</i>"),
        BookingCalendar(id="booking_calendar", on_click=on_date_clicked),
        Cancel(Const("⬅️ Назад")),
        state=BookingSG.select_day,
        getter=day_calendar_getter,
    ),
    Window(
        Format("🕐 <b>Свободное время</b> — {selected_day_label}{header_note}"),
        Group(
            Select(
                Format("{item[label]}"),
                id="time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_time_clicked,
                style=slot_style,
            ),
            width=2,
        ),
        Back(Const("⬅️ Назад")),
        state=BookingSG.select_time,
        getter=times_getter,
    ),
    Window(
        Format(
            "✅ <b>Проверьте запись</b>\n\n"
            "📅 <b>{date}</b>  ·  🕐 <b>{time}</b>{price_label}\n\n"
            "<i>После подтверждения тренер получит уведомление.</i>"
        ),
        Button(
            Const("✅ Записаться!"),
            id="confirm_booking",
            on_click=on_confirm_booking,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=BookingSG.confirm,
        getter=confirm_booking_getter,
    ),
)
