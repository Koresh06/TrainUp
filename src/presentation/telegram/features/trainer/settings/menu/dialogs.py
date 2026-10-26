from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Group
from aiogram_dialog.widgets.text import Const

from .states import TrainerSettingsSG
from .handlers import on_settings_item_click

trainer_settings_dialog = Dialog(
    Window(
        Const("⚙️ <b>Настройки</b>\n\nЧто настраиваем?"),
        # Расписание и блокировки — 2 колонки
        Group(
            Button(Const("🗓 Расписание"), id="schedule", on_click=on_settings_item_click),
            Button(Const("🚫 Блокировки"), id="blocking", on_click=on_settings_item_click),
            width=2,
        ),
        # Запись и цены — 2 колонки
        Group(
            Button(Const("📅 Запись"), id="booking_settings", on_click=on_settings_item_click),
            Button(Const("💰 Цены"), id="pricing", on_click=on_settings_item_click),
            width=2,
        ),
        # Анкета и напоминания — 2 колонки
        Group(
            Button(Const("📋 Вопросы анкеты"), id="questions", on_click=on_settings_item_click),
            Button(Const("🔔 Напоминания"), id="reminder_settings", on_click=on_settings_item_click),
            width=2,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerSettingsSG.main,
    )
)
