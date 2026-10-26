from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.kbd import Button, Back, Group, SwitchTo, Url
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.style import Style

from src.presentation.telegram.features.client.menu.getters import (
    my_bookings_getter,
    referral_getter,
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
        Const("👋 <b>Главное меню</b>\n\nЧто делаем сегодня?"),
        # Главное действие
        Button(
            Const("📅 Записаться на тренировку"),
            id="booking",
            on_click=on_menu_item_click,
            style=Style(style=ButtonStyle.PRIMARY),
        ),
        # Мои активности — 2 колонки
        Group(
            Button(Const("📋 Мои записи"), id="my_bookings", on_click=on_my_bookings_click),
            Button(Const("📈 Мой прогресс"), id="progress", on_click=on_my_progress_click),
            width=2,
        ),
        # Услуги — 2 колонки
        Group(
            Button(Const("🏋 Программа"), id="program", on_click=on_menu_item_click),
            Button(Const("💬 Консультация"), id="consultation", on_click=on_menu_item_click),
            width=2,
        ),
        # Профиль и обратная связь — 2 колонки
        Group(
            Button(Const("📝 Моя анкета"), id="profile", on_click=on_menu_item_click),
            Button(Const("✉️ Обратная связь"), id="feedback", on_click=on_menu_item_click),
            width=2,
        ),
        # Инструктор и реферал — 2 колонки
        Group(
            Button(Const("👤 Ваш инструктор"), id="trainer_profile", on_click=on_trainer_profile_click),
            SwitchTo(Const("🎁 Пригласить друга"), id="referral", state=ClientMenuSG.referral),
            width=2,
        ),
        state=ClientMenuSG.main,
    ),
    Window(
        Format(
            "👤 <b>{trainer_name}</b>\n\n"
            "<blockquote>{trainer_bio}</blockquote>"
            "{social_links_block}"
        ),
        DynamicMedia(selector="photo"),
        Back(Const("⬅️ Назад")),
        state=ClientMenuSG.trainer_profile,
        getter=trainer_profile_getter,
    ),
    Window(
        Format("📋 <b>Мои записи</b>\n\n{bookings_block}\n\n{contact_hint}"),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_menu",
            state=ClientMenuSG.main,
        ),
        LinkPreview(is_disabled=True),
        state=ClientMenuSG.my_bookings,
        getter=my_bookings_getter,
    ),
    Window(
        Format(
            "🎁 <b>Пригласите друга</b>\n\n"
            "<b>Как это работает</b>\n{steps}{rules}\n\n"
            "Ваша ссылка:\n<code>{link}</code>\n\n"
            "{invited}"
        ),
        Url(Const("📤 Поделиться"), Format("{share_url}")),
        SwitchTo(
            Const("⬅️ Назад"),
            id="referral_back",
            state=ClientMenuSG.main,
        ),
        LinkPreview(is_disabled=True),
        state=ClientMenuSG.referral,
        getter=referral_getter,
    ),
)
