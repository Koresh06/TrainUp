from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Cancel
from aiogram_dialog.widgets.text import Const

from .states import TrainerSettingsSG
from .handlers import on_settings_item_click

trainer_settings_dialog = Dialog(
    Window(
        Const("⚙️ Настройки. Что настраиваем?"),
        Column(
            Button(
                Const("🗓 Расписание"),
                id="schedule",
                on_click=on_settings_item_click,
            ),
            Button(
                Const("🚫 Блокировка дней/слотов"),
                id="blocking",
                on_click=on_settings_item_click,
            ),
            Button(
                Const("💰 Цены"),
                id="pricing",
                on_click=on_settings_item_click,
            ),
            Button(
                Const("📅 Запись"),
                id="booking_settings",
                on_click=on_settings_item_click,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerSettingsSG.main,
    )
)
