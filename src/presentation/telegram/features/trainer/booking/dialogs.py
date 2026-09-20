from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Cancel,
    CurrentPage,
    Group,
    NextPage,
    PrevPage,
    Row,
    Select,
    Button,
    Back,
    ScrollingGroup,
)
from aiogram_dialog.widgets.text import Const, Format, List as ListWidget
from aiogram_dialog.widgets.style import Style

from src.domain.enums.booking import BookingsListMode
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
    on_bookings_mode_selected,
    on_cancel_booking_from_list,
    on_reschedule_click,
    on_reschedule_confirm,
    on_reschedule_date_clicked,
    on_reschedule_time_clicked,
    show_cancel_button,
    show_reschedule_button,
)

list_bookings_dialog = Dialog(
    Window(
        Const("📋 <b>Бронирования</b>\n\nЧто посмотреть?"),
        Button(
            Const("📅 Текущие"),
            id=BookingsListMode.UPCOMING.value,
            on_click=on_bookings_mode_selected,
        ),
        Button(
            Const("🕓 История"),
            id=BookingsListMode.HISTORY.value,
            on_click=on_bookings_mode_selected,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerBookingsSG.mode,
    ),
    Window(
        Format("{title}{empty_hint}"),
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
            when="is_upcoming",
            hide_on_single_page=True,
        ),
        ListWidget(
            Format("{item[label]}"),
            items="bookings",
            id="history_list",
            page_size=8,
            when="is_history",
        ),
        Row(
            PrevPage(scroll="history_list", text=Const("◀️")),
            CurrentPage(
                scroll="history_list",
                text=Format("{current_page1}/{pages}"),
            ),
            NextPage(scroll="history_list", text=Const("▶️")),
            when="is_history",
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerBookingsSG.list,
        getter=bookings_list_getter,
    ),
    Window(
        Format(
            "👤 <b>Клиент:</b> {client_name}\n"
            "{contact_block}\n\n"
            "📅 <b>Дата:</b> {date}\n"
            "🕐 <b>Время:</b> {time}\n"
            "📌 <b>Статус:</b> {status}"
            "{recurring_note}"
        ),
        Button(
            Const("🔁 Перенести"),
            id="reschedule",
            on_click=on_reschedule_click,
            when=show_reschedule_button,
        ),
        Button(
            Const("❌ Отменить"),
            id="cancel_booking",
            on_click=on_cancel_booking_from_list,
            style=Style(style=ButtonStyle.DANGER),
            when=show_cancel_button,
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
