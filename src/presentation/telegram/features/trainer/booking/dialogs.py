from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Cancel,
    Group,
    Select,
    Button,
    Back,
    ScrollingGroup,
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.style import Style

from src.presentation.telegram.widgets.booking_calendar import BookingCalendar


from .states import TrainerBookingsSG
from .getters import (
    booking_detail_getter,
    bookings_list_getter,
    reschedule_confirm_getter,
    reschedule_day_calendar_getter,
    reschedule_times_getter,
)
from .handlers import (
    is_not_recurring,
    on_booking_selected,
    on_cancel_booking_from_list,
    on_reschedule_click,
    on_reschedule_confirm,
    on_reschedule_date_clicked,
    on_reschedule_time_clicked,
)

list_bookings_dialog = Dialog(
    Window(
        Const(
            "📋 <b>Ближайшие бронирования</b>\n\n"
            "⏳ — ожидает подтверждения\n"
            "✅ — подтверждено\n"
            "🔁 - постоянные тренировки\n\n"
            "Выберите запись:"
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="bookings_select",
                item_id_getter=lambda item: item["id"],
                items="bookings",
                on_click=on_booking_selected,
            ),
            id="bookings_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerBookingsSG.list,
        getter=bookings_list_getter,
    ),
    Window(
        Format(
            "👤 Клиент: {client_name}\n"
            "📅 {date} в {time}\n"
            "Статус: {status}"
            "{recurring_note}"
        ),
        Button(
            Const("🔁 Перенести"),
            id="reschedule",
            on_click=on_reschedule_click,
            when=is_not_recurring,
        ),
        Button(
            Const("❌ Отменить"),
            id="cancel_booking",
            on_click=on_cancel_booking_from_list,
            style=Style(style=ButtonStyle.DANGER),
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerBookingsSG.detail,
        getter=booking_detail_getter,
    ),
    Window(
        Const("Выберите новую дату:"),
        BookingCalendar(
            id="reschedule_calendar",
            on_click=on_reschedule_date_clicked,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerBookingsSG.reschedule_day,
        getter=reschedule_day_calendar_getter,
    ),
    Window(
        Format("Свободное время на {selected_day_label}:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="reschedule_time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_reschedule_time_clicked,
            ),
            width=2,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerBookingsSG.reschedule_time,
        getter=reschedule_times_getter,
    ),
    Window(
        Format("Перенести на:\n\n📅 {date} в {time}\n\nПодтвердить перенос?"),
        Button(
            Const("✅ Подтвердить перенос"),
            id="confirm_reschedule",
            on_click=on_reschedule_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerBookingsSG.reschedule_confirm,
        getter=reschedule_confirm_getter,
    ),
)
