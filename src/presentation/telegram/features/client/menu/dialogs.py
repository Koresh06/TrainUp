from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button

from src.presentation.telegram.features.client.menu.handlers import (
    on_booking_click,
    on_stub_click,
)

from .states import ClientMenuSG

client_menu_dialog = Dialog(
    Window(
        Const(
            "Привет! Я помогу записаться на тренировку, подобрать программу "
            "или связаться с тренером.\n\nВыбери, что нужно:"
        ),
        Button(
            Const("📅 Записаться на занятие"),
            id="booking",
            on_click=on_booking_click,
        ),
        Button(
            Const("🏋 Программа тренировок"),
            id="program",
            on_click=on_stub_click,
        ),
        Button(
            Const("💬 Консультация с тренером"),
            id="consultation",
            on_click=on_stub_click,
        ),
        Button(
            Const("✉️ Обратная связь"),
            id="feedback",
            on_click=on_stub_click,
        ),
        state=ClientMenuSG.main,
    ),
)
