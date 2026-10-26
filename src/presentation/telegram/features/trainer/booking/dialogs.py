from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Group,
    Row,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.widgets.booking_calendar import (
    BookingCalendar,
    ScheduleCalendar,
)

from .getters import (
    add_client_getter,
    add_confirm_getter,
    add_time_getter,
    booking_detail_getter,
    cancel_confirm_getter,
    day_getter,
    history_getter,
    pending_getter,
    pick_date_getter,
    reschedule_confirm_getter,
    reschedule_day_calendar_getter,
    reschedule_times_getter,
    week_getter,
)
from .handlers import (
    on_add_client_selected,
    on_add_confirm,
    on_add_time_selected,
    on_attended,
    on_booking_selected,
    on_cancel_confirmed,
    on_confirm_booking,
    on_date_picked,
    on_detail_back,
    on_history_filter,
    on_mark_paid,
    on_next_day,
    on_next_month,
    on_next_week,
    on_no_show,
    on_open_client_card,
    on_open_week,
    on_prev_day,
    on_prev_month,
    on_prev_week,
    on_reschedule_confirm,
    on_reschedule_date_clicked,
    on_reschedule_time_clicked,
    on_schedule_start,
    on_today,
    on_week_day_selected,
)
from .states import TrainerBookingsSG


def _bookings_select(widget_id: str) -> Select:
    return Select(
        Format("{item[label]}"),
        id=widget_id,
        item_id_getter=lambda item: item["id"],
        items="bookings",
        on_click=on_booking_selected,
    )


to_day = SwitchTo(Const("⬅️ К расписанию"), id="to_day", state=TrainerBookingsSG.day)

list_bookings_dialog = Dialog(
    Window(
        Format("📅 <b>{title}</b>\n{summary}{body}"),
        Group(_bookings_select("day_bookings"), width=1),
        Row(
            Button(Format("{prev_label}"), id="prev_day", on_click=on_prev_day),
            Button(Const("Сегодня"), id="today", on_click=on_today, when="not_today"),
            Button(Format("{next_label}"), id="next_day", on_click=on_next_day),
        ),
        Row(
            SwitchTo(Const("📆 Дата"), id="pick_date", state=TrainerBookingsSG.pick_date),
            Button(Const("🗓 Неделя"), id="week", on_click=on_open_week),
        ),
        SwitchTo(
            Format("⏳ Ждут подтверждения ({pending_count})"),
            id="pending",
            state=TrainerBookingsSG.pending,
            when="has_pending",
        ),
        SwitchTo(
            Const("➕ Записать клиента"),
            id="add",
            state=TrainerBookingsSG.add_client,
            when="can_add",
        ),
        SwitchTo(Const("🕓 История"), id="history", state=TrainerBookingsSG.history),
        Cancel(Const("⬅️ В кабинет")),
        state=TrainerBookingsSG.day,
        getter=day_getter,
    ),
    Window(
        Format("🗓 <b>Неделя {title}</b>\n{summary}\n\n{body}"),
        Group(
            Select(
                Format("{item[label]}"),
                id="week_days",
                item_id_getter=lambda item: item["id"],
                items="days",
                on_click=on_week_day_selected,
            ),
            width=4,
        ),
        Row(
            Button(Const("◀️ Пред."), id="prev_week", on_click=on_prev_week),
            Button(Const("След. ▶️"), id="next_week", on_click=on_next_week),
        ),
        to_day,
        state=TrainerBookingsSG.week,
        getter=week_getter,
    ),
    Window(
        Const("📆 Выберите день\n<i>синим — дни с тренировками</i>"),
        ScheduleCalendar(id="schedule_calendar", on_click=on_date_picked),
        to_day,
        state=TrainerBookingsSG.pick_date,
        getter=pick_date_getter,
    ),
    Window(
        Format("⏳ <b>Ждут подтверждения</b>{empty_hint}"),
        ScrollingGroup(
            _bookings_select("pending_bookings"),
            id="pending_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        to_day,
        state=TrainerBookingsSG.pending,
        getter=pending_getter,
    ),
    Window(
        Format("🕓 <b>История · {title}</b>\n{stats}{empty_hint}"),
        Group(
            Select(
                Format("{item[label]}"),
                id="history_filter",
                item_id_getter=lambda item: item["id"],
                items="filters",
                on_click=on_history_filter,
            ),
            width=2,
        ),
        ScrollingGroup(
            _bookings_select("history_bookings"),
            id="history_scroll",
            width=2,
            height=8,
            hide_on_single_page=True,
        ),
        Row(
            Button(Format("{prev_label}"), id="prev_month", on_click=on_prev_month),
            Button(Format("{next_label}"), id="next_month", on_click=on_next_month, when="has_next"),
        ),
        to_day,
        state=TrainerBookingsSG.history,
        getter=history_getter,
    ),
    Window(
        Format("{card}"),
        Button(
            Const("✅ Подтвердить"),
            id="confirm",
            on_click=on_confirm_booking,
            style=Style(style=ButtonStyle.SUCCESS),
            when="is_pending",
        ),
        Row(
            SwitchTo(
                Const("🔁 Перенести"),
                id="reschedule",
                state=TrainerBookingsSG.reschedule_day,
                when="can_change",
            ),
            SwitchTo(
                Const("❌ Отменить"),
                id="cancel",
                state=TrainerBookingsSG.cancel_confirm,
                when="can_change",
            ),
        ),
        Button(Const("🚫 Не пришёл"), id="no_show", on_click=on_no_show, when="can_no_show"),
        Button(Const("↩️ Всё же пришёл"), id="attended", on_click=on_attended, when="can_attended"),
        Button(Const("💵 Отметить оплату"), id="mark_paid", on_click=on_mark_paid, when="can_mark_paid"),
        Button(Const("👤 Карточка клиента"), id="client_card", on_click=on_open_client_card),
        Button(Const("⬅️ Назад"), id="detail_back", on_click=on_detail_back),
        LinkPreview(is_disabled=True),
        state=TrainerBookingsSG.detail,
        getter=booking_detail_getter,
    ),
    Window(
        Format(
            "❌ <b>Отменить тренировку?</b>\n\n"
            "👤 {client_name}\n"
            "📅 {when}"
            "{recurring_hint}\n\n"
            "{notify_hint}"
        ),
        Button(
            Const("❌ Да, отменить"),
            id="cancel_yes",
            on_click=on_cancel_confirmed,
            style=Style(style=ButtonStyle.DANGER),
        ),
        SwitchTo(Const("↩️ Нет, оставить"), id="cancel_no", state=TrainerBookingsSG.detail),
        state=TrainerBookingsSG.cancel_confirm,
        getter=cancel_confirm_getter,
    ),
    Window(
        Const("🔁 Выберите новую дату:"),
        BookingCalendar(id="reschedule_calendar", on_click=on_reschedule_date_clicked),
        SwitchTo(Const("⬅️ Назад"), id="back_to_detail", state=TrainerBookingsSG.detail),
        state=TrainerBookingsSG.reschedule_day,
        getter=reschedule_day_calendar_getter,
    ),
    Window(
        Format("🕐 Свободное время на {selected_day_label}:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="reschedule_time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_reschedule_time_clicked,
            ),
            width=3,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_rs_day", state=TrainerBookingsSG.reschedule_day),
        state=TrainerBookingsSG.reschedule_time,
        getter=reschedule_times_getter,
    ),
    Window(
        Format(
            "🔁 <b>Перенос тренировки</b>\n\n"
            "Новое время: 📅 <b>{date}</b>  ·  🕐 <b>{time}</b>\n\n"
            "Подтвердить перенос?"
        ),
        Button(
            Const("✅ Подтвердить перенос"),
            id="confirm_reschedule",
            on_click=on_reschedule_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_rs_time", state=TrainerBookingsSG.reschedule_time),
        state=TrainerBookingsSG.reschedule_confirm,
        getter=reschedule_confirm_getter,
    ),
    Window(
        Format("➕ <b>Записать клиента</b> на {day_label}\n\nВыберите клиента:{empty_hint}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="add_client_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_add_client_selected,
            ),
            id="add_client_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        to_day,
        state=TrainerBookingsSG.add_client,
        getter=add_client_getter,
    ),
    Window(
        Format("🕐 Свободное время на {day_label}:{empty_hint}"),
        Group(
            Select(
                Format("{item[label]}"),
                id="add_time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_add_time_selected,
            ),
            width=3,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_add_client", state=TrainerBookingsSG.add_client),
        state=TrainerBookingsSG.add_time,
        getter=add_time_getter,
    ),
    Window(
        Format(
            "➕ <b>Подтверждение записи</b>\n\n"
            "👤 {client_name}\n"
            "📅 {when}\n\n"
            "<i>Запись сразу будет подтверждена.</i>\n{notify_hint}"
        ),
        Button(
            Const("✅ Записать"),
            id="add_confirm",
            on_click=on_add_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_add_time", state=TrainerBookingsSG.add_time),
        state=TrainerBookingsSG.add_confirm,
        getter=add_confirm_getter,
    ),
    on_start=on_schedule_start,
)
