from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Row, Select, SwitchTo
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.slot_style import slot_style
from src.presentation.telegram.widgets.booking_calendar import BookingCalendar

from .getters import blocking_calendar_getter, blocking_day_getter
from .handlers import (
    on_block_day_click,
    on_blocking_date_clicked,
    on_blocking_slot_clicked,
    on_open_vacation,
)
from .states import TrainerBlockingSG

trainer_blocking_dialog = Dialog(
    Window(
        Const(
            "🚫 <b>Блокировка дней и слотов</b>\n\n"
            "Выберите день. 🟢 — есть открытые слоты, 🔴 — всё закрыто.\n"
            "Заблокированные слоты клиенты не видят и не могут на них записаться."
        ),
        BookingCalendar(id="blocking_calendar", on_click=on_blocking_date_clicked),
        Button(Const("🏖 Отпуск / больничный"), id="vacation", on_click=on_open_vacation),
        Cancel(Const("⬅️ Назад")),
        state=TrainerBlockingSG.select_date,
        getter=blocking_calendar_getter,
    ),
    Window(
        Format(
            "🗓 <b>{day_label}</b>\n\n"
            "Нажмите на время, чтобы закрыть/открыть его для записи.\n"
            "🟢 открыт · 🚫 заблокирован · (записано/мест)"
        ),
        Group(
            Select(
                Format("{item[label]}"),
                id="blocking_slot_select",
                item_id_getter=lambda item: item["value_id"],
                items="times",
                on_click=on_blocking_slot_clicked,
                style=slot_style,
            ),
            width=2,
        ),
        Row(
            Button(
                Const("🚫 Закрыть весь день"),
                id="block_day",
                on_click=on_block_day_click,
                style=Style(style=ButtonStyle.DANGER),
            ),
            Button(
                Const("✅ Открыть весь день"),
                id="unblock_day",
                on_click=on_block_day_click,
                style=Style(style=ButtonStyle.SUCCESS),
            ),
            when="has_slots",
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_calendar", state=TrainerBlockingSG.select_date),
        state=TrainerBlockingSG.day,
        getter=blocking_day_getter,
    ),
)
