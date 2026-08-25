from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.kbd import Button, Column, Cancel, Back, Next
from aiogram_dialog.widgets.input import TextInput, MessageInput

from src.presentation.telegram.features.error_handler import on_input_error

from .states import TrainerProfileSG
from .getters import trainer_profile_getter
from .handlers import (
    on_photo_received,
    on_profile_edit_click,
    on_social_links_success,
)
from .validaters import validate_social_links

trainer_profile_dialog = Dialog(
    Window(
        Format(
            "👤 <b>Профиль</b>\n\n"
            "👥 Клиентов: {clients_count}\n"
            "💳 Подписка до: {subscription_end_date}\n"
            "🔗 Соцсети:\n{social_links_summary}"
        ),
        DynamicMedia(selector="photo"),
        Next(Const("✏️ Редактировать")),
        Cancel(Const("⬅️ Назад")),
        state=TrainerProfileSG.main,
        getter=trainer_profile_getter,
        disable_web_page_preview=True,
    ),
    Window(
        Const("Что меняем?"),
        Column(
            Button(
                Const("🖼 Изменить фото"),
                id="edit_photo",
                on_click=on_profile_edit_click,
            ),
            Button(
                Const("🔗 Изменить ссылки на соцсети"),
                id="edit_social_links",
                on_click=on_profile_edit_click,
            ),
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerProfileSG.edit_menu,
    ),
    Window(
        Const("🖼 Отправьте новое фото:"),
        MessageInput(
            func=on_photo_received,
            content_types=[ContentType.PHOTO],
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerProfileSG.photo,
    ),
    Window(
        Format(
            "🔗 Текущие ссылки:\n{social_links_summary}\n\n"
            "Отправьте ссылки одной группой, каждая с новой строки, в формате:\n"
            "<code>Instagram: https://instagram.com/...</code>\n"
            "<code>Telegram: https://t.me/...</code>\n\n"
            "Это полностью заменит текущий список."
        ),
        TextInput(
            id="social_links_input",
            type_factory=validate_social_links,
            on_success=on_social_links_success,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerProfileSG.social_links,
        getter=trainer_profile_getter,
        disable_web_page_preview=True,
    ),
)