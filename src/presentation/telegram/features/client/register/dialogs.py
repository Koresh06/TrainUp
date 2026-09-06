from aiogram.enums import ButtonStyle, ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Group,
    Next,
    RequestContact,
    Back,
    Select,
)
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.style import Style

from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.handlers_phone import on_phone_input_success, on_phone_received_contact, validate_phone_number
from .states import ClientRegisterSG
from .validator import (
    validate_full_name,
    validate_age,
)
from .handlers import (
    on_full_name_success,
    on_multi_select_next,
    on_option_toggle,
    on_age_input_success,
    on_question_back,
    on_register_confirm,
    on_sport_experience_selected,
    on_text_answer,
)
from .getters import (
    is_multi_select,
    questions_getter,
    sport_experience_getter,
    welcome_getter,
    register_confirm_getter,
)

client_register_dialog = Dialog(
    Window(
        Format(
            "Привет! 👋\n\n"
            "Ты переходишь в бота тренера <b>{trainer_name}</b>.\n"
            "{trainer_bio}\n\n"
            "Для записи на тренировки нужно немного познакомиться — "
            "заполним короткую анкету."
        ),
        Next(Const("Начать →")),
        state=ClientRegisterSG.welcome,
        getter=welcome_getter,
    ),
    Window(
        Const("👤 <b>Укажите Ваше имя и фамилию:</b>\nНапример: <i>Иван Иванов</i>"),
        TextInput(
            id="full_name",
            type_factory=validate_full_name,
            on_success=on_full_name_success,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.full_name,
    ),
    Window(
        Const("Укажите Ваш возраст"),
        TextInput(
            id="age",
            type_factory=validate_age,
            on_success=on_age_input_success,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.age,
    ),
    Window(
        Const(
            "📞 <b>Укажите Ваш номер телефона (например, "
            "+375291234567 или 80291234567):</b>"
        ),
        RequestContact(Const("📞 Отправить номер")),
        MessageInput(
            func=on_phone_received_contact,
            content_types=[ContentType.CONTACT],
        ),
        TextInput(
            id="phone",
            type_factory=validate_phone_number,
            on_success=on_phone_input_success,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        markup_factory=ReplyKeyboardFactory(
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
        state=ClientRegisterSG.phone,
    ),
    Window(
        Const("🏋️ <b>Ваш стаж занятий спортом или физической культурой:</b>"),
        Group(
            Select(
                Format("{item[label]}"),
                id="sport_experience_select",
                item_id_getter=lambda item: item["id"],
                items="sport_experience_options",
                on_click=on_sport_experience_selected,
            ),
            width=1,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.sport_experience,
        getter=sport_experience_getter,
    ),
    Window(
        Format("<b>{question_label}</b>"),
        Group(
            Select(
                Format("{item[label]}"),
                id="question_options_select",
                item_id_getter=lambda item: item["id"],
                items="options",
                on_click=on_option_toggle,
            ),
            width=1,
            when=is_multi_select,
        ),
        MessageInput(
            func=on_text_answer,
            content_types=[ContentType.TEXT],
        ),
        Button(
            Const("Далее ➡️"),
            id="question_next",
            on_click=on_multi_select_next,
            style=Style(style=ButtonStyle.SUCCESS),
            when=is_multi_select,
        ),
        Button(
            Const("⬅️ Назад"),
            id="question_back",
            on_click=on_question_back,
        ),
        state=ClientRegisterSG.questions,
        getter=questions_getter,
    ),
    Window(
        Format(
            "Проверь данные:\n\n"
            "👤 {full_name}\n"
            "📞 {phone}\n"
            "🎂 {age} лет\n"
            "🏋️ Стаж: {sport_experience}\n\n"
            "{answers_summary}"
        ),
        Button(
            Const("✅ Всё верно"),
            id="confirm_register",
            on_click=on_register_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.confirm,
        getter=register_confirm_getter,
    ),
)
