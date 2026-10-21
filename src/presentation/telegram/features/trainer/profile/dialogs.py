from aiogram import F
from aiogram.enums import ButtonStyle, ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, RequestContact, SwitchTo
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.handlers_phone import validate_phone_number
from src.presentation.telegram.features.trainer.register.validaters import (
    validate_trainer_bio,
    validate_trainer_name,
)
from src.presentation.telegram.widgets.request_chat import RequestChat

from .getters import client_preview_getter, edit_getter, trainer_profile_getter
from .handlers import (
    on_bio_clear,
    on_bio_input,
    on_group_shared,
    on_group_test,
    on_name_input,
    on_phone_contact,
    on_phone_input,
    on_photo_received,
    on_photo_remove,
    on_renew_subscription_click,
    on_social_links_clear,
    on_social_links_success,
)
from .states import TrainerProfileSG
from .validaters import validate_social_links

to_main = SwitchTo(Const("⬅️ Назад"), id="to_main", state=TrainerProfileSG.main)

trainer_profile_dialog = Dialog(
    Window(
        DynamicMedia(selector="photo", when="has_photo"),
        Format(
            "👤 <b>{name}</b>\n"
            "📝 {bio}\n"
            "📞 {phone}\n"
            "🔗 Соцсети: {social_links}\n\n"
            "🔔 Уведомления: {group}\n"
            "💳 Подписка: {subscription}\n"
            "{stats}"
        ),
        Group(
            SwitchTo(Const("✏️ Имя"), id="edit_name", state=TrainerProfileSG.name),
            SwitchTo(Const("📝 О себе"), id="edit_bio", state=TrainerProfileSG.bio),
            SwitchTo(Const("📞 Телефон"), id="edit_phone", state=TrainerProfileSG.phone),
            SwitchTo(Const("🖼 Фото"), id="edit_photo", state=TrainerProfileSG.photo),
            SwitchTo(Const("🔗 Соцсети"), id="edit_links", state=TrainerProfileSG.social_links),
            SwitchTo(Const("🔔 Группа"), id="edit_group", state=TrainerProfileSG.group),
            width=3,
        ),
        SwitchTo(Const("👁 Как меня видят клиенты"), id="preview", state=TrainerProfileSG.preview),
        Button(
            Const("💳 Продлить подписку"),
            id="renew_subscription",
            on_click=on_renew_subscription_click,
        ),
        Cancel(Const("⬅️ Назад")),
        LinkPreview(is_disabled=True),
        state=TrainerProfileSG.main,
        getter=trainer_profile_getter,
    ),
    Window(
        DynamicMedia(selector="photo"),
        Format("👤 <b>{name}</b>\n\n{bio}{links}"),
        Const("\n\n<i>Так выглядит «👤 Ваш инструктор» в меню клиента.</i>"),
        to_main,
        LinkPreview(is_disabled=True),
        state=TrainerProfileSG.preview,
        getter=client_preview_getter,
    ),
    Window(
        Format("✏️ Сейчас: <b>{name}</b>\n\nВведите имя, которое увидят клиенты:"),
        TextInput(
            id="name_input",
            type_factory=validate_trainer_name,
            on_success=on_name_input,
            on_error=on_input_error,
        ),
        to_main,
        state=TrainerProfileSG.name,
        getter=edit_getter,
    ),
    Window(
        Format(
            "📝 Сейчас: {bio}\n\n"
            "Коротко о себе: специализация, опыт, подход (до 255 символов):"
        ),
        TextInput(
            id="bio_input",
            type_factory=validate_trainer_bio,
            on_success=on_bio_input,
            on_error=on_input_error,
        ),
        Button(Const("🧹 Очистить"), id="bio_clear", on_click=on_bio_clear, when="has_bio"),
        to_main,
        state=TrainerProfileSG.bio,
        getter=edit_getter,
    ),
    Window(
        Format("📞 Сейчас: {phone}\n\nОтправьте номер кнопкой или введите вручную:"),
        RequestContact(Const("📞 Отправить мой номер")),
        MessageInput(func=on_phone_contact, content_types=[ContentType.CONTACT]),
        TextInput(
            id="phone_input",
            type_factory=validate_phone_number,
            on_success=on_phone_input,
            on_error=on_input_error,
        ),
        to_main,
        markup_factory=ReplyKeyboardFactory(one_time_keyboard=True, resize_keyboard=True),
        state=TrainerProfileSG.phone,
        getter=edit_getter,
    ),
    Window(
        DynamicMedia(selector="photo", when="has_photo"),
        Const("🖼 Отправьте новое фото — его увидят клиенты.", when=~F["has_photo"]),
        Const("🖼 Текущее фото. Отправьте новое, чтобы заменить.", when="has_photo"),
        MessageInput(func=on_photo_received, content_types=[ContentType.PHOTO]),
        Button(
            Const("🗑 Удалить фото"),
            id="photo_remove",
            on_click=on_photo_remove,
            when="has_photo",
            style=Style(style=ButtonStyle.DANGER),
        ),
        to_main,
        state=TrainerProfileSG.photo,
        getter=edit_getter,
    ),
    Window(
        Format(
            "🔗 Сейчас:\n{social_links}\n\n"
            "Отправьте ссылки одним сообщением, каждая с новой строки:\n"
            "<code>Instagram: https://instagram.com/...</code>\n"
            "<code>Telegram: https://t.me/...</code>\n\n"
            "Список заменится целиком."
        ),
        TextInput(
            id="social_links_input",
            type_factory=validate_social_links,
            on_success=on_social_links_success,
            on_error=on_input_error,
        ),
        Button(Const("🧹 Удалить все"), id="links_clear", on_click=on_social_links_clear, when="has_links"),
        to_main,
        LinkPreview(is_disabled=True),
        state=TrainerProfileSG.social_links,
        getter=edit_getter,
    ),
    Window(
        Const(
            "🔔 <b>Группа для уведомлений</b>\n\n"
            "Туда приходят новые записи, отмены и заявки. Выберите новую группу или "
            "канал кнопкой ниже — Telegram сам добавит туда бота, а мы отправим "
            "проверочное сообщение."
        ),
        RequestChat(Const("👥 Выбрать группу"), request_id=11, chat_is_channel=False),
        RequestChat(Const("📢 Выбрать канал"), request_id=12, chat_is_channel=True),
        MessageInput(func=on_group_shared, content_types=[ContentType.CHAT_SHARED]),
        Button(Const("📨 Проверить текущую"), id="group_test", on_click=on_group_test),
        to_main,
        markup_factory=ReplyKeyboardFactory(one_time_keyboard=True, resize_keyboard=True),
        state=TrainerProfileSG.group,
    ),
)
