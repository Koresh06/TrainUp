from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo
from aiogram_dialog.widgets.link_preview import LinkPreview

from src.presentation.telegram.features.client.menu.getters import (
    my_bookings_getter,
    trainer_profile_getter,
)
from src.presentation.telegram.features.client.menu.handlers import (
    on_menu_item_click,
    on_my_bookings_click,
    on_my_progress_click,
    on_trainer_profile_click,
)

from .states import ClientMenuSG

client_menu_dialog = Dialog(
    Window(
        Const("Выберите подходящую Вам услугу:"),
        Button(
            Const("📅 Записаться на занятия"),
            id="booking",
            on_click=on_menu_item_click,
        ),
        Button(
            Const("📋 Мои записи"),
            id="my_bookings",
            on_click=on_my_bookings_click,
        ),
        Button(
            Const("🏋 Программа тренировок"),
            id="program",
            on_click=on_menu_item_click,
        ),
        Button(
            Const("💬 Консультация с тренером"),
            id="consultation",
            on_click=on_menu_item_click,
        ),
        Button(
            Const("✉️ Обратная связь"),
            id="feedback",
            on_click=on_menu_item_click,
        ),
        Button(
            Const("📈 Мой прогресс"),
            id="progress",
            on_click=on_my_progress_click,
        ),
        Button(
            Const("📝 Моя анкета"),
            id="profile",
            on_click=on_menu_item_click,
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
    Window(
        Format("📋 <b>Мои записи</b>\n\n{bookings_block}\n\n{contact_hint}"),
        SwitchTo(Const("⬅️ Назад"), id="back_to_menu", state=ClientMenuSG.main),
        LinkPreview(is_disabled=True),
        state=ClientMenuSG.my_bookings,
        getter=my_bookings_getter,
    ),
)
