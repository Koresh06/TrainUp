from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.kbd import Button, Back

from src.presentation.telegram.features.client.menu.getters import (
    trainer_profile_getter,
)
from src.presentation.telegram.features.client.menu.handlers import (
    on_booking_click,
    on_stub_click,
    on_trainer_profile_click,
)

from .states import ClientMenuSG

client_menu_dialog = Dialog(
    Window(
        Const("Выберите подходящую Вам услугу:"),
        Button(
            Const("📅 Записаться на занятия"),
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
        Button(
            Const("👤 Ваш инструктор"),
            id="trainer_profile",
            on_click=on_trainer_profile_click,
        ),
        state=ClientMenuSG.main,
    ),
    Window(
        Format("👤 <b>{trainer_name}</b>\n\n" "{trainer_bio}" "{social_links_block}"),
        DynamicMedia(selector="photo"),
        Back(Const("⬅️ Назад")),
        state=ClientMenuSG.trainer_profile,
        getter=trainer_profile_getter,
    ),
)
